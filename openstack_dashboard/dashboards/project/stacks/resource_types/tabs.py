# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import tabs
from openstack_dashboard import policy


class ResourceTypeOverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "resource_type_overview"
    template_name = "project/stacks.resource_types/_details.html"

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:DescribeStacks"),),
            request)

    def get_context_data(self, request):
        return {"r_type": self.tab_group.kwargs['rt'],
                "r_type_attributes": self.tab_group.kwargs['rt_attributes'],
                "r_type_properties": self.tab_group.kwargs['rt_properties']}


class ResourceTypeDetailsTabs(tabs.TabGroup):
    slug = "resource_type_details"
    tabs = (ResourceTypeOverviewTab,)
