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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import workflows as idm_workflows

# NOTE(garcianavalon) Beware! we are reusing the membership stuff
# but changing assign roles to users to assign permissions to roles.
# TODO(garcianavalon) rename al the 'role' stuff from the membership workflow
# to 'permission' and the 'user' one to 'role'
INDEX_URL = "horizon:idm:myApplications:index"
APPLICATION_ROLE_PERMISSION_SLUG = "fiware_roles"
LOG = logging.getLogger('idm_logger')

class UpdateApplicationRolesAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateApplicationRolesAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        err_msg = _('Unable to retrieve role list. Please try again later.')
        application_id = self.initial['application_id']
        # Save the application_id for use in template
        self.application_id = application_id

        # Get list of available roles
        try:
            role_list = fiware_api.keystone.role_list(request,
                                                    application=application_id)
            # Save the role_list to use in the template
            self.application_roles = role_list
            # TODO(garcianavalon) the default roles should be non editable!
            # TODO(garcianavalon) filtering for internal
            # role_list += fiware_api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request, err_msg)

        # Get list of permissions
        try:
            permission_list = fiware_api.keystone.permission_list(request,
                                                    application=application_id)
            # Save the permission_list to use in the template
            self.application_permissions = permission_list
            # TODO(garcianavalon) the default roles should be non editable!
            # TODO(garcianavalon) filtering for internal
            # permission_list += fiware_api.keystone.permission_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))

        for permission in permission_list:
            field_name = self.get_member_field_name(permission.id)
            label = permission.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = [
                (role.id, role.name) for role in role_list
            ]
            self.fields[field_name].initial = []

        # Figure out roles and permissions
        application_role_permissions = {}
        try:
            for role in role_list:
                application_role_permissions[role.id] = [
                    p.id for p in fiware_api.keystone.permission_list(
                                                        request,
                                                        role=role.id)
                ]
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))

        # Flag the alredy owned ones, both organization and application
        for role_id in application_role_permissions:
            permissions_ids = application_role_permissions[role_id]
            for permission_id in permissions_ids:
                field_name = self.get_member_field_name(permission_id)
                self.fields[field_name].initial.append(role_id)

    def get_default_role_field_name(self):
        """ No use for this method, this workflow doesn't support the
        'adding from a pool of all resources' logic as the user one does.
        """
        #return "default_" + self.slug + "_role"
        return

    def get_member_field_name(self, permission_id):
        return self.slug + "_permission_" + permission_id


    class Meta:
        name = _("Application roles")
        slug = APPLICATION_ROLE_PERMISSION_SLUG


class UpdateApplicationRoles(workflows.UpdateMembersStep):
    action_class = UpdateApplicationRolesAction
    members_list_title = _("Application roles")
    contributes = ("application_id",)
    template_name = "idm/myApplications/roles/_workflow_step_update_members.html"

    def contribute(self, data, context):
        application_id = context['application_id']
        if data:
            try:
                permission_list = fiware_api.keystone.permission_list(
                                                self.workflow.request, 
                                                application=application_id)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve permission list.'))

            post = self.workflow.request.POST
            for permission in permission_list:
                field = self.get_member_field_name(permission.id)
                context[field] = post.getlist(field)
        return context


