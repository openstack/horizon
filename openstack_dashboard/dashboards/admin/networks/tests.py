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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:admin:networks:index')


class NetworkTests(test.BaseAdminViewTests):
    @test.create_stubs({api.neutron: ('network_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',)})
    def test_index(self):
        tenants = self.tenants.list()
        api.neutron.network_list(IsA(http.HttpRequest)) \
            .AndReturn(self.networks.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        for network in self.networks.list():
            api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                         network.id)\
                .AndReturn(self.agents.list())
            api.neutron.is_extension_supported(
                IsA(http.HttpRequest),
                'dhcp_agent_scheduler').AndReturn(True)

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'admin/networks/index.html')
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

    @test.create_stubs({api.neutron: ('network_list',
                                      'is_extension_supported',)})
    def test_index_network_list_exception(self):
        api.neutron.network_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'admin/networks/index.html')
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported')})
    def test_network_detail(self):
        self._test_network_detail()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_with_mac_learning(self):
        self._test_network_detail(mac_learning=True)

    def _test_network_detail(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_network_exception(self):
        self._test_network_detail_network_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_network_exception_with_mac_learning(self):
        self._test_network_detail_network_exception(mac_learning=True)

    def _test_network_detail_network_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:detail', args=[network_id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported')})
    def test_network_detail_subnet_exception(self):
        self._test_network_detail_subnet_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_subnet_exception_with_mac_learning(self):
        self._test_network_detail_subnet_exception(mac_learning=True)

    def _test_network_detail_subnet_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertEqual(len(subnets), 0)
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_port_exception(self):
        self._test_network_detail_port_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_port_exception_with_mac_learning(self):
        self._test_network_detail_port_exception(mac_learning=True)

    def _test_network_detail_port_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertEqual(len(ports), 0)

    @test.create_stubs({api.neutron: ('profile_list',
                                      'list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_get(self,
                                test_with_profile=False):
        tenants = self.tenants.list()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(
            http.HttpRequest)).AndReturn([tenants, False])
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/create.html')

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_get_with_profile(self):
        self.test_network_create_get(test_with_profile=True)

    @test.create_stubs({api.neutron: ('network_create',
                                      'profile_list',
                                      'list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post(self,
                                 test_with_profile=False):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': True,
                  'provider:network_type': 'local'}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        api.neutron.network_create(IsA(http.HttpRequest), **params)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': True,
                     'network_type': 'local'}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_with_profile(self):
        self.test_network_create_post(test_with_profile=True)

    @test.create_stubs({api.neutron: ('network_create',
                                      'profile_list',
                                      'list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_network_exception(self,
                                                   test_with_profile=False):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': False,
                  'provider:network_type': 'local'}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'tenant_id': tenant_id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'external': True,
                     'shared': False,
                     'network_type': 'local'}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_network_exception_with_profile(self):
        self.test_network_create_post_network_exception(
            test_with_profile=True)

    @test.create_stubs({api.neutron: ('list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_vlan_segmentation_id_invalid(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

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

        self.assertFormErrors(res, 1)
        self.assertContains(res, "1 through 4094")

    @test.create_stubs({api.neutron: ('list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_gre_segmentation_id_invalid(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

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

        self.assertFormErrors(res, 1)
        self.assertContains(res, "0 through %s" % ((2 ** 32) - 1))

    @test.create_stubs({api.neutron: ('list_extensions',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'segmentation_id_range': {'vxlan': [10, 20]}})
    def test_network_create_vxlan_segmentation_id_custom(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

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

        self.assertFormErrors(res, 1)
        self.assertContains(res, "10 through 20")

    @test.create_stubs({api.neutron: ('list_extensions',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'supported_provider_types': []})
    def test_network_create_no_provider_types(self):
        tenants = self.tenants.list()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/create.html')
        self.assertContains(
            res,
            '<input type="hidden" name="network_type" id="id_network_type" />',
            html=True)

    @test.create_stubs({api.neutron: ('list_extensions',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'supported_provider_types': ['local', 'flat', 'gre']})
    def test_network_create_unsupported_provider_types(self):
        tenants = self.tenants.list()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/create.html')
        network_type = res.context['form'].fields['network_type']
        self.assertListEqual(list(network_type.choices), [('local', 'Local'),
                                                          ('flat', 'Flat'),
                                                          ('gre', 'GRE')])

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/update.html')

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()
        params = {'name': network.name,
                  'shared': True,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True}
        api.neutron.network_update(IsA(http.HttpRequest), network.id,
                                   **params)\
            .AndReturn(network)
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'tenant_id': network.tenant_id,
                     'admin_state': network.admin_state_up,
                     'shared': True,
                     'external': True}
        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        params = {'name': network.name,
                  'shared': False,
                  'admin_state_up': network.admin_state_up,
                  'router:external': False}
        api.neutron.network_update(IsA(http.HttpRequest), network.id,
                                   **params)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'tenant_id': network.tenant_id,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     'external': False}
        url = reverse('horizon:admin:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_list',
                                      'network_delete',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',)})
    def test_delete_network(self):
        tenants = self.tenants.list()
        network = self.networks.first()
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id).\
            AndReturn(self.agents.list())
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        api.neutron.network_list(IsA(http.HttpRequest))\
            .AndReturn([network])
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_list',
                                      'network_delete',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',)})
    def test_delete_network_exception(self):
        tenants = self.tenants.list()
        network = self.networks.first()
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id).\
            AndReturn(self.agents.list())
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        api.neutron.network_list(IsA(http.HttpRequest))\
            .AndReturn([network])
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)
