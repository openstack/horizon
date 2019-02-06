# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
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
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.group_types \
    import forms as group_types_forms
from openstack_dashboard.dashboards.admin.group_types \
    import tables as group_types_tables

INDEX_URL = 'horizon:admin:group_types:index'


class GroupTypesView(tables.DataTableView):
    table_class = group_types_tables.GroupTypesTable
    page_title = _("Group Types")

    def get_data(self):
        try:
            group_types = api.cinder.group_type_list(self.request)
        except Exception:
            group_types = []
            exceptions.handle(self.request,
                              _("Unable to retrieve group types."))

        return group_types


class CreateGroupTypeView(forms.ModalFormView):
    form_class = group_types_forms.CreateGroupType
    modal_id = "create_group_type_modal"
    template_name = 'admin/group_types/create_group_type.html'
    submit_label = _("Create Group Type")
    submit_url = reverse_lazy("horizon:admin:group_types:create_type")
    success_url = reverse_lazy('horizon:admin:group_types:index')
    page_title = _("Create a Group Type")


class EditGroupTypeView(forms.ModalFormView):
    form_class = group_types_forms.EditGroupType
    template_name = 'admin/group_types/update_group_type.html'
    success_url = reverse_lazy('horizon:admin:group_types:index')
    cancel_url = reverse_lazy('horizon:admin:group_types:index')
    submit_label = _('Edit')

    @memoized.memoized_method
    def get_data(self):
        try:
            group_type_id = self.kwargs['type_id']
            group_type = api.cinder.group_type_get(self.request,
                                                   group_type_id)
        except Exception:
            error_message = _(
                'Unable to retrieve group type for: "%s"') \
                % group_type_id
            exceptions.handle(self.request,
                              error_message,
                              redirect=self.success_url)

        return group_type

    def get_context_data(self, **kwargs):
        context = super(EditGroupTypeView, self).get_context_data(**kwargs)
        context['group_type'] = self.get_data()

        return context

    def get_initial(self):
        group_type = self.get_data()
        return {'id': self.kwargs['type_id'],
                'name': group_type.name,
                'is_public': getattr(group_type, 'is_public', True),
                'description': getattr(group_type, 'description', "")}


def _get_group_type_name(request, kwargs):
    try:
        group_type_list = api.cinder.group_type_list(request)
        for group_type in group_type_list:
            if group_type.id == kwargs['group_type_id']:
                return group_type.name
    except Exception:
        msg = _('Unable to retrieve group type name.')
        url = reverse('INDEX_URL')
        exceptions.handle(request, msg, redirect=url)
