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

from horizon import tabs


class NetworkProfileTab(tabs.Tab):
    name = _("Network Profile")
    slug = "network_profile"
    template_name = 'router/nexus1000v/network_profile/index.html'

    def get_context_data(self, request):
        return None


class PolicyProfileTab(tabs.Tab):
    name = _("Policy Profile")
    slug = "policy_profile"
    template_name = 'router/nexus1000v/policy_profile/index.html'
    preload = False


class IndexTabs(tabs.TabGroup):
    slug = "indextabs"
    tabs = (NetworkProfileTab, PolicyProfileTab)
