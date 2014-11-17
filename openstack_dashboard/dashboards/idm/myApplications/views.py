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

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm.myApplications \
            import tables as application_tables
from openstack_dashboard.dashboards.idm.myApplications \
            import tabs as application_tabs
from openstack_dashboard.dashboards.idm.myApplications \
            import forms as application_forms


class IndexView(tabs.TabbedTableView):
    tab_group_class = application_tabs.PanelTabs
    template_name = 'idm/myApplications/index.html'

  
class CreateView(forms.ModalFormView):
    form_class = application_forms.CreateApplicationForm
    template_name = 'idm/myApplications/create.html'
    

class UploadImageView(forms.ModalFormView):
    form_class = application_forms.UploadImageForm
    template_name = 'idm/myApplications/upload.html'
    
# NOTE(garcianavalon) from horizon.forms.views
ADD_TO_FIELD_HEADER = "HTTP_X_HORIZON_ADD_TO_FIELD"
class RolesView(tables.MultiTableView):
    """ Logic for the asynchronous widget to manage roles and permissions at the
    application level.
    """
    template_name = 'idm/myApplications/roles.html'
    table_classes = (application_tables.RolesTable,
                     application_tables.PermissionsTable)

    # def get_context_data(self, **kwargs):
    #     context = super(RolesView, self).get_context_data(**kwargs)
    #     try:
    #         context['roles'] = fiware_api.keystone.role_list(self.request)
    #         context['selected_role'] = context['roles'][0] 
    #     except Exception:
    #         exceptions.handle(self.request,
    #                           _('Unable to retrieve roles list.'))
    #     return context
    def get_roles_data(self):
        roles = []
        try:
            roles = fiware_api.keystone.role_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                               _('Unable to retrieve roles list.'))
    
        return roles

    def get_permissions_data(self):
        permissions = []
        try:
            permissions = fiware_api.keystone.permission_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                               _('Unable to retrieve permissions list.'))
    
        return permissions

    def get_context_data(self, **kwargs):
        # NOTE(garcianavalon) add the CreateRoleForm to the view for inline create
        context = super(RolesView, self).get_context_data(**kwargs)
        context['form'] = application_forms.CreateRoleForm(self.request)
        context['add_to_field'] = 'roles'
        return context

class CreateRoleView(forms.ModalFormView):
    form_class = application_forms.CreateRoleForm
    template_name = 'idm/myApplications/role_create.html'
    success_url = reverse_lazy('horizon:idm:myApplications:roles_index')

    # def get_initial(self):
    #     # Set the application of the role
    #     application = fiware_api.keystone.get_default_application(self.request)
    #     default_role = api.keystone.get_default_role(self.request)
    #     return {'application_id': application.id,
    #             'application_name': application.name,
    #             'role_id': getattr(default_role, "id", None)}
