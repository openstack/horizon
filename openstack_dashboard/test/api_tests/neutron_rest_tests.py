#
#    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

from openstack_dashboard import api
from openstack_dashboard.api.rest import neutron
from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_data import neutron_data
from openstack_dashboard.test.test_data.utils import TestData  # noqa

TEST = TestData(neutron_data.data)


class NeutronNetworksTestCase(test.TestCase):
    def setUp(self):
        super(NeutronNetworksTestCase, self).setUp()
        self._networks = [mock_factory(n)
                          for n in TEST.api_networks.list()]

    @mock.patch.object(neutron.api, 'neutron')
    def test_get_list_for_tenant(self, client):
        request = self.mock_rest_request()
        networks = self._networks
        client.network_list_for_tenant.return_value = networks
        response = neutron.Networks().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(response, TEST.api_networks.list())
        client.network_list_for_tenant.assert_called_once_with(
            request, request.user.tenant_id)

    @mock.patch.object(neutron.api, 'neutron')
    def test_create(self, client):
        self._test_create(
            '{"name": "mynetwork"}',
            {'name': 'mynetwork'}
        )

    @mock.patch.object(neutron.api, 'neutron')
    def test_create_with_bogus_param(self, client):
        self._test_create(
            '{"name": "mynetwork","bilbo":"baggins"}',
            {'name': 'mynetwork'}
        )

    @mock.patch.object(neutron.api, 'neutron')
    def _test_create(self, supplied_body, expected_call, client):
        request = self.mock_rest_request(body=supplied_body)
        client.network_create.return_value = self._networks[0]
        response = neutron.Networks().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/neutron/networks/'
                         + str(TEST.api_networks.first().get("id")))
        self.assertEqual(response.json, TEST.api_networks.first())

    #
    # Services
    #

    @test.create_stubs({api.base: ('is_service_enabled',)})
    @test.create_stubs({api.neutron: ('is_extension_supported',)})
    @mock.patch.object(neutron.api, 'neutron')
    def test_services_get(self, client):
        request = self.mock_rest_request(
            GET={"network_id": "the_network"})

        api.base.is_service_enabled(request, 'network').AndReturn(True)
        api.neutron.is_extension_supported(request, 'agent').AndReturn(True)

        client.agent_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}})
        ]
        self.mox.ReplayAll()

        response = neutron.Services().get(request)
        self.assertStatusCode(response, 200)
        client.agent_list.assert_called_once_with(
            request, network_id='the_network')
        self.assertEqual(response.content.decode('utf-8'),
                         '{"items": [{"id": "1"}, {"id": "2"}]}')

    @test.create_stubs({api.base: ('is_service_enabled',)})
    def test_services_get_disabled(self):
        request = self.mock_rest_request(
            GET={"network_id": self._networks[0].id})

        api.base.is_service_enabled(request, 'network').AndReturn(False)

        self.mox.ReplayAll()

        response = neutron.Services().get(request)
        self.assertStatusCode(response, 501)


class NeutronSubnetsTestCase(test.TestCase):
    def setUp(self):
        super(NeutronSubnetsTestCase, self).setUp()
        self._networks = [mock_factory(n)
                          for n in TEST.api_networks.list()]
        self._subnets = [mock_factory(n)
                         for n in TEST.api_subnets.list()]

    @mock.patch.object(neutron.api, 'neutron')
    def test_get(self, client):
        request = self.mock_rest_request(
            GET={"network_id": self._networks[0].id})
        client.subnet_list.return_value = [self._subnets[0]]
        response = neutron.Subnets().get(request)
        self.assertStatusCode(response, 200)
        client.subnet_list.assert_called_once_with(
            request, network_id=TEST.api_networks.first().get("id"))

    @mock.patch.object(neutron.api, 'neutron')
    def test_create(self, client):
        request = self.mock_rest_request(
            body='{"network_id": "%s",'
                 ' "ip_version": "4",'
                 ' "cidr": "192.168.199.0/24"}' % self._networks[0].id)
        client.subnet_create.return_value = self._subnets[0]
        response = neutron.Subnets().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/neutron/subnets/' +
                         str(TEST.api_subnets.first().get("id")))
        self.assertEqual(response.json, TEST.api_subnets.first())


class NeutronPortsTestCase(test.TestCase):
    def setUp(self):
        super(NeutronPortsTestCase, self).setUp()
        self._networks = [mock_factory(n)
                          for n in TEST.api_networks.list()]
        self._ports = [mock_factory(n)
                       for n in TEST.api_ports.list()]

    @mock.patch.object(neutron.api, 'neutron')
    def test_get(self, client):
        request = self.mock_rest_request(
            GET={"network_id": self._networks[0].id})
        client.port_list.return_value = [self._ports[0]]
        response = neutron.Ports().get(request)
        self.assertStatusCode(response, 200)
        client.port_list.assert_called_once_with(
            request, network_id=TEST.api_networks.first().get("id"))


def mock_obj_to_dict(r):
    return mock.Mock(**{'to_dict.return_value': r})


def mock_factory(r):
    """mocks all the attributes as well as the to_dict """
    mocked = mock_obj_to_dict(r)
    mocked.configure_mock(**r)
    return mocked
