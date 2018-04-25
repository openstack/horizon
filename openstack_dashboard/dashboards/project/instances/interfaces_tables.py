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
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.project.networks.ports \
    import tables as port_tables


class UpdatePort(port_tables.UpdatePort):
    url = "horizon:project:instances:update_port"

    def get_link_url(self, port):
        instance_id = self.table.kwargs['instance_id']
        base_url = reverse(self.url, args=(instance_id, port.id))
        params = {'step': 'update_info'}
        param = urlencode(params)
        return '?'.join([base_url, param])


class UpdateSecurityGroups(port_tables.UpdatePort):
    name = 'update_security_groups'
    verbose_name = _('Edit Security Groups')
    url = "horizon:project:instances:update_port"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_port"),)

    def get_link_url(self, port):
        instance_id = self.table.kwargs['instance_id']
        base_url = reverse(self.url, args=(instance_id, port.id))
        params = {'step': 'update_security_groups'}
        param = urlencode(params)
        return '?'.join([base_url, param])

    def allowed(self, request, datum=None):
        return datum and datum.port_security_enabled


class InterfacesTable(port_tables.PortsTable):
    network = tables.Column('network', verbose_name=_('Network'))

    class Meta(object):
        name = "interfaces"
        verbose_name = _("Interfaces")
        table_actions = []
        row_actions = [UpdateSecurityGroups, UpdatePort]
        columns = ('name', 'network', 'fixed_ips', 'mac_address',
                   'status', 'admin_state', 'mac_state')
