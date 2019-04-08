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

import collections

from django.urls import reverse
from django.utils.http import urlunquote

import mock

from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import tests
from openstack_dashboard.test import helpers as test
from openstack_dashboard import usage

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'
INDEX_URL = reverse('horizon:admin:networks:index')


class NetworkTests(test.BaseAdminViewTests):

    def _stub_is_extension_supported(self, features):
        self._features = features
        self._feature_call_counts = collections.defaultdict(int)

        def fake_extension_supported(request, alias):
            self._feature_call_counts[alias] += 1
            return self._features[alias]

        self.mock_is_extension_supported.side_effect = fake_extension_supported

    def _check_is_extension_supported(self, expected_count):
        self.assertEqual(expected_count, self._feature_call_counts)

    @test.create_mocks({api.neutron: ('network_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',),
                        usage.quotas: ('tenant_quota_usages',)})
    def test_index(self):
        tenants = self.tenants.list()
        quota_data = self.quota_usages.first()

        self.mock_network_list.return_value = self.networks.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 1,
             'dhcp_agent_scheduler': len(self.networks.list()) + 1})
        self.mock_tenant_quota_usages.assert_has_calls(
            [mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                       targets=('subnet', ))
             for network in self.networks.list()])
        self.assertEqual(len(self.networks.list()),
                         self.mock_tenant_quota_usages.call_count)
        self.mock_list_dhcp_agent_hosting_networks.assert_has_calls(
            [mock.call(test.IsHttpRequest(), network.id)
             for network in self.networks.list()])
        self.assertEqual(len(self.networks.list()),
                         self.mock_list_dhcp_agent_hosting_networks.call_count)

    @test.create_mocks({api.neutron: ('network_list',
                                      'is_extension_supported',)})
    def test_index_network_list_exception(self):
        self.mock_network_list.side_effect = self.exceptions.neutron
        self._stub_is_extension_supported(
            {'network_availability_zone': True,
             'dhcp_agent_scheduler': True})

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 1,
             'dhcp_agent_scheduler': 1})

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported'),
                        usage.quotas: ('tenant_quota_usages',)})
    def test_network_detail_new(self, mac_learning=False):
        network = self.networks.first()
        quota_data = self.quota_usages.first()

        self.mock_network_get.return_value = network
        self.mock_tenant_quota_usages.return_value = quota_data
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'network_availability_zone': True,
             'mac-learning': mac_learning,
             'dhcp_agent_scheduler': True})

        url = urlunquote(reverse('horizon:admin:networks:detail',
                                 args=[network.id]))

        res = self.client.get(url)
        network = res.context['network']
        self.assertEqual(self.networks.first().name_or_id, network.name_or_id)
        self.assertEqual(self.networks.first().status_label,
                         network.status_label)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_tenant_quota_usages.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=network.tenant_id,
            targets=('subnet',))
        self._check_is_extension_supported(
            {'network-ip-availability': 1,
             'network_availability_zone': 1,
             'mac-learning': 1,
             'dhcp_agent_scheduler': 1})

    def test_network_detail_subnets_tab(self):
        self._test_network_detail_subnets_tab()

    def test_network_detail_subnets_tab_with_mac_learning(self):
        self._test_network_detail_subnets_tab(mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'subnet_list',
                                      'show_network_ip_availability',
                                      'is_extension_supported'),
                        usage.quotas: ('tenant_quota_usages',)})
    def _test_network_detail_subnets_tab(self, mac_learning=False):
        network = self.networks.first()
        ip_availability = self.ip_availability.get()
        quota_data = self.quota_usages.first()

        self.mock_show_network_ip_availability.return_value = ip_availability
        self.mock_network_get.return_value = network
        self.mock_subnet_list.return_value = [self.subnets.first()]
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning,
             'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_tenant_quota_usages.return_value = quota_data

        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                         args=[network.id]))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])

        self.mock_show_network_ip_availability.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_subnet_list.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id=network.id)
        self._check_is_extension_supported(
            {'network-ip-availability': 2,
             'mac-learning': 1,
             'network_availability_zone': 1,
             'dhcp_agent_scheduler': 1})
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                      targets=('subnet',)))

    @test.create_mocks({api.neutron: ('network_get',
                                      'port_list',
                                      'is_extension_supported'),
                        usage.quotas: ('tenant_quota_usages',)})
    def test_network_detail_ports_tab(self, mac_learning=False):
        network = self.networks.first()
        quota_data = self.neutron_quota_usages.first()

        self.mock_network_get.return_value = network
        self.mock_port_list.return_value = [self.ports.first()]
        self.mock_tenant_quota_usages.return_value = quota_data
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning,
             'network_availability_zone': True,
             'dhcp_agent_scheduler': True})

        url = reverse('horizon:admin:networks:ports_tab',
                      args=[network.id])
        res = self.client.get(urlunquote(url))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        ports = res.context['ports_table'].data
        self.assertItemsEqual(ports, [self.ports.first()])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_port_list.assert_called_once_with(test.IsHttpRequest(),
                                                    network_id=network.id)
        self.assertEqual(3, self.mock_tenant_quota_usages.call_count)
        self.mock_tenant_quota_usages.assert_has_calls([
            mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                      targets=('subnet',)),
            mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                      targets=('port',)),
            mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                      targets=('port',)),
        ])
        self._check_is_extension_supported(
            {'network-ip-availability': 1,
             'mac-learning': 1,
             'network_availability_zone': 1,
             'dhcp_agent_scheduler': 1})

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',),
                        usage.quotas: ('tenant_quota_usages',)})
    def test_network_detail_agents_tab(self, mac_learning=False):
        network = self.networks.first()
        quota_data = self.quota_usages.first()

        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning,
             'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()
        self.mock_network_get.return_value = network
        self.mock_tenant_quota_usages.return_value = quota_data

        url = reverse('horizon:admin:networks:agents_tab', args=[network.id])
        res = self.client.get(urlunquote(url))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        result_agents = res.context['agents_table'].data
        expected_agents = self.agents.list()

        self.assertItemsEqual(result_agents, expected_agents)

        self._check_is_extension_supported(
            {'network-ip-availability': 1,
             'mac-learning': 1,
             'network_availability_zone': 1,
             'dhcp_agent_scheduler': 2})
        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.mock_network_get.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.mock_tenant_quota_usages.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=network.tenant_id,
            targets=('subnet',))

    def test_network_detail_subnets_tab_network_exception(self):
        self._test_network_detail_subnets_tab_network_exception()

    def test_network_detail_network_exception_with_mac_learning(self):
        self._test_network_detail_subnets_tab_network_exception(
            mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'subnet_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability')})
    def _test_network_detail_subnets_tab_network_exception(self,
                                                           mac_learning=False):
        network_id = self.networks.first().id
        ip_availability = self.ip_availability.get()

        self.mock_show_network_ip_availability.return_value = ip_availability
        self.mock_network_get.side_effect = self.exceptions.neutron
        self.mock_subnet_list.return_value = [self.subnets.first()]
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning})

        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                                 args=[network_id]))
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_show_network_ip_availability.assert_called_once_with(
            test.IsHttpRequest(), network_id)
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id)
        self.mock_subnet_list.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id=network_id)
        self._check_is_extension_supported(
            {'network-ip-availability': 2,
             'mac-learning': 1})

    def test_network_detail_subnets_tab_subnet_exception(self):
        self._test_network_detail_subnets_tab_subnet_exception()

    def test_network_detail_subnets_tab_subnet_exception_w_mac_learning(self):
        self._test_network_detail_subnets_tab_subnet_exception(
            mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'subnet_list',
                                      'show_network_ip_availability',
                                      'is_extension_supported'),
                        usage.quotas: ('tenant_quota_usages',)})
    def _test_network_detail_subnets_tab_subnet_exception(self,
                                                          mac_learning=False):
        network = self.networks.first()
        quota_data = self.quota_usages.first()

        self.mock_show_network_ip_availability.return_value = \
            self.ip_availability.get()
        self.mock_network_get.return_value = network
        self.mock_subnet_list.side_effect = self.exceptions.neutron
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning,
             'dhcp_agent_scheduler': True,
             'network_availability_zone': True})
        self.mock_tenant_quota_usages.return_value = quota_data

        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                         args=[network.id]))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertEqual(len(subnets), 0)

        self.mock_show_network_ip_availability.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_subnet_list.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id=network.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                      targets=('subnet',)))
        self._stub_is_extension_supported(
            {'network-ip-availability': 1,
             'mac-learning': 1,
             'dhcp_agent_scheduler': 2,
             'network_availability_zone': 1})

    def test_network_detail_port_exception(self):
        self._test_network_detail_subnets_tab_port_exception()

    def test_network_detail_subnets_tab_port_exception_with_mac_learning(self):
        self._test_network_detail_subnets_tab_port_exception(mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'subnet_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability'),
                        usage.quotas: ('tenant_quota_usages',)})
    def _test_network_detail_subnets_tab_port_exception(self,
                                                        mac_learning=False):
        network = self.networks.first()
        ip_availability = self.ip_availability.get()
        quota_data = self.quota_usages.first()

        self.mock_show_network_ip_availability.return_value = ip_availability
        self.mock_network_get.return_value = network
        self.mock_subnet_list.return_value = [self.subnets.first()]
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning,
             'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_tenant_quota_usages.return_value = quota_data

        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                         args=[network.id]))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])

        self.mock_show_network_ip_availability.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_subnet_list.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id=network.id)
        self._check_is_extension_supported(
            {'network-ip-availability': 2,
             'mac-learning': 1,
             'network_availability_zone': 1,
             'dhcp_agent_scheduler': 1})
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), tenant_id=network.tenant_id,
                      targets=('subnet',)))

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_get(self):
        tenants = self.tenants.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': False,
             'subnet_allocation': False})

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_workflow_base.html')

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'provider': 1,
             'network_availability_zone': 2,
             'subnet_allocation': 1})

    @test.create_mocks({api.neutron: ('network_create',
                                      'is_extension_supported',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': False,
             'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnetpools.list()
        self.mock_network_create.return_value = network

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': True,
                     'network_type': 'local'}
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': True,
                  'provider:network_type': 'local'}
        self.mock_network_create.assert_called_once_with(test.IsHttpRequest(),
                                                         **params)
        self._check_is_extension_supported(
            {'provider': 3,
             'network_availability_zone': 2,
             'subnet_allocation': 1})

    @test.create_mocks({api.neutron: ('network_create',
                                      'is_extension_supported',
                                      'list_availability_zones',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_with_az(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': True,
             'subnet_allocation': True})
        self.mock_list_availability_zones.return_value = \
            self.neutron_availability_zones.list()
        self.mock_subnetpool_list.return_value = self.subnetpools.list()
        self.mock_network_create.return_value = network

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': True,
                     'network_type': 'local',
                     'az_hints': ['nova']}
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._stub_is_extension_supported(
            {'provider': 1,
             'network_availability_zone': 1,
             'subnet_allocation': 1})
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_list_availability_zones, 2,
            mock.call(test.IsHttpRequest(), "network", "available"))
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': True,
                  'provider:network_type': 'local',
                  'availability_zone_hints': ['nova']}
        self.mock_network_create.assert_called_once_with(test.IsHttpRequest(),
                                                         **params)

    @test.create_mocks({api.neutron: ('network_create',
                                      'subnet_create',
                                      'is_extension_supported',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_with_subnet(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        subnet = self.subnets.first()

        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': False,
             'subnet_allocation': True})
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_subnetpool_list.return_value = self.subnetpools.list()
        self.mock_network_create.return_value = network
        self.mock_subnet_create.return_value = subnet

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': True,
                     'network_type': 'local',
                     'with_subnet': True}
        form_data.update(tests.form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self._check_is_extension_supported(
            {'provider': 3,
             'network_availability_zone': 2,
             'subnet_allocation': 1})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': True,
                  'provider:network_type': 'local'}
        self.mock_network_create.assert_called_once_with(test.IsHttpRequest(),
                                                         **params)
        subnet_params = {'tenant_id': tenant_id,
                         'name': subnet.name,
                         'network_id': subnet.network_id,
                         'cidr': subnet.cidr,
                         'enable_dhcp': subnet.enable_dhcp,
                         'gateway_ip': subnet.gateway_ip,
                         'ip_version': subnet.ip_version}
        self.mock_subnet_create.assert_called_once_with(test.IsHttpRequest(),
                                                        **subnet_params)

    @test.create_mocks({api.neutron: ('network_create',
                                      'is_extension_supported',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_network_exception(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': False,
             'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnetpools.list()
        self.mock_network_create.side_effect = self.exceptions.neutron

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': False,
                     'network_type': 'local'}
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'provider': 3,
             'network_availability_zone': 2,
             'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': False,
                  'provider:network_type': 'local'}
        self.mock_network_create.assert_called_once_with(test.IsHttpRequest(),
                                                         **params)

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_vlan_segmentation_id_invalid(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'network_availability_zone': False,
             'subnet_allocation': False,
             'provider': True})

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': False,
                     'network_type': 'vlan',
                     'physical_network': 'default',
                     'segmentation_id': 4095}
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertWorkflowErrors(res, 1)
        self.assertContains(res, "1 through 4094")

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 2,
             'subnet_allocation': 1,
             'provider': 2})

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_gre_segmentation_id_invalid(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'network_availability_zone': False,
             'subnet_allocation': False,
             'provider': True})

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': False,
                     'network_type': 'gre',
                     'physical_network': 'default',
                     'segmentation_id': (2 ** 32) + 1}
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertWorkflowErrors(res, 1)
        self.assertContains(res, "1 through %s" % ((2 ** 32) - 1))

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 2,
             'subnet_allocation': 1,
             'provider': 2})

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'segmentation_id_range': {'vxlan': [10, 20]}})
    def test_network_create_vxlan_segmentation_id_custom(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'network_availability_zone': False,
             'subnet_allocation': False,
             'provider': True})

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': False,
                     'network_type': 'vxlan',
                     'physical_network': 'default',
                     'segmentation_id': 9}
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertWorkflowErrors(res, 1)
        self.assertContains(res, "10 through 20")

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 2,
             'subnet_allocation': 1,
             'provider': 2})

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'supported_provider_types': []})
    def test_network_create_no_provider_types(self):
        tenants = self.tenants.list()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'network_availability_zone': False,
             'subnet_allocation': False,
             'provider': True})

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_workflow_base.html')
        self.assertContains(
            res,
            '<input type="hidden" name="network_type" id="id_network_type" />',
            html=True)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 2,
             'subnet_allocation': 1,
             'provider': 1})

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'supported_provider_types': ['local', 'flat', 'gre']})
    def test_network_create_unsupported_provider_types(self):
        tenants = self.tenants.list()

        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'network_availability_zone': False,
             'subnet_allocation': False,
             'provider': True})

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_workflow_base.html')
        network_type = res.context['form'].fields['network_type']
        self.assertListEqual(list(network_type.choices), [('local', 'Local'),
                                                          ('flat', 'Flat'),
                                                          ('gre', 'GRE')])

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'network_availability_zone': 2,
             'subnet_allocation': 1,
             'provider': 1})

    @test.create_mocks({api.neutron: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        self.mock_network_get.return_value = network

        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/update.html')

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id,
                                                      expand_subnet=False)

    @test.create_mocks({api.neutron: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        self.mock_network_get.side_effect = self.exceptions.neutron

        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id,
                                                      expand_subnet=False)

    @test.create_mocks({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()

        self.mock_network_update.return_value = network
        self.mock_network_get.return_value = network

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'tenant_id': network.tenant_id,
                     'admin_state': network.admin_state_up,
                     'shared': True,
                     'external': True}
        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        params = {'name': network.name,
                  'shared': True,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True}
        self.mock_network_update.assert_called_once_with(test.IsHttpRequest(),
                                                         network.id,
                                                         **params)
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id,
                                                      expand_subnet=False)

    @test.create_mocks({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        params = {'name': network.name,
                  'shared': False,
                  'admin_state_up': network.admin_state_up,
                  'router:external': False}
        self.mock_network_update.side_effect = self.exceptions.neutron
        self.mock_network_get.return_value = network

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'tenant_id': network.tenant_id,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     'external': False}
        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_network_update.assert_called_once_with(test.IsHttpRequest(),
                                                         network.id,
                                                         **params)
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id,
                                                      expand_subnet=False)

    @test.create_mocks({api.neutron: ('network_list',
                                      'network_delete',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',)})
    def test_delete_network(self):
        tenants = self.tenants.list()
        network = self.networks.first()

        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()
        self._stub_is_extension_supported(
            {'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = [network]
        self.mock_network_delete.return_value = None

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self._check_is_extension_supported(
            {'network_availability_zone': 1,
             'dhcp_agent_scheduler': 2})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_network_delete.assert_called_once_with(test.IsHttpRequest(),
                                                         network.id)

    @test.create_mocks({api.neutron: ('network_list',
                                      'network_delete',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',)})
    def test_delete_network_exception(self):
        tenants = self.tenants.list()
        network = self.networks.first()

        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()
        self._stub_is_extension_supported(
            {'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = [network]
        self.mock_network_delete.side_effect = self.exceptions.neutron

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self._check_is_extension_supported(
            {'network_availability_zone': 1,
             'dhcp_agent_scheduler': 2})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_network_delete.assert_called_once_with(test.IsHttpRequest(),
                                                         network.id)

    @test.create_mocks({api.neutron: ('is_extension_supported',)})
    @test.update_settings(FILTER_DATA_FIRST={'admin.networks': True})
    def test_networks_list_with_admin_filter_first(self):
        self._stub_is_extension_supported(
            {'network_availability_zone': True,
             'dhcp_agent_scheduler': True})

        res = self.client.get(reverse('horizon:admin:networks:index'))
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, [])

        self._check_is_extension_supported(
            {'network_availability_zone': 1,
             'dhcp_agent_scheduler': 1})

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.neutron: ('is_extension_supported',)})
    def test_networks_list_with_non_exist_tenant_filter(self):
        self._stub_is_extension_supported(
            {'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        self.client.post(
            reverse('horizon:admin:networks:index'),
            data={'networks__filter_admin_networks__q_field': 'project',
                  'networks__filter_admin_networks__q': 'non_exist_tenant'})
        res = self.client.get(reverse('horizon:admin:networks:index'))
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, [])

        self._check_is_extension_supported(
            {'network_availability_zone': 2,
             'dhcp_agent_scheduler': 2})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_without_physical_networks(self):
        tenants = self.tenants.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': False,
             'subnet_allocation': False})

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)
        physical_network = res.context['form'].fields['physical_network']
        self.assertEqual(type(physical_network), forms.CharField)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'provider': 1,
             'network_availability_zone': 2,
             'subnet_allocation': 1})

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'physical_networks': ['default', 'test']})
    def test_network_create_with_physical_networks(self):
        tenants = self.tenants.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self._stub_is_extension_supported(
            {'provider': True,
             'network_availability_zone': False,
             'subnet_allocation': False})

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)
        physical_network = res.context['form'].fields['physical_network']
        self.assertEqual(type(physical_network), forms.ThemableChoiceField)
        self.assertListEqual(list(physical_network.choices),
                             [('default', 'default'), ('test', 'test')])

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_is_extension_supported(
            {'provider': 1,
             'network_availability_zone': 2,
             'subnet_allocation': 1})
