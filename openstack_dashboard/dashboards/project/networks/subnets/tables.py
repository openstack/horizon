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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


LOG = logging.getLogger(__name__)


class CheckNetworkEditable(object):
    """Mixin class to determine the specified network is editable."""

    def allowed(self, request, datum=None):
        # Only administrator is allowed to create and manage subnets
        # on shared networks.
        network = self.table._get_network()
        if network.shared:
            return False
        return True


class SubnetPolicyTargetMixin(policy.PolicyTargetMixin):

    def get_policy_target(self, request, datum=None):
        policy_target = super(SubnetPolicyTargetMixin, self)\
            .get_policy_target(request, datum)
        network = self.table._get_network()
        policy_target["network:project_id"] = network.tenant_id
        return policy_target


class DeleteSubnet(SubnetPolicyTargetMixin, CheckNetworkEditable,
                   tables.DeleteAction):
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

    def delete(self, request, obj_id):
        try:
            api.neutron.subnet_delete(request, obj_id)
        except Exception:
            msg = _('Failed to delete subnet %s') % obj_id
            LOG.info(msg)
            network_id = self.table.kwargs['network_id']
            redirect = reverse('horizon:project:networks:detail',
                               args=[network_id])
            exceptions.handle(request, msg, redirect=redirect)


class CreateSubnet(SubnetPolicyTargetMixin, CheckNetworkEditable,
                   tables.LinkAction):
    name = "create"
    verbose_name = _("Create Subnet")
    url = "horizon:project:networks:addsubnet"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_subnet"),)

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request)
        if usages['subnets']['available'] <= 0:
            if 'disabled' not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = _('Create Subnet (Quota exceeded)')
        else:
            self.verbose_name = _('Create Subnet')
            self.classes = [c for c in self.classes if c != 'disabled']

        return True


class UpdateSubnet(SubnetPolicyTargetMixin, CheckNetworkEditable,
                   tables.LinkAction):
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
    name = tables.Column("name_or_id", verbose_name=_("Name"),
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
            msg = _('Unable to retrieve details for network "%s".') \
                % (network_id)
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        return network

    class Meta(object):
        name = "subnets"
        verbose_name = _("Subnets")
        table_actions = (CreateSubnet, DeleteSubnet)
        row_actions = (UpdateSubnet, DeleteSubnet)
        hidden_title = False
