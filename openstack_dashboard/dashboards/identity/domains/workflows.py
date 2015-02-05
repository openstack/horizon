# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.identity.domains import constants

LOG = logging.getLogger(__name__)


class CreateDomainInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    class Meta(object):
        name = _("Domain Information")
        slug = "create_domain"
        help_text = _("Domains provide separation between users and "
                      "infrastructure used by different organizations.")


class CreateDomainInfo(workflows.Step):
    action_class = CreateDomainInfoAction
    contributes = ("domain_id",
                   "name",
                   "description",
                   "enabled")


class UpdateDomainUsersAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateDomainUsersAction, self).__init__(request,
                                                      *args,
                                                      **kwargs)
        domain_id = self.initial.get("domain_id", '')

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a domain
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = (_('Could not find default role "%s" in Keystone') %
                       default)
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to find default role.'),
                              redirect=reverse(constants.DOMAINS_INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request,
                                               domain=domain_id)
        except Exception:
            exceptions.handle(request, _('Unable to retrieve user list.'))
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve role list.'),
                              redirect=reverse(constants.DOMAINS_INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = users_list
            self.fields[field_name].initial = []

        # Figure out users & roles
        if domain_id:
            try:
                users_roles = api.keystone.get_domain_users_roles(request,
                                                                  domain_id)
            except Exception:
                exceptions.handle(request,
                                  _('Unable to retrieve user domain role '
                                    'assignments.'),
                                  redirect=reverse(
                                      constants.DOMAINS_INDEX_URL))

            for user_id in users_roles:
                roles_ids = users_roles[user_id]
                for role_id in roles_ids:
                    field_name = self.get_member_field_name(role_id)
                    self.fields[field_name].initial.append(user_id)

    class Meta(object):
        name = _("Domain Members")
        slug = constants.DOMAIN_USER_MEMBER_SLUG


class UpdateDomainUsers(workflows.UpdateMembersStep):
    action_class = UpdateDomainUsersAction
    available_list_title = _("All Users")
    members_list_title = _("Domain Members")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")

    def contribute(self, data, context):
        context = super(UpdateDomainUsers, self).contribute(data, context)
        if data:
            try:
                roles = api.keystone.role_list(self.workflow.request)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve role list.'),
                                  redirect=reverse(
                                      constants.DOMAINS_INDEX_URL))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class UpdateDomainGroupsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateDomainGroupsAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        err_msg = _('Unable to retrieve group list. Please try again later.')
        domain_id = self.initial.get("domain_id", '')

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a domain
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = (_('Could not find default role "%s" in Keystone') %
                       default)
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(constants.DOMAINS_INDEX_URL))
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
                              redirect=reverse(constants.DOMAINS_INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = groups_list
            self.fields[field_name].initial = []

        # Figure out groups & roles
        if domain_id:
            for group in all_groups:
                try:
                    roles = api.keystone.roles_for_group(self.request,
                                                         group=group.id,
                                                         domain=domain_id)
                except Exception:
                    exceptions.handle(request,
                                      err_msg,
                                      redirect=reverse(
                                          constants.DOMAINS_INDEX_URL))
                for role in roles:
                    field_name = self.get_member_field_name(role.id)
                    self.fields[field_name].initial.append(group.id)

    class Meta(object):
        name = _("Domain Groups")
        slug = constants.DOMAIN_GROUP_MEMBER_SLUG


class UpdateDomainGroups(workflows.UpdateMembersStep):
    action_class = UpdateDomainGroupsAction
    available_list_title = _("All Groups")
    members_list_title = _("Domain Groups")
    no_available_text = _("No groups found.")
    no_members_text = _("No groups.")

    def contribute(self, data, context):
        context = super(UpdateDomainGroups, self).contribute(data, context)
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


class CreateDomain(workflows.Workflow):
    slug = "create_domain"
    name = _("Create Domain")
    finalize_button_name = _("Create Domain")
    success_message = _('Created new domain "%s".')
    failure_message = _('Unable to create domain "%s".')
    success_url = constants.DOMAINS_INDEX_URL
    default_steps = (CreateDomainInfo, )

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown domain')

    def handle(self, request, data):
        # create the domain
        try:
            LOG.info('Creating domain with name "%s"' % data['name'])
            desc = data['description']
            api.keystone.domain_create(request,
                                       name=data['name'],
                                       description=desc,
                                       enabled=data['enabled'])
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True


class UpdateDomainInfoAction(CreateDomainInfoAction):

    class Meta(object):
        name = _("Domain Information")
        slug = 'update_domain'
        help_text = _("Domains provide separation between users and "
                      "infrastructure used by different organizations. "
                      "Edit the domain details to add or remove "
                      "groups in the domain.")


class UpdateDomainInfo(workflows.Step):
    action_class = UpdateDomainInfoAction
    depends_on = ("domain_id",)
    contributes = ("name",
                   "description",
                   "enabled")


class UpdateDomain(workflows.Workflow):
    slug = "update_domain"
    name = _("Edit Domain")
    finalize_button_name = _("Save")
    success_message = _('Modified domain "%s".')
    failure_message = _('Unable to modify domain "%s".')
    success_url = constants.DOMAINS_INDEX_URL
    default_steps = (UpdateDomainInfo,
                     UpdateDomainUsers,
                     UpdateDomainGroups)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown domain')

    def _update_domain_members(self, request, domain_id, data):
        # update domain members
        users_to_modify = 0
        # Project-user member step
        member_step = self.get_step(constants.DOMAIN_USER_MEMBER_SLUG)
        try:
            # Get our role options
            available_roles = api.keystone.role_list(request)
            # Get the users currently associated with this project so we
            # can diff against it.
            domain_members = api.keystone.user_list(request,
                                                    domain=domain_id)
            users_to_modify = len(domain_members)

            for user in domain_members:
                # Check if there have been any changes in the roles of
                # Existing project members.
                current_roles = api.keystone.roles_for_user(self.request,
                                                            user.id,
                                                            domain=domain_id)
                current_role_ids = [role.id for role in current_roles]

                for role in available_roles:
                    field_name = member_step.get_member_field_name(role.id)
                    # Check if the user is in the list of users with this role.
                    if user.id in data[field_name]:
                        # Add it if necessary
                        if role.id not in current_role_ids:
                            # user role has changed
                            api.keystone.add_domain_user_role(
                                request,
                                domain=domain_id,
                                user=user.id,
                                role=role.id)
                        else:
                            # User role is unchanged, so remove it from the
                            # remaining roles list to avoid removing it later.
                            index = current_role_ids.index(role.id)
                            current_role_ids.pop(index)

                # Prevent admins from doing stupid things to themselves.
                is_current_user = user.id == request.user.id
                # TODO(lcheng) When Horizon moves to Domain scoped token for
                # invoking identity operation, replace this with:
                # domain_id == request.user.domain_id
                is_current_domain = True

                admin_roles = [role for role in current_roles
                               if role.name.lower() == 'admin']
                if len(admin_roles):
                    removing_admin = any([role.id in current_role_ids
                                          for role in admin_roles])
                else:
                    removing_admin = False
                if is_current_user and is_current_domain and removing_admin:
                    # Cannot remove "admin" role on current(admin) domain
                    msg = _('You cannot revoke your administrative privileges '
                            'from the domain you are currently logged into. '
                            'Please switch to another domain with '
                            'administrative privileges or remove the '
                            'administrative role manually via the CLI.')
                    messages.warning(request, msg)

                # Otherwise go through and revoke any removed roles.
                else:
                    for id_to_delete in current_role_ids:
                        api.keystone.remove_domain_user_role(
                            request,
                            domain=domain_id,
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
                    if not filter(lambda x: user_id == x.id, domain_members):
                        api.keystone.add_tenant_user_role(request,
                                                          project=domain_id,
                                                          user=user_id,
                                                          role=role.id)
                    users_added += 1
                users_to_modify -= users_added
            return True
        except Exception:
            exceptions.handle(request,
                              _('Failed to modify %s project '
                                'members and update domain groups.')
                              % users_to_modify)
            return False

    def _update_domain_groups(self, request, domain_id, data):
        # update domain groups
        groups_to_modify = 0
        member_step = self.get_step(constants.DOMAIN_GROUP_MEMBER_SLUG)
        try:
            # Get our role options
            available_roles = api.keystone.role_list(request)
            # Get the groups currently associated with this domain so we
            # can diff against it.
            domain_groups = api.keystone.group_list(request,
                                                    domain=domain_id)
            groups_to_modify = len(domain_groups)
            for group in domain_groups:
                # Check if there have been any changes in the roles of
                # Existing domain members.
                current_roles = api.keystone.roles_for_group(
                    self.request,
                    group=group.id,
                    domain=domain_id)
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
                                domain=domain_id)
                        else:
                            # Group role is unchanged, so remove it from
                            # the remaining roles list to avoid removing it
                            # later
                            index = current_role_ids.index(role.id)
                            current_role_ids.pop(index)

                # Revoke any removed roles.
                for id_to_delete in current_role_ids:
                    api.keystone.remove_group_role(request,
                                                   role=id_to_delete,
                                                   group=group.id,
                                                   domain=domain_id)
                groups_to_modify -= 1

            # Grant new roles on the domain.
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                # Count how many groups may be added for error handling.
                groups_to_modify += len(data[field_name])
            for role in available_roles:
                groups_added = 0
                field_name = member_step.get_member_field_name(role.id)
                for group_id in data[field_name]:
                    if not filter(lambda x: group_id == x.id, domain_groups):
                        api.keystone.add_group_role(request,
                                                    role=role.id,
                                                    group=group_id,
                                                    domain=domain_id)
                    groups_added += 1
                groups_to_modify -= groups_added
            return True
        except Exception:
            exceptions.handle(request,
                              _('Failed to modify %s domain groups.')
                              % groups_to_modify)
            return False

    def handle(self, request, data):
        domain_id = data.pop('domain_id')

        try:
            LOG.info('Updating domain with name "%s"' % data['name'])
            api.keystone.domain_update(request,
                                       domain_id=domain_id,
                                       name=data['name'],
                                       description=data['description'],
                                       enabled=data['enabled'])
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        if not self._update_domain_members(request, domain_id, data):
            return False

        if not self._update_domain_groups(request, domain_id, data):
            return False

        return True
