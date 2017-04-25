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

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import tests
from openstack_dashboard.test import helpers as test

DETAIL_URL = 'horizon:admin:networks:subnets:detail'

NETWORKS_INDEX_URL = reverse('horizon:admin:networks:index')
NETWORKS_DETAIL_URL = 'horizon:admin:networks:detail'


class NetworkSubnetTests(test.BaseAdminViewTests):

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_get',
                                      'is_extension_supported')})
    def test_subnet_detail(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .MultipleTimes().AndReturn(network)

        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)

        self.mox.ReplayAll()

        url = reverse(DETAIL_URL, args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

    @test.create_stubs({api.neutron: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        url = reverse(DETAIL_URL, args=[subnet.id])
        res = self.client.get(url)

        redir_url = NETWORKS_INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_subnet_create_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnets)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:createsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .MultipleTimes().AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .MultipleTimes().AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnets)
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
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[subnet.network_id])
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
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        # admin DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:project:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .MultipleTimes().AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnets)

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
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_subnet_create_post_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnets)

        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = tests.form_data_subnet(
            subnet, cidr=cidr, allocation_pools=[])
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_subnet_create_post_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnets)

        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = tests.form_data_subnet(subnet, gateway_ip=gateway_ip,
                                           allocation_pools=[])
        url = reverse('horizon:admin:networks:createsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnetpools.list())
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

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_subnet_update_post_gw_inconsistent(self):
        subnet = self.subnets.first()
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation')\
            .AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest))\
            .AndReturn(self.subnetpools.list())
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
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete(self):
        self._test_subnet_delete()

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete_with_mac_learning(self):
        self._test_subnet_delete(mac_learning=True)

    def _test_subnet_delete(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        ip_availability = self.ip_availability.get()
        api.neutron.show_network_ip_availability(IsA(http.HttpRequest),
                                                 network_id). \
            MultipleTimes().AndReturn(ip_availability)
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'network-ip-availability')\
            .MultipleTimes().AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete_exception(self):
        self._test_subnet_delete_exception()

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_subnet_delete_exception_with_mac_learning(self):
        self._test_subnet_delete_exception(mac_learning=True)

    def _test_subnet_delete_exception(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        ip_availability = self.ip_availability.get()
        api.neutron.show_network_ip_availability(IsA(http.HttpRequest),
                                                 network_id).\
            MultipleTimes().AndReturn(ip_availability)
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'network-ip-availability') \
            .MultipleTimes().AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_ip_availability_exception(self):
        self._test_network_detail_ip_availability_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'show_network_ip_availability',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_network_detail_ip_availability_exception_with_mac_learning(self):
        self._test_network_detail_ip_availability_exception(mac_learning=True)

    def _test_network_detail_ip_availability_exception(self,
                                                       mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.show_network_ip_availability(IsA(http.HttpRequest),
                                                 network_id).\
            MultipleTimes().AndRaise(self.exceptions.neutron)
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())

        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning') \
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'network-ip-availability').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .MultipleTimes().AndReturn(True)
        self.mox.ReplayAll()
        from django.utils.http import urlunquote
        url = urlunquote(reverse('horizon:admin:networks:subnets_tab',
                                 args=[network_id]))
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
