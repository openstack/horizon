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

import logging

from django.core.urlresolvers import reverse

from django.conf import settings

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon import workflows
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import views as idm_views
from openstack_dashboard.dashboards.idm.myApplications \
    import tables as application_tables
from openstack_dashboard.dashboards.idm.myApplications \
    import tabs as application_tabs
from openstack_dashboard.dashboards.idm.myApplications \
    import forms as application_forms
from openstack_dashboard.dashboards.idm.myApplications \
    import workflows as application_workflows


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
            "redirect_to": 'create',
        }
        return initial_data


class AvatarStepView(forms.ModalFormView):
    form_class = application_forms.AvatarForm
    template_name = 'idm/myApplications/avatar_step.html'

    def get_initial(self):
        application = fiware_api.keystone.application_get(self.request, self.kwargs['application_id'])
        initial_data = {
            "appID": application.id,
            "redirect_to": 'create',
        }
        return initial_data

    def get_context_data(self, **kwargs):
        context = super(AvatarStepView, self).get_context_data(**kwargs)
        application = fiware_api.keystone.application_get(self.request, self.kwargs['application_id'])
        context['application'] = application
        if hasattr(application, 'img_original'):
            image = getattr(application, 'img_original')
            image = settings.MEDIA_URL + image
        else:
            image = settings.STATIC_URL + 'dashboard/img/logos/original/app.png'
        context['image'] = image
        return context


class RolesView(workflows.WorkflowView):
    workflow_class = application_workflows.ManageApplicationRoles

    def __init__(self, *args, **kwargs):
        # NOTE(garcianavalon) call grandfather's method instead of
        # parents because parent (WorkflowView) overrides it with
        # out super and **kwargs
        super(workflows.WorkflowView, self).__init__(*args, **kwargs)

    def get_initial(self):
        initial = super(RolesView, self).get_initial()
        initial['superset_id'] = self.kwargs['application_id']
        return initial

    def get_workflow(self):
        workflow = super(RolesView, self).get_workflow()
        workflow.finalize_button_name = ("Finish")
        return workflow


class CreateRoleView(forms.ModalFormView):
    form_class = application_forms.CreateRoleForm
    template_name = 'idm/myApplications/roles/role_create.html'
    success_url = ''

    def get_success_url(self):
        """Redirects to the url it was called from."""
        return self.request.META['HTTP_REFERER']

    def get_context_data(self, **kwargs):
        context = super(CreateRoleView, self).get_context_data(**kwargs)
        context['application_id'] = self.kwargs['application_id']
        return context

    def get_initial(self):
        initial = super(CreateRoleView, self).get_initial()
        initial['application_id'] = self.kwargs['application_id']
        return initial


class EditRoleView(forms.ModalFormView):
    form_class = application_forms.EditRoleForm
    template_name = 'idm/myApplications/roles/role_edit.html'
    success_url = 'no use, all ajax!'

    def get_context_data(self, **kwargs):
        context = super(EditRoleView, self).get_context_data(**kwargs)
        context['role_id'] = self.kwargs['role_id']
        context['application_id'] = self.kwargs['application_id']
        # dont show the modal css classes
        context.pop('hide', None)
        return context

    def get_initial(self):
        initial = super(EditRoleView, self).get_initial()
        role = fiware_api.keystone.role_get(self.request,
                                            self.kwargs['role_id'])
        initial['role_id'] = role.id
        initial['name'] = role.name
        return initial


class DeleteRoleView(forms.ModalFormView):
    form_class = application_forms.DeleteRoleForm
    template_name = 'idm/myApplications/roles/role_delete.html'
    success_url = ''

    def get_success_url(self):
        """Redirects to the url it was called from."""
        return self.request.META['HTTP_REFERER']

    def get_context_data(self, **kwargs):
        context = super(DeleteRoleView, self).get_context_data(**kwargs)
        context['role_id'] = self.kwargs['role_id']
        context['application_id'] = self.kwargs['application_id']
        return context

    def get_initial(self):
        initial = super(DeleteRoleView, self).get_initial()
        initial['role_id'] = self.kwargs['role_id']
        return initial


class CreatePermissionView(forms.ModalFormView):
    form_class = application_forms.CreatePermissionForm
    template_name = 'idm/myApplications/roles/permission_create.html'
    success_url = ''

    def get_success_url(self):
        """Redirects to the url it was called from."""
        return self.request.META['HTTP_REFERER']

    def get_context_data(self, **kwargs):
        context = super(CreatePermissionView, self).get_context_data(**kwargs)
        context['application_id'] = self.kwargs['application_id']
        return context

    def get_initial(self):
        initial = super(CreatePermissionView, self).get_initial()
        initial['application_id'] = self.kwargs['application_id']
        return initial


