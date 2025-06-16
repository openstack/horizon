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

from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard.dashboards.project.networks.ports.extensions. \
    allowed_address_pairs import tabs as addr_pairs_tabs
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports \
    import tables as port_tables


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/networks/ports/_detail_overview.html"

    def get_context_data(self, request):
        @memoized.memoized_method
        def get_security_groups(sg_ids):
            # Avoid extra API calls if no security group is associated.
            if not sg_ids:
                return []
            try:
                security_groups = api.neutron.security_group_list(request,
                                                                  id=sg_ids)
            except Exception:
                security_groups = []
                msg = _("Unable to retrieve security groups for the port.")
                exceptions.handle(request, msg)
            return security_groups

        port = self.tab_group.kwargs['port']
        security_groups = get_security_groups(port.security_group_ids)
        return {'port': port, 'security_groups': security_groups}


class PortDetailTabs(tabs.DetailTabsGroup):
    slug = "port_details"
    tabs = (OverviewTab, addr_pairs_tabs.AllowedAddressPairsTab)
    sticky = True


class PortsTab(tabs.TableTab):
    name = _("Ports")
    slug = "ports_tab"
    table_classes = (port_tables.PortsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_ports_data(self):
        try:
            network_id = self.tab_group.kwargs['network_id']
            ports = api.neutron.port_list(self.request, network_id=network_id)
        except Exception:
            ports = []
            msg = _('Port list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return ports
