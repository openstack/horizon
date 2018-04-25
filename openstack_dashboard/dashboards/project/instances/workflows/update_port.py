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

from openstack_dashboard.dashboards.project.networks.ports import workflows


class UpdatePortInfo(workflows.UpdatePortInfo):
    depends_on = ('network_id', 'port_id', 'instance_id')


class UpdatePortSecurityGroup(workflows.UpdatePortSecurityGroup):
    depends_on = ("port_id", 'target_tenant_id', 'instance_id')


class UpdatePort(workflows.UpdatePort):
    default_steps = (UpdatePortInfo, UpdatePortSecurityGroup)

    def get_success_url(self):
        return reverse("horizon:project:instances:detail",
                       args=(self.context['instance_id'],))
