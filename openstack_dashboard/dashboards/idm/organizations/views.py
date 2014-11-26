# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.core.files import File
from django.views.generic.base import TemplateView

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.utils import memoized
from horizon import workflows
from horizon import tabs
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables
from openstack_dashboard.dashboards.idm.organizations \
    import tabs as organization_tabs
from openstack_dashboard.dashboards.idm.organizations \
    import forms as organization_forms

AVATAR_ROOT = os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'OrganizationAvatar'))


class IndexView(tabs.TabbedTableView):
    tab_group_class = organization_tabs.PanelTabs
    template_name = 'idm/organizations/index.html'


class CreateOrganizationView(forms.ModalFormView):
    form_class = organization_forms.CreateOrganizationForm
    template_name = 'idm/organizations/create.html'


class DetailOrganizationView(tables.MultiTableView):
    template_name = 'idm/organizations/detail.html'
    table_classes = (organization_tables.MembersTable,
                     organization_tables.ApplicationsTable)
    
    def get_members_data(self):        
        user = []
        user_id = self.request.user.id
        try:
            user_info = api.keystone.user_get(self.request, self.request.user.id)
            user.append(user_info)
            
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve member information."))
        return user

    def get_applications_data(self):
        applications = []
        return applications

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DetailOrganizationView, self).get_context_data(**kwargs)
        organization_id = self.kwargs['organization_id']
        organization = api.keystone.tenant_get(self.request, organization_id, admin=True)
        context['contact_info'] = organization.description
        context['organization.id'] = organization.id
        context['organization_name'] = organization.name
        return context


class MultiFormView(TemplateView):
    template_name = 'idm/organizations/edit.html'

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.tenant_get(self.request, self.kwargs['organization_id'])
        except Exception:
            redirect = reverse("horizon:idm:organizations:index")
            exceptions.handle(self.request, _('Unable to update organization'), redirect=redirect)



    def get_context_data(self, **kwargs):
        context = super(MultiFormView, self).get_context_data(**kwargs)
        organization = self.get_object()
        context['organization'] = organization

        #Existing data from organizations
        initial_data = {
            "orgID": organization.id,
            "name": organization.name,
            "description": organization.description,
        }
        #Create forms
        info = organization_forms.InfoForm(self.request, initial=initial_data)
        contact = organization_forms.ContactForm(self.request, initial=initial_data)
        avatar = organization_forms.AvatarForm(self.request, initial=initial_data)
        cancel = organization_forms.CancelForm(self.request, initial=initial_data)

        #Actions and titles
        info.action = 'info/'
        info.title = 'Information'
        contact.action = "contact/"
        contact.title = 'Contact Information'
        avatar.action = "avatar/"
        avatar.title = 'Avatar Update'
        cancel.action = "cancel/"
        cancel.title = 'Cancel'

        context['form'] = [info, contact, avatar, cancel]       
        return context

class HandleForm(forms.ModalFormView):
    template_name = ''
    http_method_not_allowed = ['get']


class InfoFormView(HandleForm):    
    form_class = organization_forms.InfoForm
    http_method_not_allowed = ['get']

class ContactFormView(HandleForm):
    form_class = organization_forms.ContactForm

   
class AvatarFormView(forms.ModalFormView):
    form_class = organization_forms.AvatarForm


class CancelFormView(forms.ModalFormView):
    form_class = organization_forms.CancelForm