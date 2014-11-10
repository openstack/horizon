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

from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.admin.hypervisors.compute import tables


class ComputeHostTab(tabs.TableTab):
    table_classes = (tables.ComputeHostTable,)
    name = _("Compute Host")
    slug = "compute_host"
    template_name = "horizon/common/_detail_table.html"

    def get_compute_host_data(self):
        try:
            services = nova.service_list(self.tab_group.request)
            return [service for service in services
                    if service.binary == 'nova-compute']
        except Exception:
            msg = _('Unable to get nova services list.')
            exceptions.handle(self.tab_group.request, msg)
            return []
