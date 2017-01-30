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
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports import tabs \
    as ports_tabs
from openstack_dashboard.dashboards.project.networks.subnets import tabs \
    as subnets_tabs
from openstack_dashboard.dashboards.project.networks \
    import tables as project_tables
from openstack_dashboard.utils import filters


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/networks/_detail_overview.html")
    preload = False

    @memoized.memoized_method
    def _get_data(self):
        network = {}
        network_id = None
        try:
            network_id = self.tab_group.kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
            network.set_id_as_name_if_empty(length=0)

            choices = project_tables.STATUS_DISPLAY_CHOICES
            network.status_label = (
                filters.get_display_label(choices, network.status))
            choices = project_tables.DISPLAY_CHOICES
            network.admin_state_label = (
                filters.get_display_label(choices, network.admin_state))
        except Exception:
            msg = _('Unable to retrieve details for network "%s".') \
                % (network_id)
            exceptions.handle(self.request, msg)
        return network

    def get_context_data(self, request, **kwargs):
        context = super(OverviewTab, self).get_context_data(request, **kwargs)
        network = self._get_data()

        context["network"] = network
        return context


class NetworkDetailsTabs(tabs.DetailTabsGroup):
    slug = "network_tabs"
    tabs = (OverviewTab, subnets_tabs.SubnetsTab, ports_tabs.PortsTab, )
    sticky = True
