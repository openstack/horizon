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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports \
    import forms as project_forms


LOG = logging.getLogger(__name__)
VNIC_TYPES = [('normal', _('Normal')),
              ('direct', _('Direct')),
              ('direct-physical', _('Direct Physical')),
              ('macvtap', _('MacVTap')),
              ('baremetal', _('Bare Metal')),
              ('virtio-forwarder', _('Virtio Forwarder'))]


class CreatePort(project_forms.CreatePort):
    binding__host_id = forms.CharField(
        label=_("Binding: Host"),
        help_text=_("The ID of the host where the port is allocated. In some "
                    "cases, different implementations can run on different "
                    "hosts."),
        required=False)
    failure_url = 'horizon:admin:networks:detail'

    def __init__(self, request, *args, **kwargs):
        super(CreatePort, self).__init__(request, *args, **kwargs)

        try:
            if api.neutron.is_extension_supported(request, 'binding'):
                neutron_settings = getattr(settings,
                                           'OPENSTACK_NEUTRON_NETWORK', {})
                supported_vnic_types = neutron_settings.get(
                    'supported_vnic_types', ['*'])
                if supported_vnic_types:
                    if supported_vnic_types == ['*']:
                        vnic_type_choices = VNIC_TYPES
                    else:
                        vnic_type_choices = [
                            vnic_type for vnic_type in VNIC_TYPES
                            if vnic_type[0] in supported_vnic_types
                        ]

                    self.fields['binding__vnic_type'] = \
                        forms.ThemableChoiceField(
                            choices=vnic_type_choices,
                            label=_("Binding: VNIC Type"),
                            help_text=_(
                                "The VNIC type that is bound to the neutron "
                                "port"),
                            required=False)
        except Exception:
            msg = _("Unable to verify the VNIC types extension in Neutron")
            exceptions.handle(self.request, msg)

        try:
            if api.neutron.is_extension_supported(request, 'mac-learning'):
                self.fields['mac_state'] = forms.BooleanField(
                    label=_("MAC Learning State"), initial=False,
                    required=False)
        except Exception:
            msg = _("Unable to retrieve MAC learning state")
            exceptions.handle(self.request, msg)

        try:
            if api.neutron.is_extension_supported(request, 'port-security'):
                self.fields['port_security_enabled'] = forms.BooleanField(
                    label=_("Port Security"),
                    help_text=_("Enable anti-spoofing rules for the port"),
                    initial=True,
                    required=False)
        except Exception:
            msg = _("Unable to retrieve port security state")
            exceptions.handle(self.request, msg)

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


class UpdatePort(project_forms.UpdatePort):
    # tenant_id = forms.CharField(widget=forms.HiddenInput())
    device_id = forms.CharField(max_length=100, label=_("Device ID"),
                                help_text=_("Device ID attached to the port"),
                                required=False)
    device_owner = forms.CharField(max_length=100, label=_("Device Owner"),
                                   help_text=_("Device owner attached to the "
                                               "port"),
                                   required=False)
    binding__host_id = forms.CharField(
        label=_("Binding: Host"),
        help_text=_("The ID of the host where the port is allocated. In some "
                    "cases, different implementations can run on different "
                    "hosts."),
        required=False)
    mac_address = forms.MACAddressField(
        label=_("MAC Address"),
        required=False,
        help_text=_("Specify a new MAC address for the port"))

    failure_url = 'horizon:admin:networks:detail'

    def handle(self, request, data):
        port_id = self.initial['port_id']
        try:
            LOG.debug('params = %s', data)
            extension_kwargs = {}
            if 'binding__vnic_type' in data:
                extension_kwargs['binding__vnic_type'] = \
                    data['binding__vnic_type']

            if 'mac_state' in data:
                extension_kwargs['mac_learning_enabled'] = data['mac_state']

            if 'port_security_enabled' in data:
                extension_kwargs['port_security_enabled'] = \
                    data['port_security_enabled']

            port = api.neutron.port_update(request,
                                           port_id,
                                           name=data['name'],
                                           admin_state_up=data['admin_state'],
                                           device_id=data['device_id'],
                                           device_owner=data['device_owner'],
                                           binding__host_id=data
                                           ['binding__host_id'],
                                           mac_address=data['mac_address'],
                                           **extension_kwargs)
            msg = _('Port %s was successfully updated.') % port_id
            messages.success(request, msg)
            return port
        except Exception as e:
            LOG.info('Failed to update port %(id)s: %(exc)s',
                     {'id': port_id, 'exc': e})
            msg = _('Failed to update port %s') % port_id
            redirect = reverse(self.failure_url,
                               args=[self.initial['network_id']])
            exceptions.handle(request, msg, redirect=redirect)
