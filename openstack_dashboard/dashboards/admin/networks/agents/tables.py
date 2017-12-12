# Copyright 2014 Kylincloud
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

from django.template import defaultfilters as filters
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils import filters as utils_filters

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class DeleteDHCPAgent(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete DHCP Agent",
            u"Delete DHCP Agents",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted DHCP Agent",
            u"Deleted DHCP Agents",
            count
        )

    policy_rules = (("network", "delete_agent"),)

    def delete(self, request, obj_id):
        network_id = self.table.kwargs['network_id']
        api.neutron.remove_network_from_dhcp_agent(request, obj_id, network_id)


class AddDHCPAgent(tables.LinkAction):
    name = "add"
    verbose_name = _("Add DHCP Agent")
    url = "horizon:admin:networks:adddhcpagent"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "update_agent"),)

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))


def get_agent_status(agent):
    if agent.admin_state_up:
        return _('Enabled')
    return _('Disabled')


def get_agent_state(agent):
    if agent.alive:
        return _('Up')
    return _('Down')


class DHCPAgentsFilterAction(tables.FilterAction):
    name = "agents"


class DHCPAgentsTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('ID'), hidden=True)
    host = tables.Column('host', verbose_name=_('Host'))
    status = tables.Column(get_agent_status, verbose_name=_('Status'))
    state = tables.Column(get_agent_state, verbose_name=_('Admin State'))
    heartbeat_timestamp = tables.Column('heartbeat_timestamp',
                                        verbose_name=_('Updated At'),
                                        filters=(utils_filters.parse_isotime,
                                                 filters.timesince))

    def get_object_display(self, agent):
        return agent.host

    class Meta(object):
        name = "agents"
        verbose_name = _("DHCP Agents")
        table_actions = (AddDHCPAgent, DeleteDHCPAgent,
                         DHCPAgentsFilterAction,)
        row_actions = (DeleteDHCPAgent,)
        hidden_title = False
