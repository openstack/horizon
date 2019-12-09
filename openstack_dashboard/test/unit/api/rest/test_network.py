# Copyright 2015, Hewlett-Packard Development Company, L.P.
# Copyright 2016 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from openstack_dashboard import api
from openstack_dashboard.api.rest import network
from openstack_dashboard.test import helpers as test


class RestNetworkApiSecurityGroupTests(test.TestCase):

    @test.create_mocks({api.neutron: ['security_group_list']})
    def test_security_group_detailed(self):
        request = self.mock_rest_request()
        self.mock_security_group_list.return_value = \
            self.security_groups.list()

        response = network.SecurityGroups().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [sg.to_dict() for sg
                                    in self.security_groups.list()]})
        self.mock_security_group_list.assert_called_once_with(request)


class RestNetworkApiFloatingIpTests(test.TestCase):

    @test.create_mocks({api.neutron: ['tenant_floating_ip_list']})
    def test_floating_ip_list(self):
        request = self.mock_rest_request()
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()

        response = network.FloatingIPs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {'items': [fip.to_dict() for fip
                                    in self.floating_ips.list()]})
        self.mock_tenant_floating_ip_list.assert_called_once_with(request)

    @test.create_mocks({api.neutron: ['floating_ip_pools_list']})
    def test_floating_ip_pool_list(self):
        pools = [api.neutron.FloatingIpPool(n)
                 for n in self.api_networks.list()
                 if n['router:external']]
        request = self.mock_rest_request()
        self.mock_floating_ip_pools_list.return_value = pools

        response = network.FloatingIPPools().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {'items': [p.to_dict() for p in pools]})
        self.mock_floating_ip_pools_list.assert_called_once_with(request)

    @test.create_mocks({api.neutron: ['tenant_floating_ip_allocate']})
    def test_allocate_floating_ip(self):
        request = self.mock_rest_request(
            body='{"pool_id": "pool"}'
        )
        fip = self.floating_ips.first()
        self.mock_tenant_floating_ip_allocate.return_value = fip

        response = network.FloatingIP().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, fip.to_dict())
        self.mock_tenant_floating_ip_allocate.assert_called_once_with(request,
                                                                      'pool',
                                                                      None,
                                                                      **{})

    @test.create_mocks({api.neutron: ['floating_ip_associate']})
    def test_associate_floating_ip(self):
        self.mock_floating_ip_associate.return_value = None
        request = self.mock_rest_request(
            body='{"address_id": "address", "port_id": "port"}'
        )

        response = network.FloatingIP().patch(request)
        self.assertStatusCode(response, 204)
        self.mock_floating_ip_associate.assert_called_once_with(request,
                                                                'address',
                                                                'port')

    @test.create_mocks({api.neutron: ['floating_ip_disassociate']})
    def test_disassociate_floating_ip(self):
        self.mock_floating_ip_disassociate.return_value = None
        request = self.mock_rest_request(
            body='{"address_id": "address"}'
        )

        response = network.FloatingIP().patch(request)
        self.assertStatusCode(response, 204)
        self.mock_floating_ip_disassociate.assert_called_once_with(request,
                                                                   'address')
