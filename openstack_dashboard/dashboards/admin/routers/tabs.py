# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

from openstack_dashboard.dashboards.admin.routers.extensions.extraroutes\
    import tables as ertbl
from openstack_dashboard.dashboards.admin.routers.ports import tables as ptbl
from openstack_dashboard.dashboards.project.routers.extensions.extraroutes\
    import tabs as er_tabs
from openstack_dashboard.dashboards.project.routers import tabs as r_tabs


class OverviewTab(r_tabs.OverviewTab):
    template_name = "project/routers/_detail_overview.html"


class ExtraRoutesTab(er_tabs.ExtraRoutesTab):
    table_classes = (ertbl.AdminRouterRoutesTable,)


class InterfacesTab(r_tabs.InterfacesTab):
    table_classes = (ptbl.PortsTable,)


class RouterDetailTabs(r_tabs.RouterDetailTabs):
    tabs = (OverviewTab, InterfacesTab, ExtraRoutesTab)
    sticky = True
