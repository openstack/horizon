# Copyright 2016 Mirantis Inc.
# All Rights Reserved.
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

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.networks.agents import tables


class DHCPAgentsTab(tabs.TableTab):
    name = _("DHCP Agents")
    slug = "agents_tab"
    table_classes = (tables.DHCPAgentsTable,)
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_agents_data(self):
        agents = []
        if api.neutron.is_extension_supported(self.request,
                                              'dhcp_agent_scheduler'):
            try:
                network_id = self.tab_group.kwargs['network_id']
                agents = api.neutron.list_dhcp_agent_hosting_networks(
                    self.request,
                    network_id)
            except Exception:
                msg = _('Unable to list dhcp agents hosting network.')
                exceptions.handle(self.request, msg)
        return agents
