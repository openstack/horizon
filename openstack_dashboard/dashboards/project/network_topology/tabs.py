#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard.dashboards.project.network_topology import utils


class TopologyBaseTab(tabs.Tab):
    def get_context_data(self, request):
        return utils.get_context(request)


class TopologyTab(TopologyBaseTab):
    name = _("Topology")
    slug = "topology"
    preload = False
    template_name = ("project/network_topology/_topology_view.html")


class GraphTab(TopologyBaseTab):
    name = _("Graph")
    slug = "graph"
    preload = True
    template_name = ("project/network_topology/_graph_view.html")


class TopologyTabs(tabs.TabGroup):
    slug = "topology_tabs"
    tabs = (TopologyTab, GraphTab)
    sticky = True