class DetailApplicationView(tables.MultiTableView):
    template_name = 'idm/myApplications/detail.html'
    table_classes = (application_tables.MembersTable,
                     application_tables.AuthorizedOrganizationsTable)

    def get_members_data(self):
        users = []
        try:
            # NOTE(garcianavalon) Get all the users' ids that belong to
            # the application (they have one or more roles)
            all_users = api.keystone.user_list(self.request)
            role_assignments = fiware_api.keystone.user_role_assignments(
                self.request, application=self.kwargs['application_id'])
            users = [user for user in all_users if user.id
                     in set([a.user_id for a in role_assignments])]
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve member information."))
        return users

    def get_organizations_data(self):
        organizations = []
        try:
            # NOTE(garcianavalon) Get all the orgs' ids that belong to
            # the application (they have one or more roles)
            all_organizations, _more = api.keystone.tenant_list(
                self.request, admin=False)
            role_assignments = fiware_api.keystone.organization_role_assignments(
                self.request, application=self.kwargs['application_id'])
            organizations = [org for org in all_organizations if org.id
                     in set([a.organization_id for a in role_assignments])]
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve member information."))
        return organizations

    def _can_edit(self):
        # Allowed to edit the application if owns a role with the
        # 'Manage the application' permission.
        user = self.request.user
        allowed_applications = \
            fiware_api.keystone.list_user_allowed_applications_to_manage(
                self.request, user=user.id, organization=user.default_project_id)
        app_id = self.kwargs['application_id']
        return app_id in allowed_applications

    def _can_manage_roles(self):
        # Allowed to manage roles if owns a role with the
        # 'Manage roles' permission.
        user = self.request.user
        allowed_applications = \
            fiware_api.keystone.list_user_allowed_applications_to_manage_roles(
                self.request, user=user.id, organization=user.default_project_id)
        app_id = self.kwargs['application_id']
        return app_id in allowed_applications

    def allowed(self, request, user, application):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        default_org = request.user.default_project_id
        allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
            request,
            user=request.user.id,
            organization=default_org)
        return allowed.get(application.id, False)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DetailApplicationView, self).get_context_data(**kwargs)
        application_id = self.kwargs['application_id']
        application = fiware_api.keystone.application_get(
            self.request, application_id)
        context['application'] = application
        if hasattr(application, 'img_original'):
            image = getattr(application, 'img_original')
            image = settings.MEDIA_URL + image
        else:
            image = settings.STATIC_URL + 'dashboard/img/logos/original/app.png'
        context['image'] = image
        if self._can_edit():
            context['edit'] = True
        if self._can_manage_roles():
            context['manage_roles'] = True
        if self.allowed(self.request, self.request.user, application):
            context['viewCred'] = True
        return context


class AuthorizedMembersView(workflows.WorkflowView):
    workflow_class = application_workflows.ManageAuthorizedMembers

    def get_initial(self):
        initial = super(AuthorizedMembersView, self).get_initial()
        initial['superset_id'] = self.kwargs['application_id']
        return initial


class AuthorizedOrganizationsView(workflows.WorkflowView):
    workflow_class = application_workflows.ManageAuthorizedOrganizations

    def get_initial(self):
        initial = super(AuthorizedOrganizationsView, self).get_initial()
        initial['superset_id'] = self.kwargs['application_id']
        return initial


class BaseApplicationsMultiFormView(idm_views.BaseMultiFormView):
    template_name = 'idm/myApplications/edit.html'
    forms_classes = [
        application_forms.CreateApplicationForm,
        application_forms.AvatarForm,
        application_forms.CancelForm
    ]

    def get_endpoint(self, form_class):
        """Override to allow runtime endpoint declaration"""
        endpoints = {
            application_forms.CreateApplicationForm:
                reverse('horizon:idm:myApplications:info', kwargs=self.kwargs),
            application_forms.AvatarForm:
                reverse('horizon:idm:myApplications:avatar', kwargs=self.kwargs),
            application_forms.CancelForm:
                reverse('horizon:idm:myApplications:cancel', kwargs=self.kwargs),
        }
        return endpoints.get(form_class)

    @memoized.memoized_method
    def get_object(self):
        try:
            return fiware_api.keystone.application_get(
                self.request, self.kwargs['application_id'])
        except Exception:
            redirect = reverse("horizon:idm:myApplications:index")
            exceptions.handle(self.request, ('Unable to update application'),
                redirect=redirect)

    def get_initial(self, form_class):
        initial = super(BaseApplicationsMultiFormView, 
            self).get_initial(form_class)
        # Existing data from applciation
        callback_url = self.object.redirect_uris[0] \
                        if self.object.redirect_uris else None
        initial.update({
            "appID": self.object.id,
            "name": self.object.name,
            "description": self.object.description,
            "callbackurl": callback_url,
            "url": getattr(self.object, 'url', None),
            "redirect_to": "update"
        })
        return initial

    def get_context_data(self, **kwargs):
        context = super(BaseApplicationsMultiFormView, 
            self).get_context_data(**kwargs)
        if hasattr(self.object, 'img_original'):
            image = getattr(self.object, 'img_original')
            image = settings.MEDIA_URL + image
        else:
            image = settings.STATIC_URL + 'dashboard/img/logos/original/app.png'
        context['image'] = image
        return context


class CreateApplicationFormHandleView(BaseApplicationsMultiFormView):
    form_to_handle_class = application_forms.CreateApplicationForm


class AvatarFormHandleView(BaseApplicationsMultiFormView):
    form_to_handle_class = application_forms.AvatarForm


class CancelFormHandleView(BaseApplicationsMultiFormView):
    form_to_handle_class = application_forms.CancelForm

    def handle_form(self, form):
        """ Wrapper for form.handle for easier overriding."""
        return form.handle(self.request, form.cleaned_data, 
            application=self.object)
