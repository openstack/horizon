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
from openstack_dashboard.usage import quotas


class NeutronNetworksTestCase(test.TestCase):

    def _dictify_network(self, network):
        net_dict = network.to_dict()
        net_dict['subnets'] = [s.to_dict() for s in net_dict['subnets']]
        return net_dict

    @mock.patch.object(api.neutron, 'network_list_for_tenant')
    def test_get_list_for_tenant(self, mock_network_list_for_tenant):
        request = self.mock_rest_request()
        mock_network_list_for_tenant.return_value = self.networks.list()
        response = neutron.Networks().get(request)
        self.assertStatusCode(response, 200)
        exp_resp = [self._dictify_network(n) for n in self.networks.list()]
        self.assertItemsCollectionEqual(response, exp_resp)
        mock_network_list_for_tenant.assert_called_once_with(
            request, request.user.tenant_id,
            include_pre_auto_allocate=True)

    def test_create(self):
        self._test_create(
            '{"name": "mynetwork"}',
            {'name': 'mynetwork'}
        )

    def test_create_with_bogus_param(self):
        self._test_create(
            '{"name": "mynetwork","bilbo":"baggins"}',
            {'name': 'mynetwork', 'bilbo': 'baggins'}
        )

    @mock.patch.object(api.neutron, 'network_create')
    def _test_create(self, supplied_body, expected, mock_network_create):
        request = self.mock_rest_request(body=supplied_body)
        mock_network_create.return_value = self.networks.first()
        response = neutron.Networks().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/neutron/networks/' + self.networks.first().id)
        exp_resp = self._dictify_network(self.networks.first())
        self.assertEqual(response.json, exp_resp)
        mock_network_create.assert_called_once_with(request, **expected)

    #
    # Services
    #

    @test.create_mocks({api.base: ['is_service_enabled'],
                        api.neutron: ['is_extension_supported',
                                      'agent_list']})
    def test_services_get(self):
        params = django_request.QueryDict('network_id=the_network')
        request = self.mock_rest_request(GET=params)

        self.mock_is_service_enabled.return_value = True
        self.mock_is_extension_supported.return_value = True

        self.mock_agent_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}})
        ]

        response = neutron.Services().get(request)
        self.assertStatusCode(response, 200)
        self.mock_is_service_enabled.assert_called_once_with(
            request, 'network')
        self.mock_is_extension_supported.assert_called_once_with(
            request, 'agent')
        self.mock_agent_list.assert_called_once_with(
            request, network_id='the_network')
        self.assertEqual(response.content.decode('utf-8'),
                         '{"items": [{"id": "1"}, {"id": "2"}]}')

    @mock.patch.object(api.base, 'is_service_enabled')
    def test_services_get_disabled(self, mock_is_service_enabled):
        request = self.mock_rest_request(
            GET={"network_id": self.networks.first().id})

        mock_is_service_enabled.return_value = False

        response = neutron.Services().get(request)
        self.assertStatusCode(response, 501)
        mock_is_service_enabled.assert_called_once_with(request, 'network')


class NeutronSubnetsTestCase(test.TestCase):

    @mock.patch.object(api.neutron, 'subnet_list')
    def test_get(self, mock_subnet_list):
        network_id = self.networks.first().id
        params = django_request.QueryDict('network_id=%s' % network_id)
        request = self.mock_rest_request(GET=params)
        mock_subnet_list.return_value = self.subnets.list()
        response = neutron.Subnets().get(request)
        self.assertStatusCode(response, 200)
        mock_subnet_list.assert_called_once_with(
            request, network_id=network_id)

    @mock.patch.object(api.neutron, 'subnet_create')
    def test_create(self, mock_subnet_create):
        network_id = self.networks.first().id
        request = self.mock_rest_request(
            body='{"network_id": "%s",'
                 ' "ip_version": "4",'
                 ' "cidr": "192.168.199.0/24"}' % network_id)
        mock_subnet_create.return_value = self.subnets.first()
        response = neutron.Subnets().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/neutron/subnets/' +
                         self.subnets.first().id)
        self.assertEqual(response.json, self.subnets.first().to_dict())
        mock_subnet_create.assert_called_once_with(
            request, cidr='192.168.199.0/24', ip_version='4',
            network_id=network_id)


class NeutronPortsTestCase(test.TestCase):

    @mock.patch.object(api.neutron, 'port_list_with_trunk_types')
    def test_get(self, mock_port_list_with_trunk_types):
        network_id = self.networks.first().id
        params = django_request.QueryDict('network_id=%s' % network_id)
        request = self.mock_rest_request(GET=params)
        mock_port_list_with_trunk_types.return_value = self.ports.list()
        response = neutron.Ports().get(request)
        self.assertStatusCode(response, 200)
        mock_port_list_with_trunk_types.assert_called_once_with(
            request, network_id=network_id)


