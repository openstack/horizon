# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import logging
from operator import attrgetter

import yaml

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse  # noqa
from django.utils.translation import ugettext_lazy as _
import django.views.generic

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import views
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.stacks \
    import api as project_api
from openstack_dashboard.dashboards.project.stacks \
    import forms as project_forms
from openstack_dashboard.dashboards.project.stacks \
    import tables as project_tables
from openstack_dashboard.dashboards.project.stacks \
    import tabs as project_tabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.StacksTable
    template_name = 'project/stacks/index.html'
    page_title = _("Stacks")

    def __init__(self, *args, **kwargs):
        super(IndexView, self).__init__(*args, **kwargs)
        self._more = None

    def has_prev_data(self, table):
        return self._prev

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        stacks = []
        prev_marker = self.request.GET.get(
            project_tables.StacksTable._meta.prev_pagination_param)
        if prev_marker is not None:
            sort_dir = 'asc'
            marker = prev_marker
        else:
            sort_dir = 'desc'
            marker = self.request.GET.get(
                project_tables.StacksTable._meta.pagination_param)
        try:
            stacks, self._more, self._prev = api.heat.stacks_list(
                self.request,
                marker=marker,
                paginate=True,
                sort_dir=sort_dir)
            if prev_marker is not None:
                stacks = sorted(stacks, key=attrgetter('creation_time'),
                                reverse=True)
        except Exception:
            self._prev = False
            self._more = False
            msg = _('Unable to retrieve stack list.')
            exceptions.handle(self.request, msg)
        return stacks


class SelectTemplateView(forms.ModalFormView):
    template_name = 'project/stacks/select_template.html'
    modal_header = _("Select Template")
    form_id = "select_template"
    form_class = project_forms.TemplateForm
    submit_label = _("Next")
    submit_url = reverse_lazy("horizon:project:stacks:select_template")
    success_url = reverse_lazy('horizon:project:stacks:launch')
    page_title = _("Select Template")

    def get_initial(self):
        initial = {}
        for name in [
            'template_url',
            'template_source',
            'template_data',
            'environment_source',
            'environment_data'
        ]:
            tmp = self.request.GET.get(name)
            if tmp:
                initial[name] = tmp
        return initial

    def get_form_kwargs(self):
        kwargs = super(SelectTemplateView, self).get_form_kwargs()
        kwargs['next_view'] = CreateStackView
        return kwargs


