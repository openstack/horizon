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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import forms
from horizon import tables

from openstack_dashboard import api

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
    
    class Meta:
        name = "purchased_table"
        verbose_name = _("Purchased Applications")
        pagination_param = "tenant_marker"
        table_actions = (CreateApplication, )
        multi_select = False
 

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


class RolesTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Role Name'))
    id = tables.Column('id', verbose_name=_('Role ID'))

    class Meta:
        name = "roles"
        verbose_name = _("Roles")
        row_actions = ()
        table_actions = (EditRoleLink, CreateRoleLink, DeleteRolesAction)

