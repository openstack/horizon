# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class AddInterface(forms.SelfHandlingForm):
    use_required_attribute = False
    subnet_id = forms.ThemableChoiceField(label=_("Subnet"))
    ip_address = forms.IPField(
        label=_("IP Address (optional)"), required=False, initial="",
        help_text=_("Specify an IP address for the interface "
                    "created (e.g. 192.168.0.254)."),
        version=forms.IPv4 | forms.IPv6, mask=False)
    failure_url = 'horizon:project:routers:detail'

    def __init__(self, request, *args, **kwargs):
        super(AddInterface, self).__init__(request, *args, **kwargs)
        c = self.populate_subnet_id_choices(request)
        self.fields['subnet_id'].choices = c

    def populate_subnet_id_choices(self, request):
        tenant_id = self.request.user.tenant_id
        networks = []
        router_subnet_ids = []
        router_id = self.initial['router_id']

        try:
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
            if router_id:
                ports = api.neutron.port_list(request, device_id=router_id)
                router_subnet_ids = [fixed_ip["subnet_id"] for port in ports
                                     for fixed_ip in port.fixed_ips]
        except Exception as e:
            LOG.info('Failed to get network list: %s', e)
            msg = _('Failed to get network list: %s') % e
            messages.error(request, msg)
            if router_id:
                redirect = reverse(self.failure_url, args=[router_id])
            else:
                redirect = reverse('horizon:project:routers:index')
            exceptions.handle(request, msg, redirect=redirect)
            return

        choices = []
        for n in networks:
            net_name = n.name + ': ' if n.name else ''
            choices += [(subnet.id,
                         '%s%s (%s)' % (net_name, subnet.cidr,
                                        subnet.name or subnet.id))
                        for subnet in n['subnets']
                        if (subnet.id not in router_subnet_ids and
                            subnet.gateway_ip)]
        if choices:
            choices.insert(0, ("", _("Select Subnet")))
        else:
            choices.insert(0, ("", _("No subnets available")))
        return choices

    def handle(self, request, data):
        if data['ip_address']:
            port = self._add_interface_by_port(request, data)
        else:
            port = self._add_interface_by_subnet(request, data)
        msg = _('Interface added')
        if port:
            msg += ' ' + port.fixed_ips[0]['ip_address']
        messages.success(request, msg)
        return True

    def _add_interface_by_subnet(self, request, data):
        router_id = self.initial['router_id']
        try:
            router_inf = api.neutron.router_add_interface(
                request, router_id, subnet_id=data['subnet_id'])
        except Exception as e:
            self._handle_error(request, router_id, e)
        try:
            port = api.neutron.port_get(request, router_inf['port_id'])
        except Exception:
            # Ignore an error when port_get() since it is just
            # to get an IP address for the interface.
            port = None
        return port

    def _add_interface_by_port(self, request, data):
        router_id = self.initial['router_id']
        subnet_id = data['subnet_id']
        try:
            subnet = api.neutron.subnet_get(request, subnet_id)
        except Exception:
            msg = _('Unable to get subnet "%s"') % subnet_id
            self._handle_error(request, router_id, msg)
        try:
            ip_address = data['ip_address']
            body = {'network_id': subnet.network_id,
                    'fixed_ips': [{'subnet_id': subnet.id,
                                   'ip_address': ip_address}]}
            port = api.neutron.port_create(request, **body)
        except Exception as e:
            self._handle_error(request, router_id, e)
        try:
            api.neutron.router_add_interface(request, router_id,
                                             port_id=port.id)
        except Exception as e:
            self._delete_port(request, port)
            self._handle_error(request, router_id, e)
        return port

    def _handle_error(self, request, router_id, reason):
        LOG.info('Failed to add_interface: %s', reason)
        msg = _('Failed to add interface: %s') % reason
        redirect = reverse(self.failure_url, args=[router_id])
        exceptions.handle(request, msg, redirect=redirect)

    def _delete_port(self, request, port):
        try:
            api.neutron.port_delete(request, port.id)
        except Exception as e:
            LOG.info('Failed to delete port %(id)s: %(exc)s',
                     {'id': port.id, 'exc': e})
            msg = _('Failed to delete port %s') % port.id
            exceptions.handle(request, msg)


class SetGatewayForm(forms.SelfHandlingForm):
    network_id = forms.ThemableChoiceField(label=_("External Network"))
    enable_snat = forms.BooleanField(label=_("Enable SNAT"),
                                     initial=True,
                                     required=False)
    failure_url = 'horizon:project:routers:index'

    def __init__(self, request, *args, **kwargs):
        super(SetGatewayForm, self).__init__(request, *args, **kwargs)
        networks = self.populate_network_id_choices(request)
        self.fields['network_id'].choices = networks
        self.ext_gw_mode = api.neutron.is_extension_supported(
            self.request, 'ext-gw-mode')
        self.enable_snat_allowed = api.neutron.get_feature_permission(
            self.request,
            "ext-gw-mode",
            "update_router_enable_snat")
        if not self.ext_gw_mode or not self.enable_snat_allowed:
            del self.fields['enable_snat']

    def populate_network_id_choices(self, request):
        search_opts = {'router:external': True}
        try:
            networks = api.neutron.network_list(request, **search_opts)
        except Exception as e:
            LOG.info('Failed to get network list: %s', e)
            msg = _('Failed to get network list: %s') % e
            messages.error(request, msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return
        choices = [(network.id, network.name or network.id)
                   for network in networks]
        if choices:
            choices.insert(0, ("", _("Select network")))
        else:
            choices.insert(0, ("", _("No networks available")))
        return choices

    def handle(self, request, data):
        try:
            enable_snat = None
            if 'enable_snat' in data:
                enable_snat = data['enable_snat']
            api.neutron.router_add_gateway(request,
                                           self.initial['router_id'],
                                           data['network_id'],
                                           enable_snat)
            msg = _('Gateway interface is added')
            messages.success(request, msg)
            return True
        except Exception as e:
            LOG.info('Failed to set gateway to router %(id)s: %(exc)s',
                     {'id': self.initial['router_id'], 'exc': e})
            msg = _('Failed to set gateway: %s') % e
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
