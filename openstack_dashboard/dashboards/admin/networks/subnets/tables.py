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

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets \
    import tables as proj_tables
from openstack_dashboard.dashboards.project.networks.subnets.tabs \
    import SubnetsTab as project_tabs_subnets_tab
from openstack_dashboard.usage import quotas

LOG = logging.getLogger(__name__)


class CreateSubnet(proj_tables.SubnetPolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Create Subnet")
    url = "horizon:admin:networks:createsubnet"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_subnet"),)

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))

    def allowed(self, request, datum=None):
        network = self.table._get_network()
        usages = quotas.tenant_quota_usages(
            request, tenant_id=network.tenant_id, targets=('subnet', ))

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


class UpdateSubnet(proj_tables.SubnetPolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Subnet")
    url = "horizon:admin:networks:editsubnet"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_subnet"),)

    def get_link_url(self, subnet):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id, subnet.id))


def subnet_ip_availability(availability):
    subnet_availability = availability.get("free_ips")
    if subnet_availability:
        if subnet_availability > 10000:
            return ">10000"
        else:
            return str(subnet_availability)
    else:
        return str("Not Available")


class SubnetsTable(tables.DataTable):
    name = tables.WrappingColumn("name_or_id", verbose_name=_("Name"),
                                 link='horizon:admin:networks:subnets:detail')
    cidr = tables.Column("cidr", verbose_name=_("CIDR"))
    ip_version = tables.Column("ipver_str", verbose_name=_("IP Version"))
    gateway_ip = tables.Column("gateway_ip", verbose_name=_("Gateway IP"))
    subnet_used_ips = tables.Column("used_ips",
                                    verbose_name=_("Used IPs"))
    subnet_free_ips = tables.Column(subnet_ip_availability,
                                    verbose_name=_("Free IPs"))
    failure_url = reverse_lazy('horizon:admin:networks:index')

    def get_object_display(self, subnet):
        return subnet.name_or_id

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
        table_actions = (CreateSubnet, proj_tables.DeleteSubnet,
                         tables.FilterAction,)
        row_actions = (UpdateSubnet, proj_tables.DeleteSubnet,)
        hidden_title = False

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(SubnetsTable, self).__init__(
            request, data=data,
            needs_form_wrapper=needs_form_wrapper,
            **kwargs)
        if not api.neutron.is_extension_supported(request,
                                                  'network-ip-availability'):
            del self.columns['subnet_used_ips']
            del self.columns['subnet_free_ips']


class SubnetsTab(project_tabs_subnets_tab):
    table_classes = (SubnetsTable,)

    def _get_subnet_availability(self, network_id):
        subnet_availabilities_list = []
        try:
            availability = api.neutron.\
                show_network_ip_availability(self.request, network_id)
            availabilities = availability.get("network_ip_availability",
                                              {})
            subnet_availabilities_list = availabilities.\
                get("subnet_ip_availability", [])
        except Exception:
            msg = _("Unable to retrieve IP availability.")
            exceptions.handle(self.request, msg)
        return subnet_availabilities_list

    def _add_subnet_availability(self, subnet_usage_list, subnets_dict):
        try:
            for subnet_usage in subnet_usage_list:
                subnet_id = subnet_usage.get("subnet_id")
                subnet_used_ips = subnet_usage.get("used_ips")
                subnet_total_ips = subnet_usage.get("total_ips")
                subnet_free_ips = subnet_total_ips - subnet_used_ips
                if subnet_free_ips < 0:
                    subnet_free_ips = 0
                for item in subnets_dict:
                    id = item.get("id")
                    if id == subnet_id:
                        item._apidict.update({"used_ips": subnet_used_ips})
                        item._apidict.update({"free_ips": subnet_free_ips})
        except Exception:
            msg = _("Unable to update subnets with availability.")
            exceptions.handle(self.request, msg)
        return subnets_dict

    def get_subnets_data(self):
        try:
            subnets = super(SubnetsTab, self).get_subnets_data()
            network_id = self.tab_group.kwargs['network_id']

            if api.neutron.is_extension_supported(self.request,
                                                  'network-ip-availability'):
                subnets_list = self._get_subnet_availability(network_id)
                subnets = self._add_subnet_availability(subnets_list, subnets)
        except Exception:
            subnets = []
            msg = _('Failed to check if network-ip-availability '
                    'extension is supported.')
            exceptions.handle(self.request, msg)
        return subnets
