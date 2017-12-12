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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/networks/ports/_detail_overview.html"
    failure_url = 'horizon:project:routers:index'

    def get_context_data(self, request):
        port_id = self.tab_group.kwargs['port_id']
        try:
            port = api.neutron.port_get(self.request, port_id)
        except Exception:
            redirect = reverse(self.failure_url)
            msg = _('Unable to retrieve port details.')
            exceptions.handle(request, msg, redirect=redirect)
        return {'port': port}


class PortDetailTabs(tabs.TabGroup):
    slug = "port_details"
    tabs = (OverviewTab,)
