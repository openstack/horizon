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

from django.http import request as django_request
import mock

from openstack_dashboard import api
from openstack_dashboard.api import base
from openstack_dashboard.api.rest import neutron
from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_data import neutron_data
from openstack_dashboard.test.test_data.utils import TestData

TEST = TestData(neutron_data.data)


class NeutronNetworksTestCase(test.TestCase):
    def setUp(self):
        super(NeutronNetworksTestCase, self).setUp()
        self._networks = [test.mock_factory(n)
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
        params = django_request.QueryDict('network_id=the_network')
        request = self.mock_rest_request(GET=params)

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
        self._networks = [test.mock_factory(n)
                          for n in TEST.api_networks.list()]
        self._subnets = [test.mock_factory(n)
                         for n in TEST.api_subnets.list()]

    @mock.patch.object(neutron.api, 'neutron')
    def test_get(self, client):
        params = django_request.QueryDict('network_id=%s' %
                                          self._networks[0].id)
        request = self.mock_rest_request(GET=params)
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
        self._networks = [test.mock_factory(n)
                          for n in TEST.api_networks.list()]
        self._ports = [test.mock_factory(n)
                       for n in TEST.api_ports.list()]

    @mock.patch.object(neutron.api, 'neutron')
    def test_get(self, client):
        params = django_request.QueryDict('network_id=%s' %
                                          self._networks[0].id)
        request = self.mock_rest_request(GET=params)
        client.port_list.return_value = [self._ports[0]]
        response = neutron.Ports().get(request)
        self.assertStatusCode(response, 200)
        client.port_list.assert_called_once_with(
            request, network_id=TEST.api_networks.first().get("id"))


class NeutronTrunkTestCase(test.TestCase):

    @mock.patch.object(neutron.api, 'neutron')
    def test_trunk_delete(self, client):
        request = self.mock_rest_request()
        neutron.Trunk().delete(request, 1)
        client.trunk_delete.assert_called_once_with(request, 1)

    @mock.patch.object(neutron.api, 'neutron')
    def test_trunk_get(self, client):
        trunk_id = TEST.api_trunks.first().get("id")
        request = self.mock_rest_request(GET={"trunk_id": trunk_id})
        client.trunk_show.return_value = self.trunks.first()
        response = neutron.Trunk().get(request, trunk_id=trunk_id)
        self.assertStatusCode(response, 200)
        client.trunk_show.assert_called_once_with(
            request, trunk_id)


class NeutronTrunksTestCase(test.TestCase):

    @mock.patch.object(neutron.api, 'neutron')
    def test_trunks_get(self, client):
        request = self.mock_rest_request(GET=django_request.QueryDict())
        client.trunk_list.return_value = self.trunks.list()
        response = neutron.Trunks().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(
            response,
            [t.to_dict() for t in self.trunks.list()])


class NeutronExtensionsTestCase(test.TestCase):
    def setUp(self):
        super(NeutronExtensionsTestCase, self).setUp()

        self._extensions = [n for n in TEST.api_extensions.list()]

    @mock.patch.object(neutron.api, 'neutron')
    def test_list_extensions(self, nc):
        request = self.mock_rest_request(**{'GET': {}})
        nc.list_extensions.return_value = self._extensions
        response = neutron.Extensions().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(response, TEST.api_extensions.list())
        nc.list_extensions.assert_called_once_with(request)


class NeutronDefaultQuotasTestCase(test.TestCase):
    @test.create_stubs({base: ('is_service_enabled',)})
    @mock.patch.object(neutron.api, 'neutron')
    def test_quotas_sets_defaults_get_when_service_is_enabled(self, client):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        base.is_service_enabled(request, 'network').AndReturn(True)

        client.tenant_quota_get.return_value = [
            base.Quota("network", 100),
            base.Quota("q2", 101)]

        self.mox.ReplayAll()

        response = neutron.DefaultQuotaSets().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(response, [
            {'limit': 100, 'display_name': 'Networks', 'name': 'network'},
            {'limit': 101, 'display_name': 'Q2', 'name': 'q2'}])

        client.tenant_quota_get.assert_called_once_with(
            request,
            request.user.tenant_id)

    @test.create_stubs({neutron.api.base: ('is_service_enabled',)})
    @mock.patch.object(neutron.api, 'neutron')
    def test_quota_sets_defaults_get_when_service_is_disabled(self, client):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        base.is_service_enabled(request, 'network').AndReturn(False)

        self.mox.ReplayAll()

        response = neutron.DefaultQuotaSets().get(request)
        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Neutron is disabled."')

        client.tenant_quota_get.assert_not_called()


class NeutronQuotaSetsTestCase(test.TestCase):
    def setUp(self):
        super(NeutronQuotaSetsTestCase, self).setUp()

        quota_set = self.neutron_quotas.list()[0]
        self._quota_data = {}

        for quota in quota_set:
            self._quota_data[quota.name] = quota.limit

    @mock.patch.object(neutron, 'quotas')
    @mock.patch.object(neutron.api, 'neutron')
    @mock.patch.object(neutron.api, 'base')
    def test_quotas_sets_patch(self, bc, nc, qc):
        request = self.mock_rest_request(body='''
            {"network": "5", "subnet": "5", "port": "50",
             "router": "5", "floatingip": "50",
             "security_group": "5", "security_group_rule": "50",
             "volumes": "5", "cores": "50"}
        ''')

        qc.get_disabled_quotas.return_value = []
        qc.NEUTRON_QUOTA_FIELDS = {n for n in self._quota_data}
        bc.is_service_enabled.return_value = True
        nc.is_extension_supported.return_value = True

        response = neutron.QuotasSets().patch(request, 'spam123')

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        nc.tenant_quota_update.assert_called_once_with(
            request, 'spam123', network='5',
            subnet='5', port='50', router='5',
            floatingip='50', security_group='5',
            security_group_rule='50')

    @mock.patch.object(neutron, 'quotas')
    @mock.patch.object(neutron.api, 'neutron')
    @mock.patch.object(neutron.api, 'base')
    def test_quotas_sets_patch_when_service_is_disabled(self, bc, nc, qc):
        request = self.mock_rest_request(body='''
            {"network": "5", "subnet": "5", "port": "50",
             "router": "5", "floatingip": "50",
             "security_group": "5", "security_group_rule": "50",
             "volumes": "5", "cores": "50"}
        ''')

        qc.get_disabled_quotas.return_value = []
        qc.NEUTRON_QUOTA_FIELDS = {n for n in self._quota_data}
        bc.is_service_enabled.return_value = False

        response = neutron.QuotasSets().patch(request, 'spam123')
        message = \
            '"Service Neutron is disabled or quotas extension not available."'

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'), message)
        nc.tenant_quota_update.assert_not_called()


def mock_obj_to_dict(r):
    return mock.Mock(**{'to_dict.return_value': r})


def mock_factory(r):
    """mocks all the attributes as well as the to_dict """
    mocked = mock_obj_to_dict(r)
    mocked.configure_mock(**r)
    return mocked
