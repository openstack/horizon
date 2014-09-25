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


from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas

INDEX_URL = "horizon:idm:organizations:index"
ADD_USER_URL = "horizon:idm:organizations:create_user"
PROJECT_GROUP_ENABLED = keystone.VERSIONS.active >= 3
PROJECT_USER_MEMBER_SLUG = "update_members"
PROJECT_GROUP_MEMBER_SLUG = "update_group_members"



class CreateOrganizationInfoAction(workflows.Action):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"),
                           max_length=64)
    description = forms.CharField(widget=forms.widgets.Textarea(),
                                  label=_("Description"),
                                  required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    def __init__(self, request, *args, **kwargs):
        super(CreateOrganizationInfoAction, self).__init__(request,
                                                      *args,
                                                      **kwargs)
        # For keystone V3, display the two fields in read-only
        if keystone.VERSIONS.active >= 3:
            readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput

    class Meta:
        name = _("Organization Information")
        help_text = _("Create a new organization. \
            Please enter your organization name and a description. \
            On the next tab, choose the users that will belong to your organization.")


class CreateOrganizationInfo(workflows.Step):
    action_class = CreateOrganizationInfoAction
    contributes = ("domain_id",
                   "domain_name",
                   "organization_id",
                   "name",
                   "description",
                   "enabled")


class UpdateOrganizationMembersAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateOrganizationMembersAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        err_msg = _('Unable to retrieve user list. Please try again later.')
        # Use the domain_id from the organization
        domain_id = self.initial.get("domain_id", None)
        organization_id = ''
        if 'organization_id' in self.initial:
            organization_id = self.initial['organization_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a organization
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = _('Could not find default role "%s" in Keystone') % \
                        default
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request,
                                               domain=domain_id)
        except Exception:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
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
        if organization_id:
            try:
                users_roles = api.keystone.get_project_users_roles(request,
                                                                   organization_id)
            except Exception:
                exceptions.handle(request,
                                  err_msg,
                                  redirect=reverse(INDEX_URL))

            for user_id in users_roles:
                roles_ids = users_roles[user_id]
                for role_id in roles_ids:
                    field_name = self.get_member_field_name(role_id)
                    self.fields[field_name].initial.append(user_id)


    class Meta:
        name = _("Organization Members")
        slug = PROJECT_USER_MEMBER_SLUG


class UpdateOrganizationMembers(workflows.UpdateMembersStep):
    action_class = UpdateOrganizationMembersAction
    available_list_title = _("All Users")
    members_list_title = _("Organization Members")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")

    def contribute(self, data, context):
        if data:
            try:
                roles = api.keystone.role_list(self.workflow.request)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve user list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context



class UpdateOrganizationGroupsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateOrganizationGroupsAction, self).__init__(request,
                                                        *args,
                                                        **kwargs)
        err_msg = _('Unable to retrieve group list. Please try again later.')
        # Use the domain_id from the organization
        domain_id = self.initial.get("domain_id", None)
        organization_id = ''
        if 'organization_id' in self.initial:
            organization_id = self.initial['organization_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a organization
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = _('Could not find default role "%s" in Keystone') % \
                        default
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available groups
        all_groups = []
        try:
            all_groups = api.keystone.group_list(request,
                                                 domain=domain_id)
        except Exception:
            exceptions.handle(request, err_msg)
        groups_list = [(group.id, group.name) for group in all_groups]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = groups_list
            self.fields[field_name].initial = []

        # Figure out groups & roles
        if organization_id:
            for group in all_groups:
                try:
                    roles = api.keystone.roles_for_group(self.request,
                                                         group=group.id,
                                                         organization=organization_id)
                except Exception:
                    exceptions.handle(request,
                                      err_msg,
                                      redirect=reverse(INDEX_URL))
                for role in roles:
                    field_name = self.get_member_field_name(role.id)
                    self.fields[field_name].initial.append(group.id)

    class Meta:
        name = _("Organization Groups")
        slug = PROJECT_GROUP_MEMBER_SLUG


class UpdateOrganizationGroups(workflows.UpdateMembersStep):
    action_class = UpdateOrganizationGroupsAction
    available_list_title = _("All Groups")
    members_list_title = _("Organization Groups")
    no_available_text = _("No groups found.")
    no_members_text = _("No groups.")

    def contribute(self, data, context):
        if data:
            try:
                roles = api.keystone.role_list(self.workflow.request)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve role list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class CreateOrganization(workflows.Workflow):
    slug = "create_organization"
    name = _("Create Organization")
    finalize_button_name = _("Create Organization")
    success_message = _('Created new organization "%s".')
    failure_message = _('Unable to create organization "%s".')
    success_url = "horizon:idm:organizations:index"
    default_steps = (CreateOrganizationInfo,
                     UpdateOrganizationMembers)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        if PROJECT_GROUP_ENABLED:
            self.default_steps = (CreateOrganizationInfo,
                                  UpdateOrganizationMembers,
                                  UpdateOrganizationGroups)
        super(CreateOrganization, self).__init__(request=request,
                                            context_seed=context_seed,
                                            entry_point=entry_point,
                                            *args,
                                            **kwargs)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown organization')

    def handle(self, request, data):
        # create the organization
        domain_id = data['domain_id']
        try:
            desc = data['description']
            self.object = api.keystone.tenant_create(request,
                                                     name=data['name'],
                                                     description=desc,
                                                     enabled=data['enabled'],
                                                     domain=domain_id)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        organization_id = self.object.id

        # update organization members
        users_to_add = 0
        try:
            available_roles = api.keystone.role_list(request)
            member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
            # count how many users are to be added
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                role_list = data[field_name]
                users_to_add += len(role_list)
            # add new users to organization
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                role_list = data[field_name]
                users_added = 0
                for user in role_list:
                    api.keystone.add_tenant_user_role(request,
                                                      project=organization_id,
                                                      user=user,
                                                      role=role.id)
                    users_added += 1
                users_to_add -= users_added
        except Exception:
            if PROJECT_GROUP_ENABLED:
                group_msg = _(", add organization groups")
            else:
                group_msg = ""
                exceptions.handle(request, _('Failed to add %(users_to_add)s '
                                         'organization members%(group_msg)s and '
                                         'set organization quotas.')
                                      % {'users_to_add': users_to_add,
                                         'group_msg': group_msg})

        if PROJECT_GROUP_ENABLED:
            # update organization groups
            groups_to_add = 0
            try:
                available_roles = api.keystone.role_list(request)
                member_step = self.get_step(PROJECT_GROUP_MEMBER_SLUG)

                # count how many groups are to be added
                for role in available_roles:
                    field_name = member_step.get_member_field_name(role.id)
                    role_list = data[field_name]
                    groups_to_add += len(role_list)
                # add new groups to organization
                for role in available_roles:
                    field_name = member_step.get_member_field_name(role.id)
                    role_list = data[field_name]
                    groups_added = 0
                    for group in role_list:
                        api.keystone.add_group_role(request,
                                                    role=role.id,
                                                    group=group,
                                                    organization=organization_id)
                        groups_added += 1
                    groups_to_add -= groups_added
            except Exception:
                exceptions.handle(request,
                                  _('Failed to add %s organization groups '
                                    'and update organization quotas.')
                                  % groups_to_add)
        return True



class UpdateOrganizationInfoAction(CreateOrganizationInfoAction):
    enabled = forms.BooleanField(required=False, label=_("Enabled"))

    class Meta:
        name = _("Organization Information")
        slug = 'update_info'
        help_text = _("Edit the organization details.")


class UpdateOrganizationInfo(workflows.Step):
    action_class = UpdateOrganizationInfoAction
    depends_on = ("organization_id",)
    contributes = ("domain_id",
                   "domain_name",
                   "name",
                   "description",
                   "enabled")


class UpdateOrganization(workflows.Workflow):
    slug = "update_organization"
    name = _("Edit Organization")
    finalize_button_name = _("Save")
    success_message = _('Modified organization "%s".')
    failure_message = _('Unable to modify organization "%s".')
    success_url = "horizon:idm:organizations:index"
    default_steps = (UpdateOrganizationInfo,
                     UpdateOrganizationMembers)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        if PROJECT_GROUP_ENABLED:
            self.default_steps = (UpdateOrganizationInfo,
                                  UpdateOrganizationMembers,
                                  UpdateOrganizationGroups)

        super(UpdateOrganization, self).__init__(request=request,
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

        organization_id = data['organization_id']
        domain_id = ''
        # update organization info
        try:
            organization = api.keystone.tenant_update(
                request,
                organization_id,
                name=data['name'],
                description=data['description'],
                enabled=data['enabled'])
            # Use the domain_id from the organization if available
            domain_id = getattr(organization, "domain_id", None)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        # update organization members
        users_to_modify = 0
        # Organization-user member step
        member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
        try:
            # Get our role options
            available_roles = api.keystone.role_list(request)
            # Get the users currently associated with this organization so we
            # can diff against it.
            organization_members = api.keystone.user_list(request,
                                                     project=organization_id)
            users_to_modify = len(organization_members)

            for user in organization_members:
                # Check if there have been any changes in the roles of
                # Existing organization members.
                current_roles = api.keystone.roles_for_user(self.request,
                                                            user.id,
                                                            organization_id)
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
                                project=organization_id,
                                user=user.id,
                                role=role.id)
                        else:
                            # User role is unchanged, so remove it from the
                            # remaining roles list to avoid removing it later.
                            index = current_role_ids.index(role.id)
                            current_role_ids.pop(index)

                # Prevent admins from doing stupid things to themselves.
                is_current_user = user.id == request.user.id
                is_current_organization = organization_id == request.user.tenant_id
                admin_roles = [role for role in current_roles
                               if role.name.lower() == 'admin']
                if len(admin_roles):
                    removing_admin = any([role.id in current_role_ids
                                          for role in admin_roles])
                else:
                    removing_admin = False
                if is_current_user and is_current_organization and removing_admin:
                    # Cannot remove "admin" role on current(admin) organization
                    msg = _('You cannot revoke your administrative privileges '
                            'from the organization you are currently logged into. '
                            'Please switch to another organization with '
                            'administrative privileges or remove the '
                            'administrative role manually via the CLI.')
                    messages.warning(request, msg)

                # Otherwise go through and revoke any removed roles.
                else:
                    for id_to_delete in current_role_ids:
                        api.keystone.remove_tenant_user_role(
                            request,
                            project=organization_id,
                            user=user.id,
                            role=id_to_delete)
                users_to_modify -= 1

            # Grant new roles on the organization.
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                # Count how many users may be added for exception handling.
                users_to_modify += len(data[field_name])
            for role in available_roles:
                users_added = 0
                field_name = member_step.get_member_field_name(role.id)
                for user_id in data[field_name]:
                    if not filter(lambda x: user_id == x.id, organization_members):
                        api.keystone.add_tenant_user_role(request,
                                                          project=organization_id,
                                                          user=user_id,
                                                          role=role.id)
                    users_added += 1
                users_to_modify -= users_added
        except Exception:
            if PROJECT_GROUP_ENABLED:
                group_msg = _(", update organization groups")
            else:
                group_msg = ""
            exceptions.handle(request, _('Failed to modify %(users_to_modify)s'
                                         ' organization members%(group_msg)s and '
                                         'update organization quotas.')
                                       % {'users_to_modify': users_to_modify,
                                          'group_msg': group_msg})
            return False

        if PROJECT_GROUP_ENABLED:
            # update organization groups
            groups_to_modify = 0
            member_step = self.get_step(PROJECT_GROUP_MEMBER_SLUG)
            try:
                # Get the groups currently associated with this organization so we
                # can diff against it.
                organization_groups = api.keystone.group_list(request,
                                                         domain=domain_id,
                                                         project=organization_id)
                groups_to_modify = len(organization_groups)
                for group in organization_groups:
                    # Check if there have been any changes in the roles of
                    # Existing organization members.
                    current_roles = api.keystone.roles_for_group(
                        self.request,
                        group=group.id,
                        project=organization_id)
                    current_role_ids = [role.id for role in current_roles]
                    for role in available_roles:
                        # Check if the group is in the list of groups with
                        # this role.
                        field_name = member_step.get_member_field_name(role.id)
                        if group.id in data[field_name]:
                            # Add it if necessary
                            if role.id not in current_role_ids:
                                # group role has changed
                                api.keystone.add_group_role(
                                    request,
                                    role=role.id,
                                    group=group.id,
                                    project=organization_id)
                            else:
                                # Group role is unchanged, so remove it from
                                # the remaining roles list to avoid removing it
                                # later.
                                index = current_role_ids.index(role.id)
                                current_role_ids.pop(index)

                    # Revoke any removed roles.
                    for id_to_delete in current_role_ids:
                        api.keystone.remove_group_role(request,
                                                       role=id_to_delete,
                                                       group=group.id,
                                                       project=organization_id)
                    groups_to_modify -= 1

                # Grant new roles on the organization.
                for role in available_roles:
                    field_name = member_step.get_member_field_name(role.id)
                    # Count how many groups may be added for error handling.
                    groups_to_modify += len(data[field_name])
                for role in available_roles:
                    groups_added = 0
                    field_name = member_step.get_member_field_name(role.id)
                    for group_id in data[field_name]:
                        if not filter(lambda x: group_id == x.id,
                                      organization_groups):
                            api.keystone.add_group_role(request,
                                                        role=role.id,
                                                        group=group_id,
                                                        project=organization_id)
                        groups_added += 1
                    groups_to_modify -= groups_added
            except Exception:
                exceptions.handle(request,
                                  _('Failed to modify %s organization '
                                    'members, update organization groups '
                                    'and update organization quotas.')
                                  % groups_to_modify)
                return False
        return True

        