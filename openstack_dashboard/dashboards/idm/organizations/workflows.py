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

class UpdateProjectMembersAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateProjectMembersAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        import pdb; pdb.set_trace()
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
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False, 
                                                        widget=forms.HiddenInput())
        self.fields[default_role_name].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request)
        except Exception:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = []
        try:
            # NOTE(garcianavalon) the role logic is the following:
            # list all roles grouped by application on which current user
            # has the right to get and assign
            # TODO(garcianavalon) for now lets just list all user roles
            role_list = fiware_api.keystone.role_list(request,
                                                    user=request.user.id)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = users_list
            self.fields[field_name].initial = []

        # Figure out users & roles
        # NOTE(garcianavalon) logic for this part: 
        # find all the roles from the role_list(the ones the current user can get 
        # and assign) that are already assigned for each user and flag them

        # First, load all users from the organization
        try:
            project_users = api.keystone.user_list(request,
                                            project=project_id)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))

        # Load all the roles for every user
        users_roles = {}
        for user in project_users:
            # TODO(garcianavalon) what about the roles of users in the all list??
            try:
                users_roles[user.id] = fiware_api.keystone.role_list(request,
                                                        user=user)
                #users_roles = api.keystone.get_project_users_roles(request,
                #                                                   project_id)
            except Exception:
                exceptions.handle(request,
                                  err_msg,
                                  redirect=reverse(INDEX_URL))
        # Flag the alredy owned ones
        for user_id in users_roles:
            roles_ids = [r.id for r in users_roles[user_id] if r in role_list]
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

    def contribute(self, data, context):
        if data:
            try:
                # TODO(garcianavalon) fiware roles???
                roles = api.keystone.role_list(self.workflow.request)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve user list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class ManageOrganizationMembers(workflows.Workflow):
    slug = "update_organization_users"
    name = _("Edit Project")
    finalize_button_name = _("Save")
    success_message = _('Modified users in "%s".')
    failure_message = _('Unable to modify users in "%s".')
    success_url = "horizon:idm:organizations:index"
    default_steps = (UpdateProjectMembers,)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        super(ManageOrganizationMembers, self).__init__(request=request,
                                            context_seed=context_seed,
                                            entry_point=entry_point,
                                            *args,
                                            **kwargs)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown organization')

    def handle(self, request, data):
        # FIXME(gabriel): This should be refactored to use Python's built-in
        # sets and do this all in a single "roles to add" and "roles to remove"
        # pass instead of the multi-pass thing happening now.

        project_id = data['project_id']

        # update project members
        users_to_modify = 0
        # Project-user member step
        member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
        try:
            # Get our role options
            available_roles = api.keystone.role_list(request)
            # Get the users currently associated with this project so we
            # can diff against it.
            project_members = api.keystone.user_list(request,
                                                     project=project_id)
            users_to_modify = len(project_members)
            # TODO(garcianavalon) fiware roles
            for user in project_members:
                # Check if there have been any changes in the roles of
                # Existing project members.
                current_roles = api.keystone.roles_for_user(self.request,
                                                            user.id,
                                                            project_id)
                current_role_ids = [role.id for role in current_roles]

                for role in available_roles:
                    field_name = member_step.get_member_field_name(role.id)
                    # Check if the user is in the list of users with this role.
                    if user.id in data[field_name]:
                        # Add it if necessary
                        if role.id not in current_role_ids:
                            # user role has changed
                            api.keystone.add_tenant_user_role(
                                request,
                                project=project_id,
                                user=user.id,
                                role=role.id)
                        else:
                            # User role is unchanged, so remove it from the
                            # remaining roles list to avoid removing it later.
                            index = current_role_ids.index(role.id)
                            current_role_ids.pop(index)

                # Prevent admins from doing stupid things to themselves.
                is_current_user = user.id == request.user.id
                is_current_project = project_id == request.user.tenant_id
                admin_roles = [role for role in current_roles
                               if role.name.lower() == 'admin']
                if len(admin_roles):
                    removing_admin = any([role.id in current_role_ids
                                          for role in admin_roles])
                else:
                    removing_admin = False
                if is_current_user and is_current_project and removing_admin:
                    # Cannot remove "admin" role on current(admin) project
                    msg = _('You cannot revoke your administrative privileges '
                            'from the project you are currently logged into. '
                            'Please switch to another project with '
                            'administrative privileges or remove the '
                            'administrative role manually via the CLI.')
                    messages.warning(request, msg)

                # Otherwise go through and revoke any removed roles.
                else:
                    for id_to_delete in current_role_ids:
                        api.keystone.remove_tenant_user_role(
                            request,
                            project=project_id,
                            user=user.id,
                            role=id_to_delete)
                users_to_modify -= 1

            # Grant new roles on the project.
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                # Count how many users may be added for exception handling.
                users_to_modify += len(data[field_name])
            for role in available_roles:
                users_added = 0
                field_name = member_step.get_member_field_name(role.id)
                for user_id in data[field_name]:
                    if not filter(lambda x: user_id == x.id, project_members):
                        api.keystone.add_tenant_user_role(request,
                                                          project=project_id,
                                                          user=user_id,
                                                          role=role.id)
                    users_added += 1
                users_to_modify -= users_added
        except Exception:
            exceptions.handle(request,
                              _('Failed to modify %(users_to_modify)s'
                                ' project members%(group_msg)s and '
                                'update project quotas.')
                              % {'users_to_modify': users_to_modify})
            return False