class NeutronTrunkTestCase(test.TestCase):

    @mock.patch.object(api.neutron, 'trunk_delete')
    def test_trunk_delete(self, mock_trunk_delete):
        mock_trunk_delete.return_value = None
        request = self.mock_rest_request()
        response = neutron.Trunk().delete(request, 1)
        self.assertStatusCode(response, 204)
        mock_trunk_delete.assert_called_once_with(request, 1)

    @mock.patch.object(api.neutron, 'trunk_show')
    def test_trunk_get(self, mock_trunk_show):
        trunk_id = self.trunks.first().id
        request = self.mock_rest_request(GET={"trunk_id": trunk_id})
        mock_trunk_show.return_value = self.trunks.first()
        response = neutron.Trunk().get(request, trunk_id=trunk_id)
        self.assertStatusCode(response, 200)
        mock_trunk_show.assert_called_once_with(
            request, trunk_id)

    @mock.patch.object(api.neutron, 'trunk_update')
    def test_trunk_patch(self, mock_trunk_update):
        request = self.mock_rest_request(body='''
            [{"name": "trunk1"}, {"name": "trunk2"}]
        ''')
        mock_trunk_update.return_value = self.trunks.first()

        response = neutron.Trunk().patch(request, '1')
        self.assertStatusCode(response, 200)
        mock_trunk_update.assert_called_once_with(
            request, '1', {'name': 'trunk1'}, {'name': 'trunk2'}
        )


class NeutronTrunksTestCase(test.TestCase):

    @mock.patch.object(api.neutron, 'trunk_list')
    def test_trunks_get(self, mock_trunk_list):
        request = self.mock_rest_request(GET=django_request.QueryDict())
        mock_trunk_list.return_value = self.trunks.list()
        response = neutron.Trunks().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(
            response,
            [t.to_dict() for t in self.trunks.list()])
        mock_trunk_list.assert_called_once_with(request)

    @mock.patch.object(api.neutron, 'trunk_create')
    def test_trunks_create(self, mock_trunk_create):
        request = self.mock_rest_request(body='''
            {"name": "trunk1", "port_id": "1"}
        ''')
        trunk = self.trunks.first()
        mock_trunk_create.return_value = trunk
        response = neutron.Trunks().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.json, trunk.to_dict())
        mock_trunk_create.assert_called_once_with(request, name='trunk1',
                                                  port_id='1')


class NeutronExtensionsTestCase(test.TestCase):

    @mock.patch.object(api.neutron, 'list_extensions')
    def test_list_extensions(self, mock_list_extensions):
        request = self.mock_rest_request(**{'GET': {}})
        mock_list_extensions.return_value = self.api_extensions.list()
        response = neutron.Extensions().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(response, self.api_extensions.list())
        mock_list_extensions.assert_called_once_with(request)


class NeutronDefaultQuotasTestCase(test.TestCase):

    @test.create_mocks({api.base: ['is_service_enabled'],
                        api.neutron: ['tenant_quota_get']})
    def test_quotas_sets_defaults_get_when_service_is_enabled(self):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        self.mock_is_service_enabled.return_value = True
        self.mock_tenant_quota_get.return_value = [
            base.Quota("network", 100),
            base.Quota("q2", 101)]

        response = neutron.DefaultQuotaSets().get(request)
        self.assertStatusCode(response, 200)
        self.assertItemsCollectionEqual(response, [
            {'limit': 100, 'display_name': 'Networks', 'name': 'network'},
            {'limit': 101, 'display_name': 'Q2', 'name': 'q2'}])

        self.mock_is_service_enabled.assert_called_once_with(
            request, 'network')
        self.mock_tenant_quota_get.assert_called_once_with(
            request,
            request.user.tenant_id)

    @mock.patch.object(api.base, 'is_service_enabled')
    def test_quota_sets_defaults_get_when_service_is_disabled(
            self, mock_is_service_enabled):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})
        mock_is_service_enabled.return_value = False

        response = neutron.DefaultQuotaSets().get(request)
        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Neutron is disabled."')

        mock_is_service_enabled.assert_called_once_with(request, 'network')


class NeutronQuotaSetsTestCase(test.TestCase):

    @test.create_mocks({api.base: ['is_service_enabled'],
                        api.neutron: ['is_extension_supported',
                                      'tenant_quota_update'],
                        quotas: ['get_disabled_quotas']})
    def test_quotas_sets_patch(self):
        request = self.mock_rest_request(body='''
            {"network": "5", "subnet": "5", "port": "50",
             "router": "5", "floatingip": "50",
             "security_group": "5", "security_group_rule": "50",
             "volumes": "5", "cores": "50"}
        ''')

        self.mock_get_disabled_quotas.return_value = []
        self.mock_is_service_enabled.return_value = True
        self.mock_is_extension_supported.return_value = True
        self.mock_tenant_quota_update.return_value = None

        response = neutron.QuotasSets().patch(request, 'spam123')

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')

        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_is_service_enabled.assert_called_once_with(
            request, 'network')
        self.mock_is_extension_supported.assert_called_once_with(
            request, 'quotas')
        self.mock_tenant_quota_update.assert_called_once_with(
            request, 'spam123', network='5',
            subnet='5', port='50', router='5',
            floatingip='50', security_group='5',
            security_group_rule='50')

    @test.create_mocks({api.base: ['is_service_enabled'],
                        quotas: ['get_disabled_quotas']})
    def test_quotas_sets_patch_when_service_is_disabled(self):
        request = self.mock_rest_request(body='''
            {"network": "5", "subnet": "5", "port": "50",
             "router": "5", "floatingip": "50",
             "security_group": "5", "security_group_rule": "50",
             "volumes": "5", "cores": "50"}
        ''')

        self.mock_get_disabled_quotas.return_value = []
        self.mock_is_service_enabled.return_value = False

        response = neutron.QuotasSets().patch(request, 'spam123')
        message = ('"Service Neutron is disabled or '
                   'quotas extension not available."')

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'), message)

        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_is_service_enabled.assert_called_once_with(
            request, 'network')
