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
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import views as idm_views
from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables
from openstack_dashboard.dashboards.idm.organizations \
    import tabs as organization_tabs
from openstack_dashboard.dashboards.idm.organizations \
    import forms as organization_forms
from openstack_dashboard.dashboards.idm.organizations \
    import workflows as organization_workflows


LOG = logging.getLogger('idm_logger')
AVATAR_ROOT = os.path.abspath(os.path.join(
    settings.MEDIA_ROOT, 'OrganizationAvatar'))

class IndexView(tabs.TabbedTableView):
    tab_group_class = organization_tabs.PanelTabs
    template_name = 'idm/organizations/index.html'


class CreateOrganizationView(forms.ModalFormView):
    form_class = organization_forms.CreateOrganizationForm
    template_name = 'idm/organizations/create.html'


class DetailOrganizationView(tables.MultiTableView):
    template_name = 'idm/organizations/detail.html'
    table_classes = (organization_tables.MembersTable,
                     organization_tables.AuthorizingApplicationsTable)
    
    def get_members_data(self):
        users = []
        try:
            # NOTE(garcianavalon) Filtering by project doesn't work anymore
            # in v3 API >< We need to get the role_assignments for the user's
            # id's and then filter the user list ourselves
            all_users = api.keystone.user_list(self.request)
            project_users_roles = api.keystone.get_project_users_roles(
                self.request,
                project=self.kwargs['organization_id'])
            users = [user for user in all_users if user.id in project_users_roles]
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve member information."))
        return users

    def get_applications_data(self):
        applications = []
        try:
            # TODO(garcianavalon) extract to fiware_api
            all_apps = fiware_api.keystone.application_list(self.request)
            apps_with_roles = [
                a.application_id for a 
                in fiware_api.keystone.organization_role_assignments(
                self.request, organization=self.kwargs['organization_id'])
            ]
            applications = [app for app in all_apps 
                            if app.id in apps_with_roles]
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve application list."))
        return idm_utils.filter_default(applications)

    def _can_edit(self):
        # Allowed if he is an admin in the organization
        # TODO(garcianavalon) move to fiware_api
        org_id = self.kwargs['organization_id']
        user_roles = api.keystone.roles_for_user(
            self.request, self.request.user.id, project=org_id)
        return 'admin' in [r.name for r in user_roles]

    def get_context_data(self, **kwargs):
        context = super(DetailOrganizationView, self).get_context_data(**kwargs)
        organization_id = self.kwargs['organization_id']
        organization = api.keystone.tenant_get(self.request, organization_id, admin=True)
        context['contact_info'] = organization.description
        context['organization.id'] = organization.id
        context['organization_name'] = organization.name
        if hasattr(organization, 'img_original'):
            image = settings.MEDIA_URL + getattr(organization, 'img_original')
        else:
            image = (settings.STATIC_URL 
                + 'dashboard/img/logos/original/group.png')
        context['image'] = image
        context['city'] = getattr(organization, 'city', '')
        context['email'] = getattr(organization, 'email', '')
        context['website'] = getattr(organization, 'website', '')
        if self._can_edit():
            context['edit'] = True
        return context


class OrganizationMembersView(workflows.WorkflowView):
    workflow_class = organization_workflows.ManageOrganizationMembers

    def get_initial(self):
        initial = super(OrganizationMembersView, self).get_initial()
        initial['superset_id'] = self.kwargs['organization_id']
        return initial


class BaseOrganizationsMultiFormView(idm_views.BaseMultiFormView):
    template_name = 'idm/organizations/edit.html'
    forms_classes = [
        organization_forms.InfoForm, 
        organization_forms.ContactForm, 
        organization_forms.AvatarForm, 
        organization_forms.CancelForm
    ]
    
    def get_endpoint(self, form_class):
        """Override to allow runtime endpoint declaration"""
        endpoints = {
            organization_forms.InfoForm: 
                reverse('horizon:idm:organizations:info', 
                kwargs=self.kwargs),
            organization_forms.ContactForm: 
                reverse('horizon:idm:organizations:contact', 
                kwargs=self.kwargs),
            organization_forms.AvatarForm: 
                reverse('horizon:idm:organizations:avatar', 
                kwargs=self.kwargs),
            organization_forms.CancelForm: 
                reverse('horizon:idm:organizations:cancel',  
                kwargs=self.kwargs),
        }
        return endpoints.get(form_class)

    def get_object(self):
        try:
            return api.keystone.tenant_get(
                self.request, self.kwargs['organization_id'])
        except Exception:
            redirect = reverse("horizon:idm:organizations:index")
            exceptions.handle(self.request, 
                    ('Unable to update organization'), redirect=redirect)

    def get_initial(self, form_class):
        initial = super(BaseOrganizationsMultiFormView, 
            self).get_initial(form_class)  
        # Existing data from organizations
        initial.update({
            "orgID": self.object.id,
            "name": self.object.name,
            "description": self.object.description,    
            "city": getattr(self.object, 'city', ' '),
            "email": getattr(self.object, 'email', ' '),
            "website":getattr(self.object, 'website', ' '),
        })
        return initial

    def get_context_data(self, **kwargs):

        context = super(BaseOrganizationsMultiFormView, 
            self).get_context_data(**kwargs)
        if hasattr(self.object, 'img_original'):
            image = getattr(self.object, 'img_original')
            image = settings.MEDIA_URL + image
        else:
            image = (settings.STATIC_URL 
                + 'dashboard/img/logos/original/group.png')
        context['image'] = image
        return context


class InfoFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = organization_forms.InfoForm

class ContactFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = organization_forms.ContactForm
   
class AvatarFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = organization_forms.AvatarForm

class CancelFormHandleView(BaseOrganizationsMultiFormView):
    form_to_handle_class = organization_forms.CancelForm

    def handle_form(self, form):
        """ Wrapper for form.handle for easier overriding."""
        return form.handle(self.request, 
                           form.cleaned_data, 
                           organization=self.object)
