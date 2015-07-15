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

from horizon.workflows import views

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import tests
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

    @test.create_stubs({api.neutron: ('list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_get(self):
        tenants = self.tenants.list()
        extensions = self.api_extensions.list()
        api.keystone.tenant_list(IsA(
            http.HttpRequest)).AndReturn([tenants, False])
        api.neutron.list_extensions(
            IsA(http.HttpRequest)).AndReturn(extensions)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/create.html')

    @test.create_stubs({api.neutron: ('network_create',
                                      'list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post(self):
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
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_create',
                                      'list_extensions',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_network_exception(self):
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
        url = reverse('horizon:admin:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

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


class NetworkSubnetTests(test.BaseAdminViewTests):

    @test.create_stubs({api.neutron: ('network_get', 'subnet_get',)})
    def test_subnet_detail(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/subnets/detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

    @test.create_stubs({api.neutron: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        # admin DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:project:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:addsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools,
                                  tenant_id=subnet.tenant_id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = tests.form_data_subnet(subnet)
        url = reverse('horizon:admin:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:admin:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = tests.form_data_subnet(subnet, allocation_pools=[])
        url = reverse('horizon:admin:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        # admin DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:project:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  tenant_id=subnet.tenant_id)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = tests.form_data_subnet(subnet, allocation_pools=[])
        url = reverse('horizon:admin:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:admin:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = tests.form_data_subnet(
            subnet, cidr=cidr, allocation_pools=[])
        url = reverse('horizon:admin:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = tests.form_data_subnet(subnet, gateway_ip=gateway_ip,
                                           allocation_pools=[])
        url = reverse('horizon:admin:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_update(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  enable_dhcp=subnet.enable_dhcp,
                                  dns_nameservers=[],
                                  host_routes=[])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = tests.form_data_subnet(subnet, allocation_pools=[])
        url = reverse('horizon:admin:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:admin:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_gw_inconsistent(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = tests.form_data_subnet(subnet, gateway_ip=gateway_ip,
                                           allocation_pools=[])
        url = reverse('horizon:admin:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete(self):
        self._test_subnet_delete()

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete_with_mac_learning(self):
        self._test_subnet_delete(mac_learning=True)

    def _test_subnet_delete(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:admin:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete_exception(self):
        self._test_subnet_delete_exception()

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete_exception_with_mac_learning(self):
        self._test_subnet_delete_exception(mac_learning=True)

    def _test_subnet_delete_exception(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:admin:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)


class NetworkPortTests(test.BaseAdminViewTests):

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_detail(self):
        self._test_port_detail()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_detail_with_mac_learning(self):
        self._test_port_detail(mac_learning=True)

    def _test_port_detail(self, mac_learning=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(self.ports.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .MultipleTimes().AndReturn(mac_learning)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'project/networks/ports/detail.html')
        self.assertEqual(res.context['port'].id, port.id)

    @test.create_stubs({api.neutron: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:networks:ports:detail',
                                      args=[port.id]))

        # admin DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:admin:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',)})
    def test_port_create_get(self):
        self._test_port_create_get()

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',)})
    def test_port_create_get_with_mac_learning(self):
        self._test_port_create_get(mac_learning=True)

    def _test_port_create_get(self, mac_learning=False, binding=False):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/ports/create.html')

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'port_create',)})
    def test_port_create_post(self):
        self._test_port_create_post()

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'port_create',)})
    def test_port_create_post_with_mac_learning(self):
        self._test_port_create_post(mac_learning=True, binding=False)

    def _test_port_create_post(self, mac_learning=False, binding=False):
        network = self.networks.first()
        port = self.ports.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = \
                port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_create(IsA(http.HttpRequest),
                                tenant_id=network.tenant_id,
                                network_id=network.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:admin:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'port_create',
                                      'is_extension_supported',)})
    def test_port_create_post_exception(self):
        self._test_port_create_post_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'port_create',
                                      'is_extension_supported',)})
    def test_port_create_post_exception_with_mac_learning(self):
        self._test_port_create_post_exception(mac_learning=True)

    def _test_port_create_post_exception(self, mac_learning=False,
                                         binding=False):
        network = self.networks.first()
        port = self.ports.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_create(IsA(http.HttpRequest),
                                tenant_id=network.tenant_id,
                                network_id=network.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'mac_state': True,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_learning_enabled'] = True
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:admin:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_update_get(self):
        self._test_port_update_get()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_update_get_with_mac_learning(self):
        self._test_port_update_get(mac_learning=True)

    def _test_port_update_get(self, mac_learning=False, binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest),
                             port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/ports/update.html')

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post(self):
        self._test_port_update_post()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_with_mac_learning(self):
        self._test_port_update_post(mac_learning=True)

    def _test_port_update_post(self, mac_learning=False, binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_update(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:admin:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_exception(self):
        self._test_port_update_post_exception()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_exception_with_mac_learning(self):
        self._test_port_update_post_exception(mac_learning=True, binding=False)

    def _test_port_update_post_exception(self, mac_learning=False,
                                         binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_update(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:admin:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_port_delete(self):
        self._test_port_delete()

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_port_delete_with_mac_learning(self):
        self._test_port_delete(mac_learning=True)

    def _test_port_delete(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.port_delete(IsA(http.HttpRequest), port.id)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse('horizon:admin:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_port_delete_exception(self):
        self._test_port_delete_exception()

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks')})
    def test_port_delete_exception_with_mac_learning(self):
        self._test_port_delete_exception(mac_learning=True)

    def _test_port_delete_exception(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.port_delete(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse('horizon:admin:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)


class NetworkAgentTests(test.BaseAdminViewTests):

    @test.create_stubs({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_agent_add_get(self):
        network = self.networks.first()
        api.neutron.agent_list(IsA(http.HttpRequest), agent_type='DHCP agent')\
            .AndReturn(self.agents.list())
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id)\
            .AndReturn(self.agents.list())
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/agents/add.html')

    @test.create_stubs({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',
                                      'add_network_to_dhcp_agent',)})
    def test_agent_add_post(self):
        network = self.networks.first()
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id)\
            .AndReturn([self.agents.list()[1]])
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.agent_list(IsA(http.HttpRequest), agent_type='DHCP agent')\
            .AndReturn(self.agents.list())
        api.neutron.add_network_to_dhcp_agent(IsA(http.HttpRequest),
                                              agent_id, network.id)\
            .AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'network_name': network.name,
                     'agent': agent_id}
        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:admin:networks:detail',
                            args=[network.id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',
                                      'add_network_to_dhcp_agent',)})
    def test_agent_add_post_exception(self):
        network = self.networks.first()
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id)\
            .AndReturn([self.agents.list()[1]])
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.agent_list(IsA(http.HttpRequest), agent_type='DHCP agent')\
            .AndReturn(self.agents.list())
        api.neutron.add_network_to_dhcp_agent(IsA(http.HttpRequest),
                                              agent_id, network.id)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'network_name': network.name,
                     'agent': agent_id}
        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:admin:networks:detail',
                            args=[network.id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported',
                                      'remove_network_from_dhcp_agent',)})
    def test_agent_delete(self):
        network_id = self.networks.first().id
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.remove_network_from_dhcp_agent(IsA(http.HttpRequest),
                                                   agent_id, network_id)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(False)
        self.mox.ReplayAll()

        form_data = {'action': 'agents__delete__%s' % agent_id}
        url = reverse('horizon:admin:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported',
                                      'remove_network_from_dhcp_agent',)})
    def test_agent_delete_exception(self):
        network_id = self.networks.first().id
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.remove_network_from_dhcp_agent(IsA(http.HttpRequest),
                                                   agent_id, network_id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(False)
        self.mox.ReplayAll()

        form_data = {'action': 'agents__delete__%s' % agent_id}
        url = reverse('horizon:admin:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)
