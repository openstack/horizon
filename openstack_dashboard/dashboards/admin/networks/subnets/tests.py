# Copyright 2012 NEC Corporation
# Copyright 2015 Cisco Systems, Inc.
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
import mock

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import tests
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

DETAIL_URL = 'horizon:admin:networks:subnets:detail'

NETWORKS_INDEX_URL = reverse('horizon:admin:networks:index')
NETWORKS_DETAIL_URL = 'horizon:admin:networks:detail'


class NetworkSubnetTests(test.BaseAdminViewTests):

    def _stub_is_extension_supported(self, features):
        self._features = features
        self._feature_call_counts = collections.defaultdict(int)

        def fake_extension_supported(request, alias):
            self._feature_call_counts[alias] += 1
            return self._features[alias]

        self.mock_is_extension_supported.side_effect = fake_extension_supported

    def _check_is_extension_supported(self, expected_count):
        self.assertEqual(expected_count, self._feature_call_counts)

    @test.create_mocks({api.neutron: ('network_get',
                                      'subnet_get',
                                      'is_extension_supported')})
    def test_subnet_detail(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        self.mock_network_get.return_value = network
        self.mock_subnet_get.return_value = subnet
        self._stub_is_extension_supported({'network-ip-availability': True})

        url = reverse(DETAIL_URL, args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self.mock_subnet_get.assert_called_once_with(test.IsHttpRequest(),
                                                     subnet.id)
        self._check_is_extension_supported({'network-ip-availability': 1})

    @test.create_mocks({api.neutron: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        self.mock_subnet_get.side_effect = self.exceptions.neutron

        url = reverse(DETAIL_URL, args=[subnet.id])
        res = self.client.get(url)

        redir_url = NETWORKS_INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_subnet_get.assert_called_once_with(test.IsHttpRequest(),
                                                     subnet.id)

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_subnet_create_get(self):
        network = self.networks.first()

        self.mock_network_get.return_value = network
        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnets

        url = reverse('horizon:admin:networks:createsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        self.mock_network_get.return_value = network
        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnets
        self.mock_subnet_create.return_value = subnet

        form_data = tests.form_data_subnet(subnet)
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_subnet_create.assert_called_once_with(
            test.IsHttpRequest(),
            network_id=network.id,
            name=subnet.name,
            cidr=subnet.cidr,
            ip_version=subnet.ip_version,
            gateway_ip=subnet.gateway_ip,
            enable_dhcp=subnet.enable_dhcp,
            allocation_pools=subnet.allocation_pools,
            tenant_id=subnet.tenant_id)

    @test.create_mocks({api.neutron: ('network_get',)})
    def test_subnet_create_post_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        self.mock_network_get.side_effect = self.exceptions.neutron

        form_data = tests.form_data_subnet(subnet, allocation_pools=[])
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        # admin DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:project:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        self.mock_network_get.return_value = network
        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnets
        self.mock_subnet_create.side_effect = self.exceptions.neutron

        form_data = tests.form_data_subnet(subnet, allocation_pools=[])
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_subnet_create.assert_called_once_with(
            test.IsHttpRequest(),
            network_id=network.id,
            name=subnet.name,
            cidr=subnet.cidr,
            ip_version=subnet.ip_version,
            gateway_ip=subnet.gateway_ip,
            enable_dhcp=subnet.enable_dhcp,
            tenant_id=subnet.tenant_id)

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_subnet_create_post_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        self.mock_network_get.return_value = network
        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnets

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = tests.form_data_subnet(
            subnet, cidr=cidr, allocation_pools=[])
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_subnet_create_post_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        self.mock_network_get.return_value = network
        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnets

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = tests.form_data_subnet(subnet, gateway_ip=gateway_ip,
                                           allocation_pools=[])
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('subnet_update',
                                      'subnet_get',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()

        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnetpools.list()
        self.mock_subnet_get.return_value = subnet
        self.mock_subnet_update.return_value = subnet

        form_data = tests.form_data_subnet(subnet, allocation_pools=[])
        url = reverse('horizon:admin:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_subnet_get, 2,
            mock.call(test.IsHttpRequest(), subnet.id))
        self.mock_subnet_update.assert_called_once_with(
            test.IsHttpRequest(), subnet.id,
            name=subnet.name,
            enable_dhcp=subnet.enable_dhcp,
            dns_nameservers=[],
            host_routes=[])

    @test.create_mocks({api.neutron: ('subnet_get',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_subnet_update_post_gw_inconsistent(self):
        subnet = self.subnets.first()

        self._stub_is_extension_supported({'subnet_allocation': True})
        self.mock_subnetpool_list.return_value = self.subnetpools.list()
        self.mock_subnet_get.return_value = subnet

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = tests.form_data_subnet(subnet, gateway_ip=gateway_ip,
                                           allocation_pools=[])
        url = reverse('horizon:admin:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

        self._check_is_extension_supported({'subnet_allocation': 1})
        self.mock_subnetpool_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_subnet_get.assert_called_once_with(test.IsHttpRequest(),
                                                     subnet.id)

    def test_subnet_delete(self):
        self._test_subnet_delete()

    def test_subnet_delete_with_mac_learning(self):
        self._test_subnet_delete(mac_learning=True)

    @test.create_mocks({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability')})
    def _test_subnet_delete(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        ip_availability = self.ip_availability.get()

        self.mock_show_network_ip_availability.return_value = ip_availability
        self.mock_subnet_delete.return_value = None
        self.mock_subnet_list.return_value = [self.subnets.first()]
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning})

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_show_network_ip_availability.assert_called_once_with(
            test.IsHttpRequest(), network_id)
        self.mock_subnet_delete.assert_called_once_with(test.IsHttpRequest(),
                                                        subnet.id)
        self.mock_subnet_list.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id=network_id)
        self._check_is_extension_supported(
            {'network-ip-availability': 2,
             'mac-learning': 1})

    def test_subnet_delete_exception(self):
        self._test_subnet_delete_exception()

    def test_subnet_delete_exception_with_mac_learning(self):
        self._test_subnet_delete_exception(mac_learning=True)

    @test.create_mocks({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability')})
    def _test_subnet_delete_exception(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        ip_availability = self.ip_availability.get()

        self.mock_show_network_ip_availability.return_value = ip_availability
        self.mock_subnet_delete.side_effect = self.exceptions.neutron
        self.mock_subnet_list.return_value = [self.subnets.first()]
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning})

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_show_network_ip_availability.assert_called_once_with(
            test.IsHttpRequest(), network_id)
        self.mock_subnet_delete.assert_called_once_with(test.IsHttpRequest(),
                                                        subnet.id)
        self.mock_subnet_list.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id=network_id)
        self._check_is_extension_supported(
            {'network-ip-availability': 2,
             'mac-learning': 1})

    def test_network_detail_ip_availability_exception(self):
        self._test_network_detail_ip_availability_exception()

    def test_network_detail_ip_availability_exception_with_mac_learning(self):
        self._test_network_detail_ip_availability_exception(mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'subnet_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability'),
                        quotas: ('tenant_quota_usages',)})
    def _test_network_detail_ip_availability_exception(self,
                                                       mac_learning=False):
        network = self.networks.first()
        quota_data = self.neutron_quota_usages.first()

        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning,
             'network_availability_zone': True,
             'dhcp_agent_scheduler': True})
        self.mock_show_network_ip_availability.side_effect = \
            self.exceptions.neutron
        self.mock_network_get.return_value = network
        self.mock_subnet_list.return_value = [self.subnets.first()]
        self.mock_tenant_quota_usages.return_value = quota_data

        from django.utils.http import urlunquote
        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                                 args=[network.id]))
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])

        self._check_is_extension_supported(
            {'network-ip-availability': 2,
             'mac-learning': 1,
             'network_availability_zone': 1,
             'dhcp_agent_scheduler': 1})
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
