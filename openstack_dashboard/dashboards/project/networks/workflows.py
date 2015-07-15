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
import netaddr

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets import utils


LOG = logging.getLogger(__name__)


class CreateNetworkInfoAction(workflows.Action):
    net_name = forms.CharField(max_length=255,
                               label=_("Network Name"),
                               required=False)

    admin_state = forms.ChoiceField(choices=[(True, _('UP')),
                                             (False, _('DOWN'))],
                                    label=_("Admin State"),
                                    help_text=_("The state to start"
                                                " the network in."))

    def __init__(self, request, *args, **kwargs):
        super(CreateNetworkInfoAction, self).__init__(request,
                                                      *args, **kwargs)

    class Meta(object):
        name = _("Network")
        help_text = _("Create a new network. "
                      "In addition, a subnet associated with the network "
                      "can be created in the next panel.")


class CreateNetworkInfo(workflows.Step):
    action_class = CreateNetworkInfoAction
    contributes = ("net_name", "admin_state", "net_profile_id")


class CreateSubnetInfoAction(workflows.Action):
    with_subnet = forms.BooleanField(label=_("Create Subnet"),
                                     widget=forms.CheckboxInput(attrs={
                                         'class': 'switchable',
                                         'data-slug': 'with_subnet',
                                         'data-hide-tab': 'create_network__'
                                                          'createsubnetdetail'
                                                          'action',
                                         'data-hide-on-checked': 'false'
                                     }),
                                     initial=True,
                                     required=False)
    subnet_name = forms.CharField(max_length=255,
                                  widget=forms.TextInput(attrs={
                                      'class': 'switched',
                                      'data-switch-on': 'with_subnet',
                                  }),
                                  label=_("Subnet Name"),
                                  required=False)
    cidr = forms.IPField(label=_("Network Address"),
                         required=False,
                         initial="",
                         widget=forms.TextInput(attrs={
                             'class': 'switched',
                             'data-switch-on': 'with_subnet',
                             'data-is-required': 'true'
                         }),
                         help_text=_("Network address in CIDR format "
                                     "(e.g. 192.168.0.0/24, 2001:DB8::/48)"),
                         version=forms.IPv4 | forms.IPv6,
                         mask=True)
    ip_version = forms.ChoiceField(choices=[(4, 'IPv4'), (6, 'IPv6')],
                                   widget=forms.Select(attrs={
                                       'class': 'switchable switched',
                                       'data-slug': 'ipversion',
                                       'data-switch-on': 'with_subnet'
                                   }),
                                   label=_("IP Version"))
    gateway_ip = forms.IPField(
        label=_("Gateway IP"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'with_subnet gateway_ip'
        }),
        required=False,
        initial="",
        help_text=_("IP address of Gateway (e.g. 192.168.0.254) "
                    "The default value is the first IP of the "
                    "network address "
                    "(e.g. 192.168.0.1 for 192.168.0.0/24, "
                    "2001:DB8::1 for 2001:DB8::/48). "
                    "If you use the default, leave blank. "
                    "If you do not want to use a gateway, "
                    "check 'Disable Gateway' below."),
        version=forms.IPv4 | forms.IPv6,
        mask=False)
    no_gateway = forms.BooleanField(label=_("Disable Gateway"),
                                    widget=forms.CheckboxInput(attrs={
                                        'class': 'switched switchable',
                                        'data-slug': 'gateway_ip',
                                        'data-switch-on': 'with_subnet',
                                        'data-hide-on-checked': 'true'
                                    }),
                                    initial=False,
                                    required=False)
    msg = _('Specify "Network Address" or '
            'clear "Create Subnet" checkbox.')

    class Meta(object):
        name = _("Subnet")
        help_text = _('Create a subnet associated with the new network, '
                      'in which case "Network Address" must be specified. '
                      'If you wish to create a network without a subnet, '
                      'uncheck the "Create Subnet" checkbox.')

    def __init__(self, request, context, *args, **kwargs):
        super(CreateSubnetInfoAction, self).__init__(request, context, *args,
                                                     **kwargs)
        if not getattr(settings, 'OPENSTACK_NEUTRON_NETWORK',
                       {}).get('enable_ipv6', True):
            self.fields['ip_version'].widget = forms.HiddenInput()
            self.fields['ip_version'].initial = 4

    def _check_subnet_data(self, cleaned_data, is_create=True):
        cidr = cleaned_data.get('cidr')
        ip_version = int(cleaned_data.get('ip_version'))
        gateway_ip = cleaned_data.get('gateway_ip')
        no_gateway = cleaned_data.get('no_gateway')
        if not cidr:
            raise forms.ValidationError(self.msg)
        if cidr:
            subnet = netaddr.IPNetwork(cidr)
            if subnet.version != ip_version:
                msg = _('Network Address and IP version are inconsistent.')
                raise forms.ValidationError(msg)
            if (ip_version == 4 and subnet.prefixlen == 32) or \
                    (ip_version == 6 and subnet.prefixlen == 128):
                msg = _("The subnet in the Network Address is "
                        "too small (/%s).") % subnet.prefixlen
                raise forms.ValidationError(msg)
        if not no_gateway and gateway_ip:
            if netaddr.IPAddress(gateway_ip).version is not ip_version:
                msg = _('Gateway IP and IP version are inconsistent.')
                raise forms.ValidationError(msg)
        if not is_create and not no_gateway and not gateway_ip:
            msg = _('Specify IP address of gateway or '
                    'check "Disable Gateway".')
            raise forms.ValidationError(msg)

    def clean(self):
        cleaned_data = super(CreateSubnetInfoAction, self).clean()
        with_subnet = cleaned_data.get('with_subnet')
        if not with_subnet:
            return cleaned_data
        self._check_subnet_data(cleaned_data)
        return cleaned_data


