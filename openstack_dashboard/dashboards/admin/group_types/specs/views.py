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
from openstack_dashboard.dashboards.admin.group_types.specs \
    import forms as admin_forms
from openstack_dashboard.dashboards.admin.group_types.specs \
    import tables as admin_tables


class GroupTypeSpecMixin(object):
    def get_context_data(self, **kwargs):
        context = super(GroupTypeSpecMixin, self).get_context_data(**kwargs)
        try:
            context['group_type'] = api.cinder.group_type_get(
                self.request, self.kwargs['type_id'])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve group type details."))
        if 'key' in self.kwargs:
            context['key'] = self.kwargs['key']
        return context


class IndexView(GroupTypeSpecMixin, forms.ModalFormMixin, tables.DataTableView):
    table_class = admin_tables.GroupTypeSpecsTable
    template_name = 'admin/group_types/specs/index.html'

    def get_data(self):
        try:
            group_type_id = self.kwargs['type_id']
            specs_list = api.cinder.group_type_spec_list(self.request,
                                                         group_type_id)
            specs_list.sort(key=lambda es: (es.key,))
        except Exception:
            specs_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve group type spec list.'))
        return specs_list


class CreateView(GroupTypeSpecMixin, forms.ModalFormView):
    form_class = admin_forms.CreateSpec
    form_id = "group_type_spec_create_form"
    modal_header = _("Create Group Type Spec")
    modal_id = "group_type_spec_create_modal"
    submit_label = _("Create")
    submit_url = "horizon:admin:group_types:specs:create"
    template_name = 'admin/group_types/specs/create.html'
    success_url = 'horizon:admin:group_types:index'
    cancel_url = reverse_lazy('horizon:admin:group_types:index')

    def get_initial(self):
        return {'group_type_id': self.kwargs['type_id']}

    def get_success_url(self):
        return reverse(self.success_url)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        args = (self.kwargs['type_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context


class EditView(GroupTypeSpecMixin, forms.ModalFormView):
    form_class = admin_forms.EditSpec
    form_id = "group_type_spec_edit_form"
    modal_header = _('Edit Group Type Spec Value: %s')
    modal_id = "group_type_spec_edit_modal"
    submit_label = _("Save")
    submit_url = "horizon:admin:group_types:specs:edit"
    template_name = 'admin/group_types/specs/edit.html'
    success_url = 'horizon:admin:group_types:index'
    cancel_url = reverse_lazy('horizon:admin:group_types:index')

    def get_success_url(self):
        return reverse(self.success_url)

    def get_initial(self):
        group_type_id = self.kwargs['type_id']
        key = self.kwargs['key']
        try:
            group_specs = api.cinder.group_type_spec_list(self.request,
                                                          group_type_id,
                                                          raw=True)
        except Exception:
            group_specs = {}
            exceptions.handle(self.request,
                              _('Unable to retrieve group type spec '
                                'details.'))
        return {'group_type_id': group_type_id,
                'key': key,
                'value': group_specs.get(key, '')}

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        args = (self.kwargs['type_id'], self.kwargs['key'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        context['modal_header'] = self.modal_header % self.kwargs['key']
        return context

    def form_invalid(self, form):
        context = super(EditView, self).get_context_data()
        context = self._populate_context(context)
        context['form'] = form
        context['modal_header'] = self.modal_header % self.kwargs['key']
        return self.render_to_response(context)