class ChangeTemplateView(forms.ModalFormView):
    template_name = 'project/stacks/change_template.html'
    modal_header = _("Select Template")
    form_id = "change_template"
    form_class = project_forms.ChangeTemplateForm
    submit_label = _("Next")
    submit_url = "horizon:project:stacks:change_template"
    cancel_url = reverse_lazy('horizon:project:stacks:index')
    success_url = reverse_lazy('horizon:project:stacks:edit_stack')
    page_title = _("Change Template")

    def get_context_data(self, **kwargs):
        context = super(ChangeTemplateView, self).get_context_data(**kwargs)
        args = (self.get_object().id,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_object(self):
        stack_id = self.kwargs['stack_id']
        try:
            self._stack = api.heat.stack_get(self.request, stack_id)
        except Exception:
            msg = _("Unable to retrieve stack.")
            redirect = reverse('horizon:project:stacks:index')
            exceptions.handle(self.request, msg, redirect=redirect)
        return self._stack

    def get_initial(self):
        stack = self.get_object()
        return {'stack_id': stack.id,
                'stack_name': stack.stack_name
                }

    def get_form_kwargs(self):
        kwargs = super(ChangeTemplateView, self).get_form_kwargs()
        kwargs['next_view'] = EditStackView
        return kwargs


class PreviewTemplateView(forms.ModalFormView):
    template_name = 'project/stacks/preview_template.html'
    modal_header = _("Preview Template")
    form_id = "preview_template"
    form_class = project_forms.PreviewTemplateForm
    submit_label = _("Next")
    submit_url = reverse_lazy('horizon:project:stacks:preview_template')
    success_url = reverse_lazy('horizon:project:stacks:preview')
    page_title = _("Preview Template")

    def get_form_kwargs(self):
        kwargs = super(PreviewTemplateView, self).get_form_kwargs()
        kwargs['next_view'] = PreviewStackView
        return kwargs


class CreateStackView(forms.ModalFormView):
    template_name = 'project/stacks/create.html'
    modal_header = _("Launch Stack")
    form_id = "launch_stack"
    form_class = project_forms.CreateStackForm
    submit_label = _("Launch")
    submit_url = reverse_lazy("horizon:project:stacks:launch")
    success_url = reverse_lazy('horizon:project:stacks:index')
    page_title = _("Launch Stack")

    def get_initial(self):
        initial = {}
        self.load_kwargs(initial)
        if 'parameters' in self.kwargs:
            initial['parameters'] = json.dumps(self.kwargs['parameters'])
        return initial

    def load_kwargs(self, initial):
        # load the "passed through" data from template form
        for prefix in ('template', 'environment'):
            for suffix in ('_data', '_url'):
                key = prefix + suffix
                if key in self.kwargs:
                    initial[key] = self.kwargs[key]

    def get_form_kwargs(self):
        kwargs = super(CreateStackView, self).get_form_kwargs()
        if 'parameters' in self.kwargs:
            kwargs['parameters'] = self.kwargs['parameters']
        else:
            data = json.loads(self.request.POST['parameters'])
            kwargs['parameters'] = data
        return kwargs


# edit stack parameters, coming from template selector
class EditStackView(CreateStackView):
    template_name = 'project/stacks/update.html'
    modal_header = _("Update Stack Parameters")
    form_id = "update_stack"
    form_class = project_forms.EditStackForm
    submit_label = _("Update")
    submit_url = "horizon:project:stacks:edit_stack"
    success_url = reverse_lazy('horizon:project:stacks:index')
    page_title = _("Update Stack")

    def get_initial(self):
        initial = super(EditStackView, self).get_initial()

        initial['stack'] = self.get_object()['stack']
        if initial['stack']:
            initial['stack_id'] = initial['stack'].id
            initial['stack_name'] = initial['stack'].stack_name

        return initial

    def get_context_data(self, **kwargs):
        context = super(EditStackView, self).get_context_data(**kwargs)
        args = (self.get_object()['stack'].id,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_object(self):
        stack_id = self.kwargs['stack_id']
        try:
            stack = {}
            stack['stack'] = api.heat.stack_get(self.request, stack_id)
            stack['template'] = api.heat.template_get(self.request, stack_id)
            self._stack = stack
        except Exception:
            msg = _("Unable to retrieve stack.")
            redirect = reverse('horizon:project:stacks:index')
            exceptions.handle(self.request, msg, redirect=redirect)
        return self._stack


class PreviewStackView(CreateStackView):
    template_name = 'project/stacks/preview.html'
    modal_header = _("Preview Stack")
    form_id = "preview_stack"
    form_class = project_forms.PreviewStackForm
    submit_label = _("Preview")
    submit_url = reverse_lazy('horizon:project:stacks:preview')
    success_url = reverse_lazy('horizon:project:stacks:index')
    page_title = _("Preview Stack")

    def get_form_kwargs(self):
        kwargs = super(CreateStackView, self).get_form_kwargs()
        kwargs['next_view'] = PreviewStackDetailsView
        return kwargs


class PreviewStackDetailsView(forms.ModalFormMixin, views.HorizonTemplateView):
    template_name = 'project/stacks/preview_details.html'
    page_title = _("Preview Stack Details")

    def get_context_data(self, **kwargs):
        context = super(
            PreviewStackDetailsView, self).get_context_data(**kwargs)
        context['stack_preview'] = self.kwargs['stack_preview'].to_dict()
        return context


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.StackDetailTabs
    template_name = 'project/stacks/detail.html'
    page_title = _("Stack Details: {{ stack.stack_name }}")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        stack = self.get_data(self.request, **kwargs)
        table = project_tables.StacksTable(self.request)
        context["stack"] = stack
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(stack)
        return context

    @memoized.memoized_method
    def get_data(self, request, **kwargs):
        stack_id = kwargs['stack_id']
        try:
            stack = api.heat.stack_get(request, stack_id)
            request.session['stack_id'] = stack.id
            request.session['stack_name'] = stack.stack_name
            return stack
        except Exception:
            msg = _("Unable to retrieve stack.")
            exceptions.handle(request, msg, redirect=self.get_redirect_url())

    @memoized.memoized_method
    def get_template(self, request, **kwargs):
        try:
            stack_template = api.heat.template_get(
                request,
                kwargs['stack_id'])
            return yaml.safe_dump(stack_template, indent=2)
        except Exception:
            msg = _("Unable to retrieve stack template.")
            exceptions.handle(request, msg, redirect=self.get_redirect_url())

    def get_tabs(self, request, **kwargs):
        stack = self.get_data(request, **kwargs)
        stack_template = self.get_template(request, **kwargs)
        return self.tab_group_class(
            request, stack=stack, stack_template=stack_template, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:stacks:index')


class ResourceView(tabs.TabView):
    tab_group_class = project_tabs.ResourceDetailTabs
    template_name = 'project/stacks/resource.html'
    page_title = _("Resource Details: {{ resource.resource_name }}")

    def get_context_data(self, **kwargs):
        context = super(ResourceView, self).get_context_data(**kwargs)
        context["resource"] = self.get_data(self.request, **kwargs)
        context["metadata"] = self.get_metadata(self.request, **kwargs)
        return context

    @memoized.memoized_method
    def get_data(self, request, **kwargs):
        try:
            resource = api.heat.resource_get(
                request,
                kwargs['stack_id'],
                kwargs['resource_name'])
            return resource
        except Exception:
            msg = _("Unable to retrieve resource.")
            redirect = reverse('horizon:project:stacks:index')
            exceptions.handle(request, msg, redirect=redirect)

    @memoized.memoized_method
    def get_metadata(self, request, **kwargs):
        try:
            metadata = api.heat.resource_metadata_get(
                request,
                kwargs['stack_id'],
                kwargs['resource_name'])
            return json.dumps(metadata, indent=2)
        except Exception:
            msg = _("Unable to retrieve metadata.")
            redirect = reverse('horizon:project:stacks:index')
            exceptions.handle(request, msg, redirect=redirect)

    def get_tabs(self, request, **kwargs):
        resource = self.get_data(request, **kwargs)
        metadata = self.get_metadata(request, **kwargs)
        return self.tab_group_class(
            request, resource=resource, metadata=metadata, **kwargs)


class JSONView(django.views.generic.View):
    def get(self, request, stack_id=''):
        return HttpResponse(project_api.d3_data(request, stack_id=stack_id),
                            content_type="application/json")
