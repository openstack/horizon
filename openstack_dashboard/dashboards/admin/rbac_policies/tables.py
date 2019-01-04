# Copyright 2019 vmware, Inc.
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
from openstack_dashboard import policy


class CreateRBACPolicy(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Create RBAC Policy")
    url = "horizon:admin:rbac_policies:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_rbac_policy"),)


class DeleteRBACPolicy(policy.PolicyTargetMixin, tables.DeleteAction):
    help_text = _("Deleted RBAC policy is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete RBAC Policy",
            u"Delete RBAC Policies",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted RBAC Policy",
            u"Deleted RBAC Policies",
            count
        )

    policy_rules = (("network", "delete_rbac_policy"),)

    def delete(self, request, obj_id):
        api.neutron.rbac_policy_delete(request, obj_id)


class UpdateRBACPolicy(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Policy")
    url = "horizon:admin:rbac_policies:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_rbac_policy"),)


class RBACPoliciesTable(tables.DataTable):
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    id = tables.WrappingColumn('id',
                               verbose_name=_('ID'),
                               link="horizon:admin:rbac_policies:detail")
    object_type = tables.WrappingColumn('object_type',
                                        verbose_name=_('Object Type'))
    object_name = tables.Column("object_name", verbose_name=_("Object"))
    target_tenant = tables.Column("target_tenant_name",
                                  verbose_name=_("Target Project"))

    class Meta(object):
        name = "rbac policies"
        verbose_name = _("RBAC Policies")
        table_actions = (CreateRBACPolicy, DeleteRBACPolicy,)
        row_actions = (UpdateRBACPolicy, DeleteRBACPolicy)