class CreateSubnetInfo(workflows.Step):
    action_class = CreateSubnetInfoAction
    contributes = ("with_subnet", "subnet_name", "cidr",
                   "ip_version", "gateway_ip", "no_gateway")


class CreateSubnetDetailAction(workflows.Action):
    enable_dhcp = forms.BooleanField(label=_("Enable DHCP"),
                                     initial=True, required=False)
    ipv6_modes = forms.ChoiceField(
        label=_("IPv6 Address Configuration Mode"),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'ipversion',
            'data-ipversion-6': _("IPv6 Address Configuration Mode"),
        }),
        initial=utils.IPV6_DEFAULT_MODE,
        required=False,
        help_text=_("Specifies how IPv6 addresses and additional information "
                    "are configured. We can specify SLAAC/DHCPv6 stateful/"
                    "DHCPv6 stateless provided by OpenStack, "
                    "or specify no option. "
                    "'No options specified' means addresses are configured "
                    "manually or configured by a non-OpenStack system."))
    allocation_pools = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_("Allocation Pools"),
        help_text=_("IP address allocation pools. Each entry is: "
                    "start_ip_address,end_ip_address "
                    "(e.g., 192.168.1.100,192.168.1.120) "
                    "and one entry per line."),
        required=False)
    dns_nameservers = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        label=_("DNS Name Servers"),
        help_text=_("IP address list of DNS name servers for this subnet. "
                    "One entry per line."),
        required=False)
    host_routes = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        label=_("Host Routes"),
        help_text=_("Additional routes announced to the hosts. "
                    "Each entry is: destination_cidr,nexthop "
                    "(e.g., 192.168.200.0/24,10.56.1.254) "
                    "and one entry per line."),
        required=False)

    class Meta(object):
        name = _("Subnet Details")
        help_text = _('Specify additional attributes for the subnet.')

    def __init__(self, request, context, *args, **kwargs):
        super(CreateSubnetDetailAction, self).__init__(request, context,
                                                       *args, **kwargs)
        if not getattr(settings, 'OPENSTACK_NEUTRON_NETWORK',
                       {}).get('enable_ipv6', True):
            self.fields['ipv6_modes'].widget = forms.HiddenInput()

    def populate_ipv6_modes_choices(self, request, context):
        return [(value, _("%s (Default)") % label)
                if value == utils.IPV6_DEFAULT_MODE
                else (value, label)
                for value, label in utils.IPV6_MODE_CHOICES]

    def _convert_ip_address(self, ip, field_name):
        try:
            return netaddr.IPAddress(ip)
        except (netaddr.AddrFormatError, ValueError):
            msg = (_('%(field_name)s: Invalid IP address (value=%(ip)s)')
                   % {'field_name': field_name, 'ip': ip})
            raise forms.ValidationError(msg)

    def _convert_ip_network(self, network, field_name):
        try:
            return netaddr.IPNetwork(network)
        except (netaddr.AddrFormatError, ValueError):
            msg = (_('%(field_name)s: Invalid IP address (value=%(network)s)')
                   % {'field_name': field_name, 'network': network})
            raise forms.ValidationError(msg)

    def _check_allocation_pools(self, allocation_pools):
        for p in allocation_pools.split('\n'):
            p = p.strip()
            if not p:
                continue
            pool = p.split(',')
            if len(pool) != 2:
                msg = _('Start and end addresses must be specified '
                        '(value=%s)') % p
                raise forms.ValidationError(msg)
            start, end = [self._convert_ip_address(ip, "allocation_pools")
                          for ip in pool]
            if start > end:
                msg = _('Start address is larger than end address '
                        '(value=%s)') % p
                raise forms.ValidationError(msg)

    def _check_dns_nameservers(self, dns_nameservers):
        for ns in dns_nameservers.split('\n'):
            ns = ns.strip()
            if not ns:
                continue
            self._convert_ip_address(ns, "dns_nameservers")

    def _check_host_routes(self, host_routes):
        for r in host_routes.split('\n'):
            r = r.strip()
            if not r:
                continue
            route = r.split(',')
            if len(route) != 2:
                msg = _('Host Routes format error: '
                        'Destination CIDR and nexthop must be specified '
                        '(value=%s)') % r
                raise forms.ValidationError(msg)
            self._convert_ip_network(route[0], "host_routes")
            self._convert_ip_address(route[1], "host_routes")

    def clean(self):
        cleaned_data = super(CreateSubnetDetailAction, self).clean()
        self._check_allocation_pools(cleaned_data.get('allocation_pools'))
        self._check_host_routes(cleaned_data.get('host_routes'))
        self._check_dns_nameservers(cleaned_data.get('dns_nameservers'))
        return cleaned_data


