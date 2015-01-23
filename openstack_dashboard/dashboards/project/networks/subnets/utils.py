# Copyright 2014 NEC Corporation
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

from django.utils.translation import ugettext_lazy as _

IPV6_DEFAULT_MODE = 'none/none'
IPV6_MODE_CHOICES = [
    ('none/none',
     _('No options specified')),
    ('slaac/slaac',
     _('SLAAC: Address discovered from OpenStack Router')),
    ('dhcpv6-stateful/dhcpv6-stateful',
     _('DHCPv6 stateful: Address discovered from OpenStack DHCP')),
    ('dhcpv6-stateless/dhcpv6-stateless',
     _('DHCPv6 stateless: Address discovered from OpenStack Router '
       'and additional information from OpenStack DHCP')),
]
IPV6_MODE_MAP = dict(IPV6_MODE_CHOICES)


def get_ipv6_modes_menu_from_attrs(ipv6_ra_mode, ipv6_address_mode):
    ipv6_modes = '%s/%s' % (str(ipv6_ra_mode).lower(),
                            str(ipv6_address_mode).lower())
    if ipv6_modes in IPV6_MODE_MAP:
        return ipv6_modes


def get_ipv6_modes_attrs_from_menu(ipv6_modes):
    return [None if mode == 'none' else mode
            for mode in ipv6_modes.split('/', 1)]
