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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets import utils


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/networks/subnets/_detail_overview.html"

    def get_context_data(self, request):
        subnet_id = self.tab_group.kwargs['subnet_id']
        try:
            subnet = api.neutron.subnet_get(self.request, subnet_id)
        except Exception:
            redirect = reverse('horizon:project:networks:index')
            msg = _('Unable to retrieve subnet details.')
            exceptions.handle(request, msg, redirect=redirect)
        if subnet.ip_version == 6:
            ipv6_modes = utils.get_ipv6_modes_menu_from_attrs(
                subnet.ipv6_ra_mode, subnet.ipv6_address_mode)
            subnet.ipv6_modes_desc = utils.IPV6_MODE_MAP.get(ipv6_modes)
        return {'subnet': subnet}


class SubnetDetailTabs(tabs.TabGroup):
    slug = "subnet_details"
    tabs = (OverviewTab,)
