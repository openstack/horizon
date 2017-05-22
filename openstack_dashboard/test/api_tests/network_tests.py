# Copyright 2013 NEC Corporation
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

import collections

from django.test.utils import override_settings

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class NetworkApiNeutronTestBase(test.APITestCase):
    def setUp(self):
        super(NetworkApiNeutronTestBase, self).setUp()
        self.qclient = self.stub_neutronclient()


class NetworkApiNeutronTests(NetworkApiNeutronTestBase):

    def _get_expected_addresses(self, server, no_fip_expected=True):
        server_ports = self.ports.filter(device_id=server.id)
        addresses = collections.defaultdict(list)
        for p in server_ports:
            net_name = self.networks.get(id=p['network_id']).name
            for ip in p.fixed_ips:
                addresses[net_name].append(
                    {'version': 4,
                     'addr': ip['ip_address'],
                     'OS-EXT-IPS-MAC:mac_addr': p.mac_address,
                     'OS-EXT-IPS:type': 'fixed'})
                if no_fip_expected:
                    continue
                fips = self.floating_ips.filter(port_id=p['id'])
                if not fips:
                    continue
                # Only one FIP should match.
                fip = fips[0]
                addresses[net_name].append(
                    {'version': 4,
                     'addr': fip.floating_ip_address,
                     'OS-EXT-IPS-MAC:mac_addr': p.mac_address,
                     'OS-EXT-IPS:type': 'floating'})
        return addresses

    def _check_server_address(self, res_server_data, no_fip_expected=False):
        expected_addresses = self._get_expected_addresses(res_server_data,
                                                          no_fip_expected)
        self.assertEqual(len(expected_addresses),
                         len(res_server_data.addresses))
        for net, addresses in expected_addresses.items():
            self.assertIn(net, res_server_data.addresses)
            self.assertEqual(addresses, res_server_data.addresses[net])

    def _test_servers_update_addresses(self, router_enabled=True):
        tenant_id = self.request.user.tenant_id

        servers = self.servers.list()
        server_ids = tuple([server.id for server in servers])
        server_ports = [p for p in self.api_ports.list()
                        if p['device_id'] in server_ids]
        server_port_ids = tuple([p['id'] for p in server_ports])
        if router_enabled:
            assoc_fips = [fip for fip in self.api_floating_ips.list()
                          if fip['port_id'] in server_port_ids]
        server_network_ids = [p['network_id'] for p in server_ports]
        server_networks = [net for net in self.api_networks.list()
                           if net['id'] in server_network_ids]

        self.qclient.list_ports(device_id=server_ids) \
            .AndReturn({'ports': server_ports})
        if router_enabled:
            self.qclient.list_floatingips(tenant_id=tenant_id,
                                          port_id=server_port_ids) \
                .AndReturn({'floatingips': assoc_fips})
            self.qclient.list_ports(tenant_id=tenant_id) \
                .AndReturn({'ports': self.api_ports.list()})
        self.qclient.list_networks(id=frozenset(server_network_ids)) \
            .AndReturn({'networks': server_networks})
        self.qclient.list_subnets() \
            .AndReturn({'subnets': self.api_subnets.list()})
        self.mox.ReplayAll()

        api.network.servers_update_addresses(self.request, servers)

        self.assertEqual(self.servers.count(), len(servers))
        self.assertEqual([server.id for server in self.servers.list()],
                         [server.id for server in servers])

        no_fip_expected = not router_enabled

        # server[0] has one fixed IP and one floating IP
        # if router ext isenabled.
        self._check_server_address(servers[0], no_fip_expected)
        # The expected is also calculated, we examine the result manually once.
        addrs = servers[0].addresses['net1']
        if router_enabled:
            self.assertEqual(2, len(addrs))
            self.assertEqual('fixed', addrs[0]['OS-EXT-IPS:type'])
            self.assertEqual('floating', addrs[1]['OS-EXT-IPS:type'])
        else:
            self.assertEqual(1, len(addrs))
            self.assertEqual('fixed', addrs[0]['OS-EXT-IPS:type'])

        # server[1] has one fixed IP.
        self._check_server_address(servers[1], no_fip_expected)
        # manual check.
        addrs = servers[1].addresses['net2']
        self.assertEqual(1, len(addrs))
        self.assertEqual('fixed', addrs[0]['OS-EXT-IPS:type'])

        # server[2] has no corresponding ports in neutron_data,
        # so it should be an empty dict.
        self.assertFalse(servers[2].addresses)

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_router': True})
    def test_servers_update_addresses(self):
        self._test_servers_update_addresses()

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_router': False})
    def test_servers_update_addresses_router_disabled(self):
        self._test_servers_update_addresses(router_enabled=False)
