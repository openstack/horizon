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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/routers/_detail_overview.html")
    redirect_url = 'horizon:project:routers:index'

    def get_context_data(self, request):
        router_id = self.tab_group.kwargs['router_id']
        try:
            router = api.quantum.router_get(request, router_id)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve router details.'),
                              redirect=reverse(self.redirect_url))
        return {'router': router}


class RouterDetailTabs(tabs.TabGroup):
    slug = "router_details"
    tabs = (OverviewTab,)
