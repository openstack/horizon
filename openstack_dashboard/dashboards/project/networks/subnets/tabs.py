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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets \
    import tables as subnet_tables


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/networks/subnets/_detail_overview.html"

    def get_context_data(self, request):
        subnet = self.tab_group.kwargs['subnet']
        return {'subnet': subnet}


class SubnetsTab(tabs.TableTab):
    name = _("Subnets")
    slug = "subnets_tab"
    table_classes = (subnet_tables.SubnetsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_subnets_data(self):
        try:
            network_id = self.tab_group.kwargs['network_id']
            subnets = api.neutron.subnet_list(self.request,
                                              network_id=network_id)

        except Exception:
            subnets = []
            msg = _('Subnet list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return subnets


class SubnetDetailTabs(tabs.TabGroup):
    slug = "subnet_details"
    tabs = (OverviewTab,)
