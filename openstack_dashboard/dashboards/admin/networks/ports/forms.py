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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports \
    import forms as project_forms


LOG = logging.getLogger(__name__)


class CreatePort(project_forms.CreatePort):
    binding__host_id = forms.CharField(
        label=_("Binding: Host"),
        help_text=_("The ID of the host where the port is allocated. In some "
                    "cases, different implementations can run on different "
                    "hosts."),
        required=False)
    failure_url = 'horizon:admin:networks:detail'

    def handle(self, request, data):
        network_id = self.initial['network_id']
        try:
            # We must specify tenant_id of the network which a subnet is
            # created for if admin user does not belong to the tenant.
            network = api.neutron.network_get(request, network_id)
            params = {
                'tenant_id': network.tenant_id,
                'network_id': network_id,
                'admin_state_up': data['admin_state'],
                'name': data['name'],
                'device_id': data['device_id'],
                'device_owner': data['device_owner'],
                'binding__host_id': data['binding__host_id']
            }

            if data.get('specify_ip') == 'subnet_id':
                if data.get('subnet_id'):
                    params['fixed_ips'] = [{"subnet_id": data['subnet_id']}]
            elif data.get('specify_ip') == 'fixed_ip':
                if data.get('fixed_ip'):
                    params['fixed_ips'] = [{"ip_address": data['fixed_ip']}]

            if data.get('binding__vnic_type'):
                params['binding__vnic_type'] = data['binding__vnic_type']

            if data.get('mac_state'):
                params['mac_learning_enabled'] = data['mac_state']

            if 'port_security_enabled' in data:
                params['port_security_enabled'] = data['port_security_enabled']

            port = api.neutron.port_create(request, **params)
            msg = _('Port %s was successfully created.') % port['id']
            messages.success(request, msg)
            return port
        except Exception as e:
            LOG.info('Failed to create a port for network %(id)s: %(exc)s',
                     {'id': network_id, 'exc': e})
            msg = _('Failed to create a port for network %s') % network_id
            redirect = reverse(self.failure_url, args=(network_id,))
            exceptions.handle(request, msg, redirect=redirect)
