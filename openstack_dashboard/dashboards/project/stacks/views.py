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
    form_class = project_forms.TemplateForm
    template_name = 'project/stacks/select_template.html'
    success_url = reverse_lazy('horizon:project:stacks:launch')

    def get_form_kwargs(self):
        kwargs = super(SelectTemplateView, self).get_form_kwargs()
        kwargs['next_view'] = CreateStackView
        return kwargs


class ChangeTemplateView(forms.ModalFormView):
    form_class = project_forms.ChangeTemplateForm
    template_name = 'project/stacks/change_template.html'
    success_url = reverse_lazy('horizon:project:stacks:edit_stack')

    def get_context_data(self, **kwargs):
        context = super(ChangeTemplateView, self).get_context_data(**kwargs)
        context['stack'] = self.get_object()
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


class CreateStackView(forms.ModalFormView):
    form_class = project_forms.CreateStackForm
    template_name = 'project/stacks/create.html'
    success_url = reverse_lazy('horizon:project:stacks:index')

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
    form_class = project_forms.EditStackForm
    template_name = 'project/stacks/update.html'
    success_url = reverse_lazy('horizon:project:stacks:index')

    def get_initial(self):
        initial = super(EditStackView, self).get_initial()

        initial['stack'] = self.get_object()['stack']
        if initial['stack']:
            initial['stack_id'] = initial['stack'].id
            initial['stack_name'] = initial['stack'].stack_name

        return initial

    def get_context_data(self, **kwargs):
        context = super(EditStackView, self).get_context_data(**kwargs)
        context['stack'] = self.get_object()['stack']
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


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.StackDetailTabs
    template_name = 'project/stacks/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["stack"] = self.get_data(self.request, **kwargs)
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
            redirect = reverse('horizon:project:stacks:index')
            exceptions.handle(request, msg, redirect=redirect)

    def get_tabs(self, request, **kwargs):
        stack = self.get_data(request, **kwargs)
        return self.tab_group_class(request, stack=stack, **kwargs)


class ResourceView(tabs.TabView):
    tab_group_class = project_tabs.ResourceDetailTabs
    template_name = 'project/stacks/resource.html'

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
