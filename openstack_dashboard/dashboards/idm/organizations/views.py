# Copyright (C) 2014 Universidad Politecnica de Madrid
#
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

import os
import logging

from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon import workflows
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.idm import views as idm_views
from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables
from openstack_dashboard.dashboards.idm.organizations \
    import tabs as organization_tabs
from openstack_dashboard.dashboards.idm.organizations.forms \
    import  InfoForm, ContactForm, AvatarForm, CancelForm, CreateOrganizationForm
from openstack_dashboard.dashboards.idm.organizations \
    import workflows as organization_workflows


LOG = logging.getLogger('idm_logger')
AVATAR_ROOT = os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'OrganizationAvatar'))

class IndexView(tabs.TabbedTableView):
    tab_group_class = organization_tabs.PanelTabs
    template_name = 'idm/organizations/index.html'


class CreateOrganizationView(forms.ModalFormView):
    form_class = CreateOrganizationForm
    template_name = 'idm/organizations/create.html'


class DetailOrganizationView(tables.MultiTableView):
    template_name = 'idm/organizations/detail.html'
    table_classes = (organization_tables.MembersTable,
                     organization_tables.ApplicationsTable)
    
    def get_members_data(self):        
        users = []
        try:
            # NOTE(garcianavalon) Filtering by project doesn't work anymore
            # in v3 API >< We need to get the role_assignments for the user's
            # id's and then filter the user list ourselves
            all_users = api.keystone.user_list(self.request,
                                         project=self.kwargs['organization_id'])
            project_users_roles = api.keystone.get_project_users_roles(self.request,
                                                 project=self.kwargs['organization_id'])
            users = [user for user in all_users if user.id in project_users_roles]
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve member information."))
        return users

    def get_applications_data(self):
        applications = []
        return applications

    def get_context_data(self, **kwargs):
        context = super(DetailOrganizationView, self).get_context_data(**kwargs)
        organization_id = self.kwargs['organization_id']
        organization = api.keystone.tenant_get(self.request, organization_id, admin=True)
        context['contact_info'] = organization.description
        context['organization.id'] = organization.id
        context['organization_name'] = organization.name
        context['image'] = getattr(organization, 'img', '/static/dashboard/img/logos/small/group.png')
        context['city'] = getattr(organization, 'city', '')
        context['email'] = getattr(organization, 'email', '')
        context['website'] = getattr(organization, 'website', '')
        return context


class OrganizationMembersView(workflows.WorkflowView):
    workflow_class = organization_workflows.ManageOrganizationMembers

    def get_initial(self):
        initial = super(OrganizationMembersView, self).get_initial()

        project_id = self.kwargs['organization_id']
        initial['project_id'] = project_id

        return initial


class BaseOrganizationsMultiFormView(idm_views.BaseMultiFormView):
    template_name = 'idm/organizations/edit.html'
    forms_classes = [InfoForm, ContactForm, AvatarForm, CancelForm]
    
    def get_endpoint(self, form_class):
        """Override to allow runtime endpoint declaration"""
        endpoints = {
            InfoForm: reverse('horizon:idm:organizations:info', 
                                kwargs=self.kwargs),
            ContactForm: reverse('horizon:idm:organizations:contact', 
                                kwargs=self.kwargs),
            AvatarForm: reverse('horizon:idm:organizations:avatar', 
                                kwargs=self.kwargs),
            CancelForm: reverse('horizon:idm:organizations:cancel', 
                                kwargs=self.kwargs),
        }
        return endpoints.get(form_class)

    def get_object(self):
        try:
            return api.keystone.tenant_get(self.request, self.kwargs['organization_id'])
        except Exception:
            redirect = reverse("horizon:idm:organizations:index")
            exceptions.handle(self.request, 
                    _('Unable to update organization'), redirect=redirect)

    def get_initial(self, form_class):
        initial = super(BaseOrganizationsMultiFormView, self).get_initial(form_class)  
        # Existing data from organizations
        initial.update({
            "orgID": self.object.id,
            "name": self.object.name,
            "description": self.object.description,    
            "city": getattr(self.object, 'city', 'patata'),
            "email": getattr(self.object, 'email', 'patata'),
            "website":getattr(self.object, 'website', 'patata'),
        })
        return initial

    def get_context_data(self, **kwargs):

        context = super(BaseOrganizationsMultiFormView, self).get_context_data(**kwargs)
        context['image'] = getattr(self.object, 'img', 
                            '/static/dashboard/img/logos/small/group.png')
        return context


class InfoFormHandleView(BaseOrganizationsMultiFormView):    
    form_to_handle_class = InfoForm

class ContactFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = ContactForm
   
class AvatarFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = AvatarForm

class CancelFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = CancelForm

    def handle_form(self, form):
        """ Wrapper for form.handle for easier overriding."""
        return form.handle(self.request, form.cleaned_data, organization=self.object)
