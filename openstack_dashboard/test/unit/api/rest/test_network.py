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
import mock

from openstack_dashboard.api.rest import network
from openstack_dashboard.test import helpers as test


class RestNetworkApiSecurityGroupTests(test.TestCase):

    @mock.patch.object(network.api, 'neutron')
    def test_security_group_detailed(self, client):
        request = self.mock_rest_request()
        client.security_group_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'default'}}),
        ]

        response = network.SecurityGroups().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "default"}]})
        client.security_group_list.assert_called_once_with(request)


class RestNetworkApiFloatingIpTests(test.TestCase):

    @mock.patch.object(network.api, 'neutron')
    def test_floating_ip_list(self, client):
        request = self.mock_rest_request()
        client.tenant_floating_ip_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'ip': '1.2.3.4'}}),
            mock.Mock(**{'to_dict.return_value': {'ip': '2.3.4.5'}})
        ])

        response = network.FloatingIPs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {'items': [{'ip': '1.2.3.4'}, {'ip': '2.3.4.5'}]})
        client.tenant_floating_ip_list.assert_called_once_with(request)

    @mock.patch.object(network.api, 'neutron')
    def test_floating_ip_pool_list(self, client):
        request = self.mock_rest_request()
        client.floating_ip_pools_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'name': '2'}})
        ])

        response = network.FloatingIPPools().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {'items': [{'name': '1'}, {'name': '2'}]})
        client.floating_ip_pools_list.assert_called_once_with(request)

    @mock.patch.object(network.api, 'neutron')
    def test_allocate_floating_ip(self, client):
        request = self.mock_rest_request(
            body='{"pool_id": "pool"}'
        )
        client.tenant_floating_ip_allocate.return_value = (
            mock.Mock(**{'to_dict.return_value': {'ip': '1.2.3.4'}})
        )

        response = network.FloatingIP().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {'ip': '1.2.3.4'})
        client.tenant_floating_ip_allocate.assert_called_once_with(request,
                                                                   'pool')

    @mock.patch.object(network.api, 'neutron')
    def test_associate_floating_ip(self, client):
        request = self.mock_rest_request(
            body='{"address_id": "address", "port_id": "port"}'
        )

        response = network.FloatingIP().patch(request)
        self.assertStatusCode(response, 204)
        client.floating_ip_associate.assert_called_once_with(request,
                                                             'address',
                                                             'port')

    @mock.patch.object(network.api, 'neutron')
    def test_disassociate_floating_ip(self, client):
        request = self.mock_rest_request(
            body='{"address_id": "address"}'
        )

        response = network.FloatingIP().patch(request)
        self.assertStatusCode(response, 204)
        client.floating_ip_disassociate.assert_called_once_with(request,
                                                                'address')
