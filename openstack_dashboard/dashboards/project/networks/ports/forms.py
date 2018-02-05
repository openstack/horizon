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

from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)
VNIC_TYPES = [('normal', _('Normal')),
              ('direct', _('Direct')),
              ('direct-physical', _('Direct Physical')),
              ('macvtap', _('MacVTap')),
              ('baremetal', _('Bare Metal')),
              ('virtio-forwarder', _('Virtio Forwarder'))]


class CreatePort(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    admin_state = forms.BooleanField(label=_("Enable Admin State"),
                                     initial=True,
                                     required=False)
    device_id = forms.CharField(max_length=100, label=_("Device ID"),
                                help_text=_("Device ID attached to the port"),
                                required=False)
    device_owner = forms.CharField(
        max_length=100, label=_("Device Owner"),
        help_text=_("Owner of the device attached to the port"),
        required=False)
    specify_ip = forms.ThemableChoiceField(
        label=_("Specify IP address or subnet"),
        help_text=_("To specify a subnet or a fixed IP, select any options."),
        required=False,
        choices=[('', _("Unspecified")),
                 ('subnet_id', _("Subnet")),
                 ('fixed_ip', _("Fixed IP Address"))],
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switchable',
            'data-slug': 'specify_ip',
        }))
    subnet_id = forms.ThemableChoiceField(
        label=_("Subnet"),
        required=False,
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'specify_ip',
            'data-specify_ip-subnet_id': _('Subnet'),
        }))
    fixed_ip = forms.IPField(
        label=_("Fixed IP Address"),
        required=False,
        help_text=_("Specify the subnet IP address for the new port"),
        version=forms.IPv4 | forms.IPv6,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'specify_ip',
            'data-specify_ip-fixed_ip': _('Fixed IP Address'),
        }))
    mac_address = forms.MACAddressField(
        label=_("MAC Address"),
        required=False,
        help_text=_("Specify the MAC address for the new port"))
    failure_url = 'horizon:project:networks:detail'

    def __init__(self, request, *args, **kwargs):
        super(CreatePort, self).__init__(request, *args, **kwargs)

        # prepare subnet choices and input area for each subnet
        subnet_choices = self._get_subnet_choices(kwargs['initial'])
        if subnet_choices:
            subnet_choices.insert(0, ('', _("Select a subnet")))
            self.fields['subnet_id'].choices = subnet_choices
        else:
            self.fields['specify_ip'].widget = forms.HiddenInput()
            self.fields['subnet_id'].widget = forms.HiddenInput()
            self.fields['fixed_ip'].widget = forms.HiddenInput()

        if api.neutron.is_extension_supported(request, 'mac-learning'):
            self.fields['mac_state'] = forms.BooleanField(
                label=_("MAC Learning State"), initial=False, required=False)

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

    def _get_subnet_choices(self, kwargs):
        try:
            network_id = kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
        except Exception:
            return []

        # NOTE(amotoki): When a user cannot retrieve a subnet info,
        # subnet ID is stored in network.subnets field.
        # If so, we skip such subnet as subnet choices.
        # This happens usually for external networks.
        # TODO(amotoki): Ideally it is better to disable/hide
        # Create Port button in the port table, but as of Pike
        # the default neutron policy.json for "create_port" is empty
        # and there seems no appropriate policy. This is a dirty hack.
        return [(subnet.id, '%s %s' % (subnet.name_or_id, subnet.cidr))
                for subnet in network.subnets
                if isinstance(subnet, api.neutron.Subnet)]

    def handle(self, request, data):
        try:
            params = {
                'network_id': self.initial['network_id'],
                'admin_state_up': data['admin_state'],
                'name': data['name'],
                'device_id': data['device_id'],
                'device_owner': data['device_owner']
            }

            if data.get('specify_ip') == 'subnet_id':
                if data.get('subnet_id'):
                    params['fixed_ips'] = [{"subnet_id": data['subnet_id']}]
            elif data.get('specify_ip') == 'fixed_ip':
                if data.get('fixed_ip'):
                    params['fixed_ips'] = [{"ip_address": data['fixed_ip']}]

            if data.get('mac_state'):
                params['mac_learning_enabled'] = data['mac_state']
            if 'port_security_enabled' in data:
                params['port_security_enabled'] = data['port_security_enabled']

            # Send mac_address only when it is specified.
            if data['mac_address']:
                params['mac_address'] = data['mac_address']

            port = api.neutron.port_create(request, **params)
            if port['name']:
                msg = _('Port %s was successfully created.') % port['name']
            else:
                msg = _('Port %s was successfully created.') % port['id']
            messages.success(request, msg)
            return port
        except Exception as e:
            LOG.info('Failed to create a port for network %(id)s: %(exc)s',
                     {'id': self.initial['network_id'], 'exc': e})
            if isinstance(e, neutron_exc.Forbidden):
                msg = (_('You are not allowed to create a port '
                         'for network %s.')
                       % self.initial['network_id'])
            else:
                msg = (_('Failed to create a port for network %s')
                       % self.initial['network_id'])
            redirect = reverse(self.failure_url,
                               args=(self.initial['network_id'],))
            exceptions.handle(request, msg, redirect=redirect)


class UpdatePort(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    admin_state = forms.BooleanField(label=_("Enable Admin State"),
                                     required=False)
    failure_url = 'horizon:project:networks:detail'

    def __init__(self, request, *args, **kwargs):
        super(UpdatePort, self).__init__(request, *args, **kwargs)
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

                    self.fields['binding__vnic_type'] = forms.ChoiceField(
                        choices=vnic_type_choices,
                        label=_("Binding: VNIC Type"),
                        help_text=_(
                            "The VNIC type that is bound to the neutron port"),
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
                    required=False)
        except Exception:
            msg = _("Unable to retrieve port security state")
            exceptions.handle(self.request, msg)

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
