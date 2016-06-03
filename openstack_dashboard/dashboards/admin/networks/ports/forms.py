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
VNIC_TYPES = [('normal', _('Normal')), ('direct', _('Direct')),
              ('macvtap', _('MacVTap'))]


class CreatePort(forms.SelfHandlingForm):
    network_name = forms.CharField(label=_("Network Name"),
                                   widget=forms.TextInput(
                                       attrs={'readonly': 'readonly'}),
                                   required=False)
    network_id = forms.CharField(label=_("Network ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    admin_state = forms.ThemableChoiceField(choices=[(True, _('UP')),
                                                     (False, _('DOWN'))],
                                            label=_("Admin State"))
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
    specify_ip = forms.ThemableChoiceField(
        label=_("Specify IP address or subnet"),
        help_text=_("To specify a subnet or a fixed IP, select any options."),
        initial=False,
        required=False,
        choices=[('', _("Unspecified")),
                 ('subnet_id', _("Subnet")),
                 ('fixed_ip', _("Fixed IP Address"))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'specify_ip',
        }))
    subnet_id = forms.ThemableChoiceField(
        label=_("Subnet"),
        required=False,
        widget=forms.Select(attrs={
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
    failure_url = 'horizon:admin:networks:detail'

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

    def _get_subnet_choices(self, kwargs):
        try:
            network_id = kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
        except Exception:
            return []

        return [(subnet.id, '%s %s' % (subnet.name_or_id, subnet.cidr))
                for subnet in network.subnets]

    def handle(self, request, data):
        try:
            # We must specify tenant_id of the network which a subnet is
            # created for if admin user does not belong to the tenant.
            network = api.neutron.network_get(request, data['network_id'])
            params = {
                'tenant_id': network.tenant_id,
                'network_id': data['network_id'],
                'admin_state_up': data['admin_state'] == 'True',
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

            port = api.neutron.port_create(request, **params)
            msg = _('Port %s was successfully created.') % port['id']
            LOG.debug(msg)
            messages.success(request, msg)
            return port
        except Exception:
            msg = _('Failed to create a port for network %s') \
                % data['network_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=(data['network_id'],))
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

    failure_url = 'horizon:admin:networks:detail'

    def handle(self, request, data):
        try:
            LOG.debug('params = %s' % data)
            extension_kwargs = {}
            data['admin_state'] = (data['admin_state'] == 'True')
            if 'binding__vnic_type' in data:
                extension_kwargs['binding__vnic_type'] = \
                    data['binding__vnic_type']

            if 'mac_state' in data:
                extension_kwargs['mac_learning_enabled'] = data['mac_state']

            port = api.neutron.port_update(request,
                                           data['port_id'],
                                           name=data['name'],
                                           admin_state_up=data['admin_state'],
                                           device_id=data['device_id'],
                                           device_owner=data['device_owner'],
                                           binding__host_id=data
                                           ['binding__host_id'],
                                           **extension_kwargs)
            msg = _('Port %s was successfully updated.') % data['port_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return port
        except Exception:
            msg = _('Failed to update port %s') % data['port_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['network_id']])
            exceptions.handle(request, msg, redirect=redirect)
