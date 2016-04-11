# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import functions as utils

from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.admin.hypervisors.compute \
    import tabs as cmp_tabs
from openstack_dashboard.dashboards.admin.hypervisors import tables


class HypervisorTab(tabs.TableTab):
    table_classes = (tables.AdminHypervisorsTable,)
    name = _("Hypervisor")
    slug = "hypervisor"
    template_name = "horizon/common/_detail_table.html"

    def get_hypervisors_data(self):
        hypervisors = []
        try:
            hypervisors = nova.hypervisor_list(self.request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor information.'))

        return hypervisors


class HypervisorHostTabs(tabs.TabGroup):
    slug = "hypervisor_info"
    tabs = (HypervisorTab, cmp_tabs.ComputeHostTab)
    sticky = True
