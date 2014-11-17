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

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from keystoneclient.exceptions import Conflict  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import tables as idm_tables

class CreateApplication(tables.LinkAction):
    name = "create_application"
    verbose_name = _("Add application")
    url = "horizon:idm:myApplication"

    def get_link_url(self):
        base_url = '/idm/myApplication/create'
        return base_url


class ProvidingApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(),
                                    required=False))
    clickable = True
    class Meta:
        name = "providing_table"
        verbose_name = _("Providing Applications")
        pagination_param = "tenant_marker"
        table_actions = (CreateApplication, )
        multi_select = False


class PurchasedApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(),
                                    required=False))
    clickable = True
    class Meta:
        name = "purchased_table"
        verbose_name = _("Purchased Applications")
        pagination_param = "tenant_marker"
        table_actions = (CreateApplication, )
        multi_select = False

# class CreateRoleLink(tables.LinkAction):
#     name = "new_role"
#     verbose_name = _("New role")
#     url = "horizon:idm:myApplications:roles_create"
#     classes = ("ajax-modal",)
#     icon = "plus"
#     #policy_rules = (("identity", "identity:create_role"),)

#     def allowed(self, request, role):
#         # TODO(garcianavalon) implement roles/policies for this
#         return True

# class CreateRoleAction(idm_tables.InlineCreateAction):
#     name = "new_role"
#     verbose_name = _("New role")
#     url = "horizon:idm:myApplications:roles_create"
#     icon = "plus"
#     classes = ("ajax-inline-create",)

#     def create(self, request, obj_data):
#         import pdb; pdb.set_trace()
#         name = obj_data['name']
#         fiware_api.keystone.role_create(request, name)

# class EditRoleLink(tables.LinkAction):
#     name = "edit"
#     verbose_name = _("Edit")
#     url = "horizon:identity:roles:update"
#     classes = ("ajax-modal",)
#     icon = "pencil"
#     policy_rules = (("identity", "identity:update_role"),)

#     def allowed(self, request, role):
#         return api.keystone.keystone_can_edit_role()


class DeleteRolesAction(tables.DeleteAction):

    icon = "cross"

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
    #policy_rules = (("identity", "identity:delete_role"),)

    def allowed(self, request, role):
        #return api.keystone.keystone_can_edit_role()
        # TODO(garcianavalon) implement roles/policies for this
        return True

    def delete(self, request, obj_id):
        fiware_api.keystone.role_delete(request, obj_id)

class UpdateRoleRow(tables.Row):
    ajax = True

    def get_data(self, request, role_id):
        role_info = fiware_api.keystone.role_get(request, role_id)
        return role_info

class UpdateRoleCell(tables.UpdateAction):

    def allowed(self, request, role, cell):
        # return api.keystone.keystone_can_edit_role() and \
        #     policy.check((("identity", "identity:update_role"),),
        #                  request)
        # TODO(garcianavalon) implement roles/policies for this
        return True

    def update_cell(self, request, datum, role_id,
                    cell_name, new_cell_value):
        # inline update role info
        try:
            role_obj = datum
            # updating changed value by new value
            setattr(role_obj, cell_name, new_cell_value)
            fiware_api.keystone.role_update(
                request,
                role_id,
                name=role_obj.name)
            # TODO(garcianavalon) application relation, permissions
        except Conflict:
            # Returning a nice error message about name conflict. The message
            # from exception is not that clear for the users.
            message = _("A role with this name already exists")
            raise ValidationError(message)
        except Exception:
            exceptions.handle(request, _('Error updating role'))
            return False
        return True

class RolesTable(tables.DataTable):
    name = tables.Column('name', 
                        form_field=forms.CharField(max_length=64),
                        update_action=UpdateRoleCell)
    id = tables.Column('id', verbose_name=_('Role ID'))

    class Meta:
        name = "roles"
        verbose_name = _("Roles")
        row_class = UpdateRoleRow
        row_actions = (DeleteRolesAction,)
        table_actions = ()

class PermissionsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Permission Name'))
    id = tables.Column('id', verbose_name=_('Permission ID'))

    class Meta:
        name = "permissions"
        verbose_name = _("Permissions")
        row_actions = ()
        table_actions = ()

