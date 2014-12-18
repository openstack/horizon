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


INDEX_URL = "horizon:idm:organization:index"
PROJECT_USER_MEMBER_SLUG = "update_members"
LOG = logging.getLogger('idm_logger')

class UpdateProjectMembersAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateProjectMembersAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        err_msg = _('Unable to retrieve user list. Please try again later.')

        project_id = self.initial['project_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a project
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = (_('Could not find default role "%s" in Keystone') %
                       default)
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        # TODO(garcianavalon) hide the default role, show the 'owner'
        # role under the organization ('owner' is 'admin' for now)
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request)
        except Exception:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = {}
        try:
            # NOTE(garcianavalon) list all roles grouped by application
            # on which current user has the right to get and assign
            # TODO(garcianavalon) for now lets just list all user roles
            role_list['applications'] = fiware_api.keystone.role_list(request,
                                                    user=request.user.id)
            # NOTE(garcianavalon) we also need the organization (keystone)
            # roles here to add members
            role_list['organizations'] = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for k in role_list:
            # TODO(garcianavalon) different behaviour
            # TODO(garcianavalon) hide the default role, show the 'owner'
            # role under the organization ('owner' is 'admin' for now)
            for role in role_list[k]:
                field_name = self.get_member_field_name(role.id)
                label = role.name
                self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                    label=label)
                self.fields[field_name].choices = users_list
                self.fields[field_name].initial = []

        # Figure out users & roles
        # NOTE(garcianavalon) logic for this part: 
        # find all the (fiware)roles from the role_list(the ones the current user 
        # can get and assign) that are already assigned for each user and flag them
        # ALSO find out the organization members and assign them the 
        # default (keystone)role

        # First, load all users from the organization
        # with their roles
        try:
            project_users_roles = api.keystone.get_project_users_roles(request,
                                                                  project_id)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))

        # Second, load all the application roles for every user
        # but only the ones the user can assign
        for user_id in project_users_roles:
            try:
                # TODO(garcianavalon) filter by organization
                project_users_roles[user_id] = [
                        r.id for r in fiware_api.keystone.role_list(request,
                                                                user=user_id)
                        if r in role_list['applications']
                ]
                
            except Exception:
                exceptions.handle(request,
                                  err_msg,
                                  redirect=reverse(INDEX_URL))
        # Flag the alredy owned ones, both organization and application
        for user_id in project_users_roles:
            roles_ids = project_users_roles[user_id]
            for role_id in roles_ids:
                field_name = self.get_member_field_name(role_id)
                self.fields[field_name].initial.append(user_id)

    class Meta:
        name = _("Organization Members")
        slug = PROJECT_USER_MEMBER_SLUG


class UpdateProjectMembers(workflows.UpdateMembersStep):
    action_class = UpdateProjectMembersAction
    available_list_title = _("All Users")
    members_list_title = _("Organization Members")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")
    contributes = ("project_id",)

    def contribute(self, data, context):
        import pdb; pdb.set_trace()
        if data:
            try:
                # TODO(garcianavalon) fiware roles too
                roles = api.keystone.role_list(self.workflow.request)
                roles += fiware_api.keystone.role_list(self.workflow.request,
                                                user=self.workflow.request.user.id)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve role list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class ManageOrganizationMembers(workflows.Workflow):
    slug = "manage_organization_users"
    name = _("Manage Members")
    finalize_button_name = _("Save")
    success_message = _('Modified users in "%s".')
    failure_message = _('Unable to modify users in "%s".')
    success_url = "horizon:idm:organizations:index"
    default_steps = (UpdateProjectMembers,)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown organization')

    def handle(self, request, data):
        import pdb; pdb.set_trace()
        project_id = data['project_id']
        # Project-user member step
        member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)

        
        try:
            role_list = {}
            # NOTE(garcianavalon) list all roles grouped by application
            # on which current user has the right to get and assign
            # TODO(garcianavalon) for now lets just list all user roles
            role_list['applications'] = fiware_api.keystone.role_list(request,
                                                    user=request.user.id)
            # NOTE(garcianavalon) we also need the organization (keystone)
            # roles here to add members
            role_list['organizations'] = api.keystone.role_list(request)
            # Get the current roles for each user
            project_users_roles = api.keystone.get_project_users_roles(request,
                                                                  project_id)
            for user_id in project_users_roles:
                # TODO(garcianavalon) filter by organization
                project_users_roles[user_id] = [
                        r.id for r in fiware_api.keystone.role_list(request,
                                                                user=user_id)
                        if r in role_list['applications']
                ]
            # re-index by role with a user list for easier processing
            current_roles = {}
            for user_id in project_users_roles:
                for role_id in project_users_roles[user_id]:
                    current_roles[role_id] = current_roles.get(role_id, [])
                    current_roles[role_id].append(user_id)
            import pdb; pdb.set_trace()

            # Parse the form data
            modified_roles = {}
            for k in role_list:
                for role in role_list[k]:
                    field_name = member_step.get_member_field_name(role.id)
                    modified_roles[role.id] = data[field_name]

            import pdb; pdb.set_trace()            
            # Create the delete and add sets
            roles_to_delete = {}
            roles_to_add = {}
            for role_id in modified_roles:
                new_users = set(modified_roles[role_id])
                current_users = set(project_users_roles[role_id])
                # users to add-> users in N and not in C -> N-C
                roles_to_add[role_id] = new_users - current_users
                # users to delete -> users in C and not in N -> C-N
                roles_to_delete[role_id] = current_users - new_users

            import pdb; pdb.set_trace()
            # Add the roles
            for role_id in roles_to_add:
                for user_id in roles_to_add[role_id]:
                    if role_id in [r.id for r in role_list['applications']]:
                        fiware_api.keystone.add_role_to_user(request,
                                                            role_id,
                                                            user_id,
                                                            project_id)
                    elif role_id in [r.id for r in role_list['organizations']]:
                        api.keystone.add_tenant_user_role(request,
                                                        project=project_id,
                                                        user=user_id,
                                                        role=role_id)
                    else:
                        LOG.error('Unexpected role {0} not in possible roles'
                                    .format(role_id))
                        raise ValueError('Invalid role')

            import pdb; pdb.set_trace()
            # Remove the roles
            for role_id in roles_to_delete:
                for user_id in roles_to_delete[role_id]:
                    if role_id in [r.id for r in role_list['applications']]:
                        fiware_api.keystone.remove_role_from_user(request,
                                                            role_id,
                                                            user_id,
                                                            project_id)
                    elif role_id in [r.id for r in role_list['organizations']]:
                        api.keystone.remove_tenant_user_role(request,
                                                        project=project_id,
                                                        user=user_id,
                                                        role=role_id)
                    else:
                        LOG.error('Unexpected role {0} not in possible roles'
                                    .format(role_id))
                        raise ValueError('Invalid role')


        except Exception:
            exceptions.handle(request,
                          _('Failed to modify organization\'s members.'))
            return False