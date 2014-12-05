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

import logging
import json

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from django.views.generic.base import TemplateView

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm.myApplications \
            import tables as application_tables
from openstack_dashboard.dashboards.idm.myApplications \
            import tabs as application_tabs
from openstack_dashboard.dashboards.idm.myApplications \
            import forms as application_forms

LOG = logging.getLogger('idm_logger')


class IndexView(tabs.TabbedTableView):
    tab_group_class = application_tabs.PanelTabs
    template_name = 'idm/myApplications/index.html'

  
class CreateView(forms.ModalFormView):
    form_class = application_forms.CreateApplicationForm
    template_name = 'idm/myApplications/create.html'

    def get_initial(self):
        initial_data = {
            "appID" : "",
            "nextredir": 'create',
        }
        return initial_data
    

class UploadImageView(forms.ModalFormView):
    form_class = application_forms.UploadImageForm
    template_name = 'idm/myApplications/upload.html'

    def get_initial(self):
        application = fiware_api.keystone.application_get(self.request, self.kwargs['application_id'])
        initial_data = {
            "appID": application.id,
            "nextredir": 'create',
        }
        return initial_data

    def get_context_data(self, **kwargs):
        context = super(UploadImageView, self).get_context_data(**kwargs)
        application = fiware_api.keystone.application_get(self.request, self.kwargs['application_id'])
        context['application'] = application
        context['image'] = getattr(application, 'img', '/static/dashboard/img/logos/small/app.png')
        return context


# NOTE(garcianavalon) from horizon.forms.views
ADD_TO_FIELD_HEADER = "HTTP_X_HORIZON_ADD_TO_FIELD"
class RolesView(tables.MultiTableView):
    """ Logic for the asynchronous widget to manage roles and permissions at the
    application level.
    """
    template_name = 'idm/myApplications/roles.html'
    table_classes = (application_tables.RolesTable,
                     application_tables.PermissionsTable)

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
        context['inline_forms'] = True
        context['roles_form'] = application_forms.CreateRoleForm(self.request)
        context['roles_add_to_field'] = 'roles'
        context['permissions_form'] = application_forms.CreatePermissionForm(self.request)
        context['permissions_add_to_field'] = 'permissions'
        return context

class CreateRoleView(forms.ModalFormView):
    form_class = application_forms.CreateRoleForm
    template_name = 'idm/myApplications/role_create.html'
    success_url = reverse_lazy('horizon:idm:myApplications:roles_index')

class CreatePermissionView(forms.ModalFormView):
    form_class = application_forms.CreatePermissionForm
    template_name = 'idm/myApplications/permission_create.html'
    success_url = reverse_lazy('horizon:idm:myApplications:roles_index')

class DetailApplicationView(TemplateView):
    template_name = 'idm/myApplications/detail.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DetailApplicationView, self).get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        application = fiware_api.keystone.application_get(self.request, application_id)
        context['description'] = application.description
        context['url'] = application.extra['url']
        context['image'] = application.extra.get('img', 'Image not present in extra')
        if application.redirect_uris:
            context['callbackURL'] = application.redirect_uris[0]
        else:
            context['callbackURL'] = ''
        context['application_name'] = application.name
        context['application_id'] = application_id
        context['application_secret'] = application.secret
        return context

class MultiFormView(TemplateView):
    template_name = 'idm/myApplications/edit.html'

    @memoized.memoized_method
    def get_object(self):
        try:
            return fiware_api.keystone.application_get(self.request, self.kwargs['application_id'])
        except Exception:
            redirect = reverse("horizon:idm:myApplications:index")
            exceptions.handle(self.request, _('Unable to update application'), redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(MultiFormView, self).get_context_data(**kwargs)
        application = self.get_object()
        context['application'] = application
        context['image'] = application.extra.get('img', 'Image not present in extra')

        #Existing data from organizations
        initial_data = {
            "appID": application.id,
            "name": application.name,
            "description": application.description,
            "callbackurl": application.redirect_uris[0],
            "url": application.extra.get('url', None),
            "nextredir": "update" 
        }
        
        #Create forms
        info = application_forms.CreateApplicationForm(self.request, initial=initial_data)
        avatar = application_forms.UploadImageForm(self.request, initial=initial_data)
        cancel = application_forms.CancelForm(self.request, initial=initial_data)

        #Actions and titles
        # TODO(garcianavalon) quizas es mejor meterlo en el __init__ del form
        info.action = 'info/'
        info.title = 'Information'
        avatar.action = "avatar/"
        avatar.title = 'Avatar Update'
        cancel.action = "cancel/"
        cancel.title = ' '

        context['forms'] = [info, avatar]
        context['cancel_form'] = cancel
        return context

class CancelFormView(forms.ModalFormView):
    form_class = application_forms.CancelForm
    http_method_not_allowed = ['get']
