# Copyright 2012 NEC Corporation
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

from neutronclient.common import exceptions as neutron_exceptions

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from horizon.tables import actions
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


LOG = logging.getLogger(__name__)


class SubnetPolicyTargetMixin(policy.PolicyTargetMixin):

    def get_policy_target(self, request, datum=None):
        policy_target = super(SubnetPolicyTargetMixin, self)\
            .get_policy_target(request, datum)
        # Use the network information if it is passed in with datum.
        if datum and "tenant_id" in datum:
            network = datum
        else:
            # This is called by the table actions of the subnets table on the
            # network details panel and some information is not available.
            # 1. Network information is not passed in so need to make a neutron
            #    API call to get it.
            # 2. tenant_id and project_id are missing from policy_target.
            network = self.table._get_network()
            policy_target["tenant_id"] = network.tenant_id
            policy_target["project_id"] = network.tenant_id
        # neutron switched policy target values, we'll support both
        policy_target["network:tenant_id"] = network.tenant_id
        policy_target["network:project_id"] = network.tenant_id
        return policy_target


class DeleteSubnet(SubnetPolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Subnet",
            u"Delete Subnets",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Subnet",
            u"Deleted Subnets",
            count
        )

    policy_rules = (("network", "delete_subnet"),)

    @actions.handle_exception_with_detail_message(
        # normal_log_message
        'Failed to delete subnet %(id)s: %(exc)s',
        # target_exception
        neutron_exceptions.Conflict,
        # target_log_message
        'Unable to delete subnet %(id)s with 409 Conflict: %(exc)s',
        # target_user_message
        _('Unable to delete subnet %(name)s. Most possible reason is because '
          'one or more ports have an IP allocation from this subnet.'),
        # logger_name
        __name__)
    def delete(self, request, obj_id):
        api.neutron.subnet_delete(request, obj_id)


class CreateSubnet(SubnetPolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Create Subnet")
    url = "horizon:project:networks:createsubnet"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_subnet"),)

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request, targets=('subnet', ))

        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages["subnet'] is empty
        if usages.get('subnet', {}).get('available', 1) <= 0:
            if 'disabled' not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = _('Create Subnet (Quota exceeded)')
        else:
            self.verbose_name = _('Create Subnet')
            self.classes = [c for c in self.classes if c != 'disabled']

        return True


class UpdateSubnet(SubnetPolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Subnet")
    url = "horizon:project:networks:editsubnet"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_subnet"),)

    def get_link_url(self, subnet):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id, subnet.id))


class SubnetsTable(tables.DataTable):
    name = tables.WrappingColumn(
        "name_or_id",
        verbose_name=_("Name"),
        link='horizon:project:networks:subnets:detail')
    cidr = tables.Column("cidr", verbose_name=_("Network Address"))
    ip_version = tables.Column("ipver_str", verbose_name=_("IP Version"))
    gateway_ip = tables.Column("gateway_ip", verbose_name=_("Gateway IP"))
    failure_url = reverse_lazy('horizon:project:networks:index')

    @memoized.memoized_method
    def _get_network(self):
        try:
            network_id = self.kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
            network.set_id_as_name_if_empty(length=0)
        except Exception:
            network = None
            msg = _('Unable to retrieve details for network "%s".') \
                % (network_id)
            exceptions.handle(self.request, msg,)
        return network

    def get_object_display(self, subnet):
        return subnet.name_or_id

    class Meta(object):
        name = "subnets"
        verbose_name = _("Subnets")
        table_actions = (CreateSubnet, DeleteSubnet, tables.FilterAction,)
        row_actions = (UpdateSubnet, DeleteSubnet)
        hidden_title = False
