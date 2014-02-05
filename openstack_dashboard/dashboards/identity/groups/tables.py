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

from django.core.urlresolvers import reverse
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.dashboards.identity.groups import constants


LOG = logging.getLogger(__name__)
LOGOUT_URL = 'logout'
STATUS_CHOICES = (
    ("true", True),
    ("false", False)
)


class CreateGroupLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Group")
    url = constants.GROUPS_CREATE_URL
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("identity", "identity:create_group"),)

    def allowed(self, request, group):
        return api.keystone.keystone_can_edit_group()


class EditGroupLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Group")
    url = constants.GROUPS_UPDATE_URL
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:update_group"),)

    def allowed(self, request, group):
        return api.keystone.keystone_can_edit_group()


class DeleteGroupsAction(tables.DeleteAction):
    name = "delete"
    data_type_singular = _("Group")
    data_type_plural = _("Groups")
    policy_rules = (("identity", "identity:delete_group"),)

    def allowed(self, request, datum):
        return api.keystone.keystone_can_edit_group()

    def delete(self, request, obj_id):
        LOG.info('Deleting group "%s".' % obj_id)
        api.keystone.group_delete(request, obj_id)


class ManageUsersLink(tables.LinkAction):
    name = "users"
    verbose_name = _("Modify Users")
    url = constants.GROUPS_MANAGE_URL
    icon = "pencil"
    policy_rules = (("identity", "identity:get_group"),
                    ("identity", "identity:list_users"),)

    def allowed(self, request, datum):
        return api.keystone.keystone_can_edit_group()


class GroupFilterAction(tables.FilterAction):
    def filter(self, table, groups, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(group):
            if q in group.name.lower():
                return True
            return False

        return filter(comp, groups)


class GroupsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    id = tables.Column('id', verbose_name=_('Group ID'))

    class Meta:
        name = "groups"
        verbose_name = _("Groups")
        row_actions = (ManageUsersLink, EditGroupLink, DeleteGroupsAction)
        table_actions = (GroupFilterAction, CreateGroupLink,
                         DeleteGroupsAction)


class UserFilterAction(tables.FilterAction):
    def filter(self, table, users, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [user for user in users
                if q in user.name.lower()
                or q in getattr(user, 'email', '').lower()]


class RemoveMembers(tables.DeleteAction):
    name = "removeGroupMember"
    action_present = _("Remove")
    action_past = _("Removed")
    data_type_singular = _("User")
    data_type_plural = _("Users")
    policy_rules = (("identity", "identity:remove_user_from_group"),)

    def allowed(self, request, user=None):
        return api.keystone.keystone_can_edit_group()

    def action(self, request, obj_id):
        user_obj = self.table.get_object_by_id(obj_id)
        group_id = self.table.kwargs['group_id']
        LOG.info('Removing user %s from group %s.' % (user_obj.id,
                                                      group_id))
        api.keystone.remove_group_user(request,
                                       group_id=group_id,
                                       user_id=user_obj.id)
        # TODO(lin-hua-cheng): Fix the bug when removing current user
        # Keystone revokes the token of the user removed from the group.
        # If the logon user was removed, redirect the user to logout.


class AddMembersLink(tables.LinkAction):
    name = "add_user_link"
    verbose_name = _("Add...")
    classes = ("ajax-modal",)
    icon = "plus"
    url = constants.GROUPS_ADD_MEMBER_URL
    policy_rules = (("identity", "identity:list_users"),
                    ("identity", "identity:add_user_to_group"),)

    def allowed(self, request, user=None):
        return api.keystone.keystone_can_edit_group()

    def get_link_url(self, datum=None):
        return reverse(self.url, kwargs=self.table.kwargs)


class UsersTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('User Name'))
    email = tables.Column('email', verbose_name=_('Email'),
                          filters=[defaultfilters.escape,
                                   defaultfilters.urlize])
    id = tables.Column('id', verbose_name=_('User ID'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'),
                            status=True,
                            status_choices=STATUS_CHOICES,
                            empty_value="False")


class GroupMembersTable(UsersTable):
    class Meta:
        name = "group_members"
        verbose_name = _("Group Members")
        table_actions = (UserFilterAction, AddMembersLink, RemoveMembers)


class AddMembers(tables.BatchAction):
    name = "addMember"
    action_present = _("Add")
    action_past = _("Added")
    data_type_singular = _("User")
    data_type_plural = _("Users")
    icon = "plus"
    requires_input = True
    success_url = constants.GROUPS_MANAGE_URL
    policy_rules = (("identity", "identity:add_user_to_group"),)

    def allowed(self, request, user=None):
        return api.keystone.keystone_can_edit_group()

    def action(self, request, obj_id):
        user_obj = self.table.get_object_by_id(obj_id)
        group_id = self.table.kwargs['group_id']
        LOG.info('Adding user %s to group %s.' % (user_obj.id,
                                                  group_id))
        api.keystone.add_group_user(request,
                                    group_id=group_id,
                                    user_id=user_obj.id)
        # TODO(lin-hua-cheng): Fix the bug when adding current user
        # Keystone revokes the token of the user added to the group.
        # If the logon user was added, redirect the user to logout.

    def get_success_url(self, request=None):
        group_id = self.table.kwargs.get('group_id', None)
        return reverse(self.success_url, args=[group_id])


class GroupNonMembersTable(UsersTable):
    class Meta:
        name = "group_non_members"
        verbose_name = _("Non-Members")
        table_actions = (UserFilterAction, AddMembers)
