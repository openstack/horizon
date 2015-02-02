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


INDEX_URL = "horizon:idm:organizations:index"
PROJECT_USER_MEMBER_SLUG = "update_members"
LOG = logging.getLogger('idm_logger')

class RolesMixin(object):
    """Simple container for the roles logic."""
    # TODO(garcianavalon) maybe move to fiware_api
    def list_all_roles(self, request, project_id):
        role_list = {}
        # NOTE(garcianavalon) list all roles grouped by application
        # on which current user has the right to get and assign
        role_list['applications'] = fiware_api.keystone.list_allowed_roles_to_assign(request,
                                                user=request.user.id,
                                                organization=project_id)
        # NOTE(garcianavalon) we also need the organization (keystone)
        # roles here to add members.
        role_list['organization'] = api.keystone.role_list(request)
        # Little trick to show them together, we simulate the organization to be
        # an application
        for role in role_list['organization']:
            role.application = project_id
        return role_list

    def list_users_with_roles(self, request, project_id, available_roles):
        # First, load all users from the organization
        # with their roles
        project_users_roles = api.keystone.get_project_users_roles(request,
                                                              project_id)
        # Second, load all the organization-scoped application roles for every user
        # but only the ones the user can assign (and only scoped for the current
        # organization)
        for user_id in project_users_roles:
            project_users_roles[user_id] += [
                r.id for r in fiware_api.keystone.role_list(
                                                    request,
                                                    user=user_id,
                                                    organization=project_id)
                    if r in available_roles
            ]
        return project_users_roles

class UpdateProjectMembersAction(workflows.MembershipAction, RolesMixin):
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
        try:
            all_users = api.keystone.user_list(request)
        except Exception:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        try:
            role_list = self.list_all_roles(request, project_id)
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
                widget = forms.widgets.SelectMultiple(
                                attrs={'data-application-name':role.application})
                self.fields[field_name] = forms.MultipleChoiceField(
                                                        required=False,
                                                        label=label,
                                                        widget=widget)
                self.fields[field_name].choices = users_list
                self.fields[field_name].initial = []

        # Figure out users & roles
        # NOTE(garcianavalon) logic for this part: 
        # find all the (fiware)roles from the role_list(the ones the current user 
        # can get and assign) that are already assigned for each user and flag them
        # ALSO find out the organization members and assign them the 
        # default (keystone)role
        try:
            project_users_roles = self.list_users_with_roles(request,
                                                            project_id,
                                                            role_list['applications'])
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


class UpdateProjectMembers(workflows.UpdateMembersStep, RolesMixin):
    action_class = UpdateProjectMembersAction
    available_list_title = _("All Users")
    members_list_title = _("Organization Members")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")
    contributes = ("project_id",)

    def contribute(self, data, context):
        project_id = context['project_id']
        if data:
            try:
                role_list = self.list_all_roles(self.workflow.request, project_id)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve role list.'))

            post = self.workflow.request.POST
            for k in role_list:
                for role in role_list[k]:
                    field = self.get_member_field_name(role.id)
                    context[field] = post.getlist(field)
        return context


class ManageOrganizationMembers(workflows.Workflow, RolesMixin):
    slug = "manage_organization_users"
    name = _("Manage Members")
    finalize_button_name = _("Save")
    success_message = _('Modified users.')
    failure_message = _('Unable to modify users.')
    success_url = "horizon:idm:organizations:detail"
    default_steps = (UpdateProjectMembers,)

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return reverse(self.success_url, 
                    kwargs={'organization_id':self.context['project_id']})

    def handle(self, request, data):
        project_id = data['project_id']
        # Project-user member step
        member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)

        try:
            role_list = self.list_all_roles(request, project_id)
            project_users_roles = self.list_users_with_roles(request,
                                                            project_id,
                                                            role_list['applications'])
            # re-index by role with a user list for easier processing in later steps
            current_roles = idm_utils.swap_dict(project_users_roles)

            # Parse the form data
            modified_roles = {}
            for k in role_list:
                for role in role_list[k]:
                    field_name = member_step.get_member_field_name(role.id)
                    modified_roles[role.id] = data[field_name]
            
            # Create the delete and add sets
            roles_to_add, roles_to_delete = self._create_add_and_delete_sets(
                                                                modified_roles, 
                                                                current_roles)
            application_roles = [r.id for r in role_list['applications']]
            organization_roles = [r.id for r in role_list['organization']]

            # Add the roles
            add_methods = [
                (application_roles, fiware_api.keystone.add_role_to_user),
                (organization_roles, api.keystone.add_tenant_user_role)
            ]
            self._apply_method(roles_to_add, add_methods, project_id)

            # Remove the roles
            delete_methods = [
                (application_roles, fiware_api.keystone.remove_role_from_user),
                (organization_roles, api.keystone.remove_tenant_user_role)
            ]
            self._apply_method(roles_to_delete, delete_methods, project_id)

            return True
        except Exception:
            exceptions.handle(request,
                          _('Failed to modify organization\'s members.'))
            return False

    def _create_add_and_delete_sets(self, modified_roles, current_roles):
        roles_to_add = {}
        roles_to_delete = {}
        for role_id in modified_roles:
            new_users = set(modified_roles.get(role_id, []))
            current_users = set(current_roles.get(role_id, []))
            # users to add-> users in N and not in C -> N-C
            users_to_add = new_users - current_users
            if users_to_add:
                roles_to_add[role_id] = users_to_add
            # users to delete -> users in C and not in N -> C-N
            users_to_delete = current_users - new_users
            if users_to_delete:
                roles_to_delete[role_id] = users_to_delete
        return roles_to_add, roles_to_delete


    def _apply_method(self, roles_users, methods, project_id):
        """Utility method to iterate all elements in the dictionary and 
        apply a method based on a condition.

            :param methods: a list with the methods to apply to each group
            :type methods: list of tuples (container, function)
        """
        for role_id in roles_users:
            function = self._decide_function(role_id, methods)
            if not function:
                # We should never get to this point
                LOG.error('Unexpected role {0} not in possible roles'.format(role_id))
                raise ValueError('Invalid role')
            for user_id in roles_users[role_id]:
                function(self.request,
                        project=project_id,
                        user=user_id,
                        role=role_id)

    def _decide_function(self, role_id, methods):
        for (container, function) in methods:
            if role_id not in container:
                continue
            return function
        return None