class CreateSubnetDetail(workflows.Step):
    action_class = CreateSubnetDetailAction
    contributes = ("enable_dhcp", "ipv6_modes", "allocation_pools",
                   "dns_nameservers", "host_routes")


class CreateNetwork(workflows.Workflow):
    slug = "create_network"
    name = _("Create Network")
    finalize_button_name = _("Create")
    success_message = _('Created network "%s".')
    failure_message = _('Unable to create network "%s".')
    default_steps = (CreateNetworkInfo,
                     CreateSubnetInfo,
                     CreateSubnetDetail)
    wizard = True

    def get_success_url(self):
        return reverse("horizon:project:networks:index")

    def get_failure_url(self):
        return reverse("horizon:project:networks:index")

    def format_status_message(self, message):
        name = self.context.get('net_name') or self.context.get('net_id', '')
        return message % name

    def _create_network(self, request, data):
        try:
            params = {'name': data['net_name'],
                      'admin_state_up': (data['admin_state'] == 'True')}
            network = api.neutron.network_create(request, **params)
            self.context['net_id'] = network.id
            msg = (_('Network "%s" was successfully created.') %
                   network.name_or_id)
            LOG.debug(msg)
            return network
        except Exception as e:
            msg = (_('Failed to create network "%(network)s": %(reason)s') %
                   {"network": data['net_name'], "reason": e})
            LOG.info(msg)
            redirect = self.get_failure_url()
            exceptions.handle(request, msg, redirect=redirect)
            return False

    def _setup_subnet_parameters(self, params, data, is_create=True):
        """Setup subnet parameters

        This methods setups subnet parameters which are available
        in both create and update.
        """
        is_update = not is_create
        params['enable_dhcp'] = data['enable_dhcp']
        if int(data['ip_version']) == 6:
            ipv6_modes = utils.get_ipv6_modes_attrs_from_menu(
                data['ipv6_modes'])
            if ipv6_modes[0] and is_create:
                params['ipv6_ra_mode'] = ipv6_modes[0]
            if ipv6_modes[1] and is_create:
                params['ipv6_address_mode'] = ipv6_modes[1]
        if data['allocation_pools']:
            pools = [dict(zip(['start', 'end'], pool.strip().split(',')))
                     for pool in data['allocation_pools'].split('\n')
                     if pool.strip()]
            params['allocation_pools'] = pools
        if data['host_routes'] or is_update:
            routes = [dict(zip(['destination', 'nexthop'],
                               route.strip().split(',')))
                      for route in data['host_routes'].split('\n')
                      if route.strip()]
            params['host_routes'] = routes
        if data['dns_nameservers'] or is_update:
            nameservers = [ns.strip()
                           for ns in data['dns_nameservers'].split('\n')
                           if ns.strip()]
            params['dns_nameservers'] = nameservers

    def _create_subnet(self, request, data, network=None, tenant_id=None,
                       no_redirect=False):
        if network:
            network_id = network.id
            network_name = network.name
        else:
            network_id = self.context.get('network_id')
            network_name = self.context.get('network_name')
        try:
            params = {'network_id': network_id,
                      'name': data['subnet_name'],
                      'cidr': data['cidr'],
                      'ip_version': int(data['ip_version'])}
            if tenant_id:
                params['tenant_id'] = tenant_id
            if data['no_gateway']:
                params['gateway_ip'] = None
            elif data['gateway_ip']:
                params['gateway_ip'] = data['gateway_ip']

            self._setup_subnet_parameters(params, data)

            subnet = api.neutron.subnet_create(request, **params)
            self.context['subnet_id'] = subnet.id
            msg = _('Subnet "%s" was successfully created.') % data['cidr']
            LOG.debug(msg)
            return subnet
        except Exception as e:
            msg = _('Failed to create subnet "%(sub)s" for network "%(net)s": '
                    ' %(reason)s')
            if no_redirect:
                redirect = None
            else:
                redirect = self.get_failure_url()
            exceptions.handle(request,
                              msg % {"sub": data['cidr'], "net": network_name,
                                     "reason": e},
                              redirect=redirect)
            return False

    def _delete_network(self, request, network):
        """Delete the created network when subnet creation failed."""
        try:
            api.neutron.network_delete(request, network.id)
            msg = _('Delete the created network "%s" '
                    'due to subnet creation failure.') % network.name
            LOG.debug(msg)
            redirect = self.get_failure_url()
            messages.info(request, msg)
            raise exceptions.Http302(redirect)
        except Exception:
            msg = _('Failed to delete network "%s"') % network.name
            LOG.info(msg)
            redirect = self.get_failure_url()
            exceptions.handle(request, msg, redirect=redirect)

    def handle(self, request, data):
        network = self._create_network(request, data)
        if not network:
            return False
        # If we do not need to create a subnet, return here.
        if not data['with_subnet']:
            return True
        subnet = self._create_subnet(request, data, network, no_redirect=True)
        if subnet:
            return True
        else:
            self._delete_network(request, network)
            return False
