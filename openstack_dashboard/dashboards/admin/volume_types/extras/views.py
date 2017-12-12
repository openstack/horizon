# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.volume_types.extras \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.volume_types.extras \
    import tables as project_tables


class ExtraSpecMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ExtraSpecMixin, self).get_context_data(**kwargs)
        try:
            context['vol_type'] = api.cinder.volume_type_get(
                self.request, self.kwargs['type_id'])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volume type details."))
        if 'key' in self.kwargs:
            context['key'] = self.kwargs['key']
        return context


class IndexView(ExtraSpecMixin, forms.ModalFormMixin, tables.DataTableView):
    table_class = project_tables.ExtraSpecsTable
    template_name = 'admin/volume_types/extras/index.html'

    def get_data(self):
        try:
            type_id = self.kwargs['type_id']
            extras_list = api.cinder.volume_type_extra_get(self.request,
                                                           type_id)
            extras_list.sort(key=lambda es: (es.key,))
        except Exception:
            extras_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve extra spec list.'))
        return extras_list


class CreateView(ExtraSpecMixin, forms.ModalFormView):
    form_class = project_forms.CreateExtraSpec
    form_id = "extra_spec_create_form"
    page_title = _("Create Volume Type Extra Spec")
    modal_id = "extra_spec_create_modal"
    submit_label = _("Create")
    submit_url = "horizon:admin:volume_types:extras:create"
    template_name = 'admin/volume_types/extras/create.html'
    success_url = 'horizon:admin:volume_types:extras:index'
    cancel_url = reverse_lazy('horizon:admin:volume_types:index')

    def get_initial(self):
        return {'type_id': self.kwargs['type_id']}

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['type_id'],))

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        args = (self.kwargs['type_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context


class EditView(ExtraSpecMixin, forms.ModalFormView):
    form_class = project_forms.EditExtraSpec
    form_id = "extra_spec_edit_form"
    page_title = _('Edit Extra Spec Value: %s')
    modal_id = "extra_spec_edit_modal"
    submit_label = _("Save")
    submit_url = "horizon:admin:volume_types:extras:edit"
    template_name = 'admin/volume_types/extras/edit.html'
    success_url = 'horizon:admin:volume_types:extras:index'
    cancel_url = reverse_lazy('horizon:admin:volume_types:index')

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['type_id'],))

    def get_initial(self):
        type_id = self.kwargs['type_id']
        key = self.kwargs['key']
        try:
            extra_specs = api.cinder.volume_type_extra_get(self.request,
                                                           type_id,
                                                           raw=True)
        except Exception:
            extra_specs = {}
            exceptions.handle(self.request,
                              _('Unable to retrieve volume type extra spec '
                                'details.'))
        return {'type_id': type_id,
                'key': key,
                'value': extra_specs.get(key, '')}

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        args = (self.kwargs['type_id'], self.kwargs['key'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        context['page_title'] = self.page_title % self.kwargs['key']
        return context

    def form_invalid(self, form):
        context = super(EditView, self).get_context_data()
        context = self._populate_context(context)
        context['form'] = form
        context['page_title'] = self.page_title % self.kwargs['key']
        return self.render_to_response(context)
