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

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:floating_ips:index')
INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class AdminFloatingIpViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('server_list', ),
                        api.keystone: ('tenant_list', ),
                        api.neutron: ('network_list',
                                      'tenant_floating_ip_list',)})
    def test_index(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        servers = self.servers.list()
        tenants = self.tenants.list()
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn(fips)
        api.nova.server_list(IsA(http.HttpRequest),
                             search_opts={'all_tenants': True}) \
            .AndReturn([servers, False])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {"router:external": True}
        api.neutron.network_list(IsA(http.HttpRequest), **params) \
            .AndReturn(self.networks.list())

        self.mox.ReplayAll()

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

    @test.create_stubs({api.neutron: ('tenant_floating_ip_get',
                                      'network_get', )})
    def test_floating_ip_detail_get(self):
        fip = self.floating_ips.first()
        network = self.networks.first()
        api.neutron.tenant_floating_ip_get(
            IsA(http.HttpRequest), fip.id).AndReturn(fip)
        api.neutron.network_get(
            IsA(http.HttpRequest), fip.pool).AndReturn(network)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:floating_ips:detail',
                                      args=[fip.id]))
        self.assertTemplateUsed(res,
                                'admin/floating_ips/detail.html')
        self.assertEqual(res.context['floating_ip'].ip, fip.ip)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_get',)})
    def test_floating_ip_detail_exception(self):
        fip = self.floating_ips.first()
        # Only supported by neutron, so raise a neutron exception
        api.neutron.tenant_floating_ip_get(
            IsA(http.HttpRequest),
            fip.id).AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:floating_ips:detail',
                                      args=[fip.id]))

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list', )})
    def test_index_no_floating_ips(self):
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn([])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list', )})
    def test_index_error(self):
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True) \
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

    @test.create_stubs({api.neutron: ('network_list',),
                        api.keystone: ('tenant_list',)})
    def test_admin_allocate_get(self):
        pool = self.networks.first()
        tenants = self.tenants.list()

        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        search_opts = {'router:external': True}
        api.neutron.network_list(IsA(http.HttpRequest), **search_opts) \
            .AndReturn([pool])

        self.mox.ReplayAll()

        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'admin/floating_ips/allocate.html')
        allocate_form = res.context['form']

        pool_choices = allocate_form.fields['pool'].choices
        self.assertEqual(len(pool_choices), 1)
        tenant_choices = allocate_form.fields['tenant'].choices
        self.assertEqual(len(tenant_choices), 3)

    @test.create_stubs({api.neutron: ('network_list',),
                        api.keystone: ('tenant_list',)})
    def test_admin_allocate_post_invalid_ip_version(self):
        tenant = self.tenants.first()
        pool = self.networks.first()
        tenants = self.tenants.list()

        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        search_opts = {'router:external': True}
        api.neutron.network_list(IsA(http.HttpRequest), **search_opts) \
            .AndReturn([pool])
        self.mox.ReplayAll()

        form_data = {'pool': pool.id,
                     'tenant': tenant.id,
                     'floating_ip_address': 'fc00::1'}
        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.post(url, form_data)
        self.assertContains(res, "Invalid version for IP address")

    @test.create_stubs({api.neutron: ('tenant_floating_ip_allocate',
                                      'network_list', 'subnet_get'),
                        api.keystone: ('tenant_list',)})
    def test_admin_allocate_post(self):
        tenant = self.tenants.first()
        floating_ip = self.floating_ips.first()
        subnet = self.subnets.first()
        pool = self.networks.first()
        tenants = self.tenants.list()

        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        search_opts = {'router:external': True}
        api.neutron.network_list(IsA(http.HttpRequest), **search_opts) \
            .AndReturn([pool])
        api.neutron.tenant_floating_ip_allocate(
            IsA(http.HttpRequest),
            pool=pool.id,
            tenant_id=tenant.id).AndReturn(floating_ip)
        self.mox.ReplayAll()

        form_data = {'pool': subnet.id,
                     'tenant': tenant.id}
        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list',
                                      'floating_ip_disassociate',
                                      'network_list'),
                        api.nova: ('server_list', ),
                        api.keystone: ('tenant_list', )})
    def test_admin_disassociate_floatingip(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        floating_ip = self.floating_ips.list()[1]
        servers = self.servers.list()
        tenants = self.tenants.list()
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn(fips)
        api.nova.server_list(IsA(http.HttpRequest),
                             search_opts={'all_tenants': True}) \
            .AndReturn([servers, False])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {"router:external": True}
        api.neutron.network_list(IsA(http.HttpRequest), **params) \
            .AndReturn(self.networks.list())
        api.neutron.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "floating_ips__disassociate__%s" % floating_ip.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list',
                                      'network_list'),
                        api.nova: ('server_list', ),
                        api.keystone: ('tenant_list', )})
    def test_admin_delete_floatingip(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        floating_ip = self.floating_ips.list()[1]
        servers = self.servers.list()
        tenants = self.tenants.list()
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn(fips)
        api.nova.server_list(IsA(http.HttpRequest),
                             search_opts={'all_tenants': True}) \
            .AndReturn([servers, False])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {"router:external": True}
        api.neutron.network_list(IsA(http.HttpRequest), **params) \
            .AndReturn(self.networks.list())

        self.mox.ReplayAll()

        form_data = {
            "action":
            "floating_ips__delete__%s" % floating_ip.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list',
                                      'network_list'),
                        api.nova: ('server_list', ),
                        api.keystone: ('tenant_list', )})
    def test_floating_ip_table_actions(self):
        # Use neutron test data
        fips = self.floating_ips.list()
        servers = self.servers.list()
        tenants = self.tenants.list()
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn(fips)
        api.nova.server_list(IsA(http.HttpRequest),
                             search_opts={'all_tenants': True}) \
            .AndReturn([servers, False])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {"router:external": True}
        api.neutron.network_list(IsA(http.HttpRequest), **params) \
            .AndReturn(self.networks.list())

        self.mox.ReplayAll()

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
