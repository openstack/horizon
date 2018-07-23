# Copyright 2016 Letv Cloud Computing
# All Rights Reserved.
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

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:floating_ips:index')
INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class AdminFloatingIpViewTest(test.BaseAdminViewTests):

    @test.create_mocks({
        api.nova: ['server_list'],
        api.keystone: ['tenant_list'],
        api.neutron: ['network_list',
                      'is_extension_supported',
                      'tenant_floating_ip_list']})
    def test_index(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        servers = self.servers.list()
        tenants = self.tenants.list()
        self.mock_tenant_floating_ip_list.return_value = fips
        self.mock_server_list.return_value = [servers, False]
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertIn('floating_ips_table', res.context)
        floating_ips_table = res.context['floating_ips_table']
        floating_ips = floating_ips_table.data
        self.assertEqual(len(floating_ips), 2)

        row_actions = floating_ips_table.get_row_actions(floating_ips[0])
        self.assertEqual(len(row_actions), 1)
        row_actions = floating_ips_table.get_row_actions(floating_ips[1])
        self.assertEqual(len(row_actions), 2)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest(),
            all_tenants=True)
        self.mock_server_list.assert_called_once_with(
            test.IsHttpRequest(),
            detailed=False,
            search_opts={'all_tenants': True})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        params = {"router:external": True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **params)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({
        api.neutron: ['network_get',
                      'is_extension_supported',
                      'tenant_floating_ip_get']})
    def test_floating_ip_detail_get(self):
        fip = self.floating_ips.first()
        network = self.networks.first()
        self.mock_tenant_floating_ip_get.return_value = fip
        self.mock_network_get.return_value = network
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(reverse('horizon:admin:floating_ips:detail',
                                      args=[fip.id]))
        self.assertTemplateUsed(res,
                                'admin/floating_ips/detail.html')
        self.assertEqual(res.context['floating_ip'].ip, fip.ip)
        self.mock_tenant_floating_ip_get.assert_called_once_with(
            test.IsHttpRequest(), fip.id)
        self.mock_network_get.assert_called_once_with(
            test.IsHttpRequest(), fip.pool)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({api.neutron: ['tenant_floating_ip_get']})
    def test_floating_ip_detail_exception(self):
        fip = self.floating_ips.first()
        # Only supported by neutron, so raise a neutron exception
        self.mock_tenant_floating_ip_get.side_effect = self.exceptions.neutron

        res = self.client.get(reverse('horizon:admin:floating_ips:detail',
                                      args=[fip.id]))

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_tenant_floating_ip_get.assert_called_once_with(
            test.IsHttpRequest(), fip.id)

    @test.create_mocks({api.neutron: ['tenant_floating_ip_list',
                                      'is_extension_supported']})
    def test_index_no_floating_ips(self):
        self.mock_tenant_floating_ip_list.return_value = []
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest(), all_tenants=True)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({api.neutron: ['tenant_floating_ip_list',
                                      'is_extension_supported']})
    def test_index_error(self):
        self.mock_tenant_floating_ip_list.side_effect = self.exceptions.neutron
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest(), all_tenants=True)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({
        api.neutron: ['network_list'],
        api.keystone: ['tenant_list']})
    def test_admin_allocate_get(self):
        pool = self.networks.first()
        tenants = self.tenants.list()

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = [pool]

        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'admin/floating_ips/allocate.html')
        allocate_form = res.context['form']

        pool_choices = allocate_form.fields['pool'].choices
        self.assertEqual(len(pool_choices), 1)
        tenant_choices = allocate_form.fields['tenant'].choices
        self.assertEqual(len(tenant_choices), 3)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'router:external': True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **search_opts)

    @test.create_mocks({
        api.neutron: ['network_list'],
        api.keystone: ['tenant_list']})
    def test_admin_allocate_post_invalid_ip_version(self):
        tenant = self.tenants.first()
        pool = self.networks.first()
        tenants = self.tenants.list()

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = [pool]

        form_data = {'pool': pool.id,
                     'tenant': tenant.id,
                     'floating_ip_address': 'fc00::1'}
        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.post(url, form_data)
        self.assertContains(res, "Invalid version for IP address")
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'router:external': True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **search_opts)

    @test.create_mocks({
        api.neutron: ['tenant_floating_ip_allocate',
                      'network_list',
                      'subnet_get'],
        api.keystone: ['tenant_list']})
    def test_admin_allocate_post(self):
        tenant = self.tenants.first()
        floating_ip = self.floating_ips.first()
        subnet = self.subnets.first()
        pool = self.networks.first()
        tenants = self.tenants.list()

        self.mock_subnet_get.return_value = subnet
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = [pool]
        self.mock_tenant_floating_ip_allocate.return_value = floating_ip

        form_data = {'pool': subnet.id,
                     'tenant': tenant.id}
        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_subnet_get.assert_called_once_with(
            test.IsHttpRequest(), subnet.id)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'router:external': True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **search_opts)
        self.mock_tenant_floating_ip_allocate.assert_called_once_with(
            test.IsHttpRequest(),
            pool=pool.id,
            subnet_id=subnet.id,
            tenant_id=tenant.id)

    @test.create_mocks({
        api.neutron: ['tenant_floating_ip_list',
                      'floating_ip_disassociate',
                      'is_extension_supported',
                      'network_list'],
        api.nova: ['server_list'],
        api.keystone: ['tenant_list']})
    def test_admin_disassociate_floatingip(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        floating_ip = self.floating_ips.list()[1]
        servers = self.servers.list()
        tenants = self.tenants.list()
        self.mock_tenant_floating_ip_list.return_value = fips
        self.mock_server_list.return_value = [servers, False]
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_floating_ip_disassociate.return_value = None
        self.mock_is_extension_supported.return_value = True

        form_data = {
            "action":
            "floating_ips__disassociate__%s" % floating_ip.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest(), all_tenants=True)
        self.mock_server_list.assert_called_once_with(
            test.IsHttpRequest(),
            detailed=False,
            search_opts={'all_tenants': True})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        params = {"router:external": True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **params)
        self.mock_floating_ip_disassociate.assert_called_once_with(
            test.IsHttpRequest(), floating_ip.id)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({
        api.neutron: ['tenant_floating_ip_list',
                      'is_extension_supported',
                      'network_list'],
        api.nova: ['server_list'],
        api.keystone: ['tenant_list']})
    def test_admin_delete_floatingip(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        floating_ip = self.floating_ips.list()[1]
        servers = self.servers.list()
        tenants = self.tenants.list()
        self.mock_tenant_floating_ip_list.return_value = fips
        self.mock_server_list.return_value = [servers, False]
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_is_extension_supported.return_value = True

        form_data = {
            "action":
            "floating_ips__delete__%s" % floating_ip.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest(), all_tenants=True)
        self.mock_server_list.assert_called_once_with(
            test.IsHttpRequest(),
            detailed=False,
            search_opts={'all_tenants': True})
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        params = {"router:external": True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **params)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({
        api.neutron: ['tenant_floating_ip_list',
                      'is_extension_supported',
                      'network_list'],
        api.nova: ['server_list'],
        api.keystone: ['tenant_list']})
    def test_floating_ip_table_actions(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        servers = self.servers.list()
        tenants = self.tenants.list()
        self.mock_tenant_floating_ip_list.return_value = fips
        self.mock_server_list.return_value = [servers, False]
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertIn('floating_ips_table', res.context)
        floating_ips_table = res.context['floating_ips_table']
        floating_ips = floating_ips_table.data
        self.assertEqual(len(floating_ips), 2)
        # table actions
        self.assertContains(res, 'id="floating_ips__action_allocate"')
        self.assertContains(res, 'id="floating_ips__action_release"')
        # row actions
        self.assertContains(res, 'floating_ips__release__%s' % fips[0].id)
        self.assertContains(res, 'floating_ips__release__%s' % fips[1].id)
        self.assertContains(res, 'floating_ips__disassociate__%s' % fips[1].id)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest(), all_tenants=True)
        self.mock_server_list.assert_called_once_with(
            test.IsHttpRequest(),
            detailed=False,
            search_opts={'all_tenants': True})
        params = {"router:external": True}
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **params)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')