class ManageApplicationRoles(workflows.Workflow):
    slug = "manage_application_roles"
    name = _("Manage Roles")
    finalize_button_name = _("Save")
    success_message = _('Modified roles and permissions.')
    failure_message = _('Unable to modify roles and permissions.')
    success_url = "horizon:idm:myApplications:detail"
    default_steps = (UpdateApplicationRoles,)

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return reverse(self.success_url, 
                    kwargs={'application_id':self.context['application_id']})

    def handle(self, request, data):
        application_id = data['application_id']
        member_step = self.get_step(APPLICATION_ROLE_PERMISSION_SLUG)

        try:
            # TODO(garcianavalon) exclude from processing the non-editable roles
            role_list = fiware_api.keystone.role_list(request,
                                                application=application_id)
            permission_list = fiware_api.keystone.permission_list(request,
                                                application=application_id)
            application_role_permissions = {}
            for role in role_list:
                application_role_permissions[role.id] = \
                    fiware_api.keystone.permission_list(request,
                                                        role=role.id)
            # re-index by permission with role list for easier processing 
            # in later steps
            current_permissions = idm_utils.swap_dict(application_role_permissions)

            # Parse the form data
            modified_permissions = {}
            for permission in permission_list:
                field_name = member_step.get_member_field_name(permission.id)
                modified_permissions[permission.id] = data[field_name]
            
            # Create the remove and add sets
            permissions_to_add, permissions_to_remove = self._create_add_and_remove_sets(
                                                                modified_permissions, 
                                                                current_permissions)
            # Add the permissions
            for permission in permissions_to_add:
                for role in permissions_to_add[permission]:
                    fiware_api.keystone.add_permission_to_role(request, permission, role)

            # Remove the permissions
            for permission in permissions_to_remove:
                for role in permissions_to_remove[permission]:
                    fiware_api.keystone.remove_permission_from_role(request, permission, role)

            return True
        except Exception:
            exceptions.handle(request,
                          _('Failed to modify application\'s roles.'))
            return False

    def _create_add_and_remove_sets(self, modified_permissions, current_permissions):
        # TODO(garcianavalon) extract this logic as utils or extend worflow
        permissions_to_add = {}
        permissions_to_remove = {}
        for role_id in modified_permissions:
            new_users = set(modified_permissions.get(role_id, []))
            current_users = set(current_permissions.get(role_id, []))
            # users to add-> users in N and not in C -> N-C
            users_to_add = new_users - current_users
            if users_to_add:
                permissions_to_add[role_id] = users_to_add
            # users to remove -> users in C and not in N -> C-N
            users_to_remove = current_users - new_users
            if users_to_remove:
                permissions_to_remove[role_id] = users_to_remove
        return permissions_to_add, permissions_to_remove


# APPLICATION ROLES
class AuthorizedMembersApi(idm_workflows.RelationshipApiInterface):
    """FIWARE Roles logic to assign"""
    
    def _list_all_owners(self, request, superset_id):
        all_users = api.keystone.user_list(request)
        return  [(user.id, user.name) for user in all_users]


    def _list_all_objects(self, request, superset_id):
        all_roles = fiware_api.keystone.role_list(request)
        default_org = api.keystone.user_get(
            request, request.user).default_project_id
        allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
            request,
            user=request.user.id,
            organization=default_org)
        self.allowed = [role for role in all_roles 
                   if role.id in allowed[superset_id]]
        return self.allowed


    def _list_current_assignments(self, request, superset_id):
        # NOTE(garcianavalon) logic for this part:
        # load all the organization-scoped application roles for every user
        # but only the ones the user can assign
        application_users_roles = {}
        allowed_ids = [r.id for r in self.allowed]
        role_assignments = fiware_api.keystone.user_role_assignments(
            request, application=superset_id)
        users = set([a.user_id for a in role_assignments])
        for user_id in users:
            application_users_roles[user_id] = [
                a.role_id for a in role_assignments
                if a.user_id == user_id
                and a.role_id in allowed_ids
            ]
        return application_users_roles


    def _get_default_object(self, request):
        return None


    def _add_object_to_owner(self, request, superset, owner, obj):
        default_org = api.keystone.user_get(request, owner).default_project_id
        fiware_api.keystone.add_role_to_user(request,
                                             application=superset,
                                             user=owner,
                                             organization=default_org,
                                             role=obj)


    def _remove_object_from_owner(self, request, superset, owner, obj):
        default_org = api.keystone.user_get(request, owner).default_project_id
        fiware_api.keystone.remove_role_from_user(request,
                                                  application=superset,
                                                  user=owner,
                                                  organization=default_org,
                                                  role=obj)


    def _get_supersetid_name(self, request, superset_id):
        application = fiware_api.keystone.application_get(request, superset_id)
        return application.name


class UpdateAuthorizedMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = _('Unable to retrieve data. Please try again later.')
    RELATIONSHIP_CLASS = AuthorizedMembersApi
    ERROR_URL = INDEX_URL

    class Meta:
        name = _("Manage your applications' roles")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateAuthorizedMembers(idm_workflows.UpdateRelationship):
    action_class = UpdateAuthorizedMembersAction
    available_list_title = _("Organization Members")
    members_list_title = _("Members with roles")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")
    RELATIONSHIP_CLASS = AuthorizedMembersApi


class ManageAuthorizedMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_users_application_roles"
    name = _("Manage your applications' Roles")
    finalize_button_name = _("Save")
    success_message = _('Modified users.')
    failure_message = _('Unable to modify users.')
    success_url = "horizon:idm:myApplications:detail"
    default_steps = (UpdateAuthorizedMembers,)
    RELATIONSHIP_CLASS = AuthorizedMembersApi

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return reverse(self.success_url, 
                    kwargs={'application_id':self.context['superset_id']})