# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers.extensions.routerrules\
    import tabs as rr_tabs
from openstack_dashboard.dashboards.project.routers.ports import tables as ptbl


class InterfacesTab(tabs.TableTab):
    table_classes = (ptbl.PortsTable,)
    name = _("Interfaces")
    slug = "interfaces"
    template_name = "horizon/common/_detail_table.html"

    def get_interfaces_data(self):
        ports = self.tab_group.ports
        for p in ports:
            p.set_id_as_name_if_empty()
        return ports


class RouterDetailTabs(tabs.TabGroup):
    slug = "router_details"
    tabs = (InterfacesTab, rr_tabs.RulesGridTab, rr_tabs.RouterRulesTab)
    sticky = True

    def __init__(self, request, **kwargs):
        rid = kwargs['router_id']
        self.router = {}
        if 'router' in kwargs:
            self.router = kwargs['router']
        else:
            self.router = api.neutron.router_get(request, rid)
        try:
            self.ports = api.neutron.port_list(request, device_id=rid)
        except Exception:
            self.ports = []
            msg = _('Unable to retrieve router details.')
            exceptions.handle(request, msg)
        super(RouterDetailTabs, self).__init__(request, **kwargs)
