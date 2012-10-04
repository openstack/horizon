# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import netaddr

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import forms
from horizon import workflows
from horizon.utils import fields

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class CreateNetworkInfoAction(workflows.Action):
    net_name = forms.CharField(max_length=255,
                               label=_("Network Name (optional)"),
                               required=False)

    class Meta:
        name = ("Network")
        help_text = _("From here you can create a new network.\n"
                      "In addition a subnet associated with the network "
                      "can be created in the next panel.")


class CreateNetworkInfo(workflows.Step):
    action_class = CreateNetworkInfoAction
    contributes = ("net_name",)


class CreateSubnetInfoAction(workflows.Action):
    with_subnet = forms.BooleanField(label=_("Create Subnet"),
                                     initial=True, required=False)
    subnet_name = forms.CharField(max_length=255,
                                  label=_("Subnet Name (optional)"),
                                  required=False)
    cidr = fields.IPField(label=_("Network Address"),
                          required=False,
                          initial="",
                          help_text=_("Network address in CIDR format "
                                      "(e.g. 192.168.0.0/24)"),
                          version=fields.IPv4 | fields.IPv6,
                          mask=True)
    ip_version = forms.ChoiceField(choices=[(4, 'IPv4'), (6, 'IPv6')],
                                   label=_("IP Version"))
    gateway_ip = fields.IPField(label=_("Gateway IP (optional)"),
                                required=False,
                                initial="",
                                help_text=_("IP address of Gateway "
                                            "(e.g. 192.168.0.1)"),
                                version=fields.IPv4 | fields.IPv6,
                                mask=False)

    class Meta:
        name = ("Subnet")
        help_text = _('You can create a subnet associated with the new '
                      'network, in which case "Network Address" must be '
                      'specified. If you wish to create a network WITHOUT a '
                      'subnet, uncheck the "Create Subnet" checkbox.')

    def clean(self):
        cleaned_data = super(CreateSubnetInfoAction, self).clean()
        with_subnet = cleaned_data.get('with_subnet')
        cidr = cleaned_data.get('cidr')
        ip_version = int(cleaned_data.get('ip_version'))
        gateway_ip = cleaned_data.get('gateway_ip')
        if with_subnet and not cidr:
            msg = _('Specify "Network Address" or '
                    'clear "Create Subnet" checkbox.')
            raise forms.ValidationError(msg)
        if cidr:
            if netaddr.IPNetwork(cidr).version is not ip_version:
                msg = _('Network Address and IP version are inconsistent.')
                raise forms.ValidationError(msg)
        if gateway_ip:
            if netaddr.IPAddress(gateway_ip).version is not ip_version:
                msg = _('Gateway IP and IP version are inconsistent.')
                raise forms.ValidationError(msg)
        return cleaned_data


class CreateSubnetInfo(workflows.Step):
    action_class = CreateSubnetInfoAction
    contributes = ("with_subnet", "subnet_name", "cidr",
                   "ip_version", "gateway_ip")


class CreateNetwork(workflows.Workflow):
    slug = "create_network"
    name = _("Create Network")
    finalize_button_name = _("Create")
    success_message = _('Created network "%s".')
    failure_message = _('Unable to create network "%s".')
    success_url = "horizon:project:networks:index"
    default_steps = (CreateNetworkInfo,
                     CreateSubnetInfo)

    def format_status_message(self, message):
        name = self.context.get('net_name') or self.context.get('net_id', '')
        return message % name

    def handle(self, request, data):
        # create the network
        try:
            network = api.quantum.network_create(request,
                                                 name=data['net_name'])
            network.set_id_as_name_if_empty()
            self.context['net_id'] = network.id
            msg = _('Network "%s" was successfully created.') % network.name
            LOG.debug(msg)
        except:
            msg = _('Failed to create network "%s".') % data['net_name']
            LOG.info(msg)
            redirect = reverse('horizon:project:networks:index')
            exceptions.handle(request, msg, redirect=redirect)
            return False

        # If we do not need to create a subnet, return here.
        if not data['with_subnet']:
            return True

        # Create the subnet.
        try:
            params = {'network_id': network.id,
                      'name': data['subnet_name'],
                      'cidr': data['cidr'],
                      'ip_version': int(data['ip_version'])}
            if data['gateway_ip']:
                params['gateway_ip'] = data['gateway_ip']
            api.quantum.subnet_create(request, **params)
            msg = _('Subnet "%s" was successfully created.') % data['cidr']
            LOG.debug(msg)
        except Exception:
            msg = _('Failed to create subnet "%(sub)s" for network "%(net)s".')
            redirect = reverse('horizon:project:networks:index')
            exceptions.handle(request,
                              msg % {"sub": data['cidr'], "net": network.id},
                              redirect=redirect)
            return False

        return True
