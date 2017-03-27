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
from django.utils.http import urlunquote

from mox3.mox import IsA

from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import tests
from openstack_dashboard.test import helpers as test

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'
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

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
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

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported')})
    def test_network_detail_subnets_tab(self):
        self._test_network_detail_subnets_tab()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_subnets_tab_with_mac_learning(self):
        self._test_network_detail_subnets_tab(mac_learning=True)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported')})
    def test_network_detail_new(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id) \
            .MultipleTimes().AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'network-ip-availability') \
            .AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning') \
            .AndReturn(mac_learning)

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        self.mox.ReplayAll()
        url = urlunquote(reverse('horizon:admin:networks:detail',
                                 args=[network_id]))

        res = self.client.get(url)
        network = res.context['network']
        self.assertEqual(self.networks.first().name_or_id, network.name_or_id)
        self.assertEqual(self.networks.first().status_label,
                         network.status_label)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')

    def _test_network_detail_subnets_tab(self, mac_learning=False):
        network_id = self.networks.first().id
        ip_availability = self.ip_availability.get()
        api.neutron.show_network_ip_availability(IsA(http.HttpRequest),
                                                 network_id).\
            MultipleTimes().AndReturn(ip_availability)
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        self.mox.ReplayAll()
        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                         args=[network_id]))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_ports_tab(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)

        self.mox.ReplayAll()
        url = reverse('horizon:admin:networks:ports_tab',
                      args=[network_id])
        res = self.client.get(urlunquote(url))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        ports = res.context['ports_table'].data
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_agents_tab(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'network-ip-availability') \
            .AndReturn(True)

        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id)\
            .AndReturn(self.agents.list())
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        self.mox.ReplayAll()
        url = reverse('horizon:admin:networks:agents_tab', args=[network_id])
        res = self.client.get(urlunquote(url))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        result_agents = res.context['agents_table'].data
        expected_agents = self.agents.list()

        self.assertItemsEqual(result_agents, expected_agents)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_subnets_tab_network_exception(self):
        self._test_network_detail_subnets_tab_network_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_network_exception_with_mac_learning(self):
        self._test_network_detail_subnets_tab_network_exception(
            mac_learning=True)

    def _test_network_detail_subnets_tab_network_exception(self,
                                                           mac_learning=False):
        network_id = self.networks.first().id
        ip_availability = self.ip_availability.get()
        api.neutron.show_network_ip_availability(IsA(http.HttpRequest),
                                                 network_id).\
            MultipleTimes().AndReturn(ip_availability)
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)

        self.mox.ReplayAll()

        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                                 args=[network_id]))
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported')})
    def test_network_detail_subnets_tab_subnet_exception(self):
        self._test_network_detail_subnets_tab_subnet_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_subnets_tab_subnet_exception_w_mac_learning(self):
        self._test_network_detail_subnets_tab_subnet_exception(
            mac_learning=True)

    def _test_network_detail_subnets_tab_subnet_exception(self,
                                                          mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
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
        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                         args=[network_id]))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertEqual(len(subnets), 0)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_port_exception(self):
        self._test_network_detail_subnets_tab_port_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_subnets_tab_port_exception_with_mac_learning(self):
        self._test_network_detail_subnets_tab_port_exception(mac_learning=True)

    def _test_network_detail_subnets_tab_port_exception(self,
                                                        mac_learning=False):
        network_id = self.networks.first().id
        ip_availability = self.ip_availability.get()
        api.neutron.show_network_ip_availability(IsA(http.HttpRequest),
                                                 network_id). \
            MultipleTimes().AndReturn(ip_availability)
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)

        self.mox.ReplayAll()
        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                         args=[network_id]))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_get(self):
        tenants = self.tenants.list()
        api.keystone.tenant_list(IsA(
            http.HttpRequest)).AndReturn([tenants, False])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            AndReturn(True)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_workflow_base.html')

    @test.create_stubs({api.neutron: ('network_create',
                                      'is_extension_supported',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': True,
                  'provider:network_type': 'local',
                  'with_subnet': False}
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            MultipleTimes().AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
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
                                      'subnet_create',
                                      'is_extension_supported',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_with_subnet(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': True,
                  'provider:network_type': 'local',
                  'with_subnet': True}

        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])

        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            MultipleTimes().AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest), **params)\
            .AndReturn(network)
        self.mox.ReplayAll()

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

    @test.create_stubs({api.neutron: ('network_create',
                                      'is_extension_supported',
                                      'subnetpool_list'),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_network_exception(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        params = {'name': network.name,
                  'tenant_id': tenant_id,
                  'admin_state_up': network.admin_state_up,
                  'router:external': True,
                  'shared': False,
                  'provider:network_type': 'local',
                  'with_subnet': False}
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            MultipleTimes().AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
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

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_vlan_segmentation_id_invalid(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        api.keystone.tenant_list(
            IsA(http.HttpRequest)
        ).MultipleTimes().AndReturn([tenants, False])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider')\
            .MultipleTimes().AndReturn(True)

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

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_gre_segmentation_id_invalid(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()

        api.keystone.tenant_list(
            IsA(http.HttpRequest)
        ).MultipleTimes().AndReturn([tenants, False])

        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            MultipleTimes().AndReturn(True)
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
        self.assertContains(res, "1 through %s" % ((2 ** 32) - 1))

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'segmentation_id_range': {'vxlan': [10, 20]}})
    def test_network_create_vxlan_segmentation_id_custom(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        api.keystone.tenant_list(
            IsA(http.HttpRequest)
        ).MultipleTimes().AndReturn([tenants, False])

        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider')\
            .MultipleTimes().AndReturn(True)

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

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'supported_provider_types': []})
    def test_network_create_no_provider_types(self):
        tenants = self.tenants.list()

        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            AndReturn(True)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_workflow_base.html')
        self.assertContains(
            res,
            '<input type="hidden" name="network_type" id="id_network_type" />',
            html=True)

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'supported_provider_types': ['local', 'flat', 'gre']})
    def test_network_create_unsupported_provider_types(self):
        tenants = self.tenants.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            AndReturn(True)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_workflow_base.html')
        network_type = res.context['form'].fields['network_type']
        self.assertListEqual(list(network_type.choices), [('local', 'Local'),
                                                          ('flat', 'Flat'),
                                                          ('gre', 'GRE')])

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id,
                                expand_subnet=False).AndReturn(network)

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
        api.neutron.network_get(IsA(http.HttpRequest), network.id,
                                expand_subnet=False).AndReturn(network)
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
        api.neutron.network_get(IsA(http.HttpRequest), network.id,
                                expand_subnet=False).AndReturn(network)
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

    @test.create_stubs({api.neutron: ('is_extension_supported',)})
    @test.update_settings(FILTER_DATA_FIRST={'admin.networks': True})
    def test_networks_list_with_admin_filter_first(self):
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'dhcp_agent_scheduler').AndReturn(True)
        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:admin:networks:index'))
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, [])

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_without_physical_networks(self):
        tenants = self.tenants.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            AndReturn(True)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)
        physical_network = res.context['form'].fields['physical_network']
        self.assertEqual(type(physical_network), forms.CharField)

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'physical_networks': ['default', 'test']})
    def test_network_create_with_physical_networks(self):
        tenants = self.tenants.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).AndReturn([tenants,
                                                                   False])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'provider').\
            AndReturn(True)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:create')
        res = self.client.get(url)
        physical_network = res.context['form'].fields['physical_network']
        self.assertEqual(type(physical_network), forms.ThemableChoiceField)
        self.assertListEqual(list(physical_network.choices),
                             [('default', 'default'), ('test', 'test')])
