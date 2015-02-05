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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api


class CreateRoleLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Role")
    url = "horizon:identity:roles:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("identity", "identity:create_role"),)

    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()


class EditRoleLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:identity:roles:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:update_role"),)

    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()


class DeleteRolesAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Role",
            u"Delete Roles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Role",
            u"Deleted Roles",
            count
        )
    policy_rules = (("identity", "identity:delete_role"),)

    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()

    def delete(self, request, obj_id):
        api.keystone.role_delete(request, obj_id)


class RoleFilterAction(tables.FilterAction):
    def filter(self, table, roles, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [role for role in roles
                if q in role.name.lower()]


class RolesTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Role Name'))
    id = tables.Column('id', verbose_name=_('Role ID'))

    class Meta(object):
        name = "roles"
        verbose_name = _("Roles")
        row_actions = (EditRoleLink, DeleteRolesAction)
        table_actions = (RoleFilterAction, CreateRoleLink, DeleteRolesAction)
