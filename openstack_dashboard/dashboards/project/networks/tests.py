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
from django.utils.html import escape

from horizon.workflows import views

from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import tables\
    as networks_tables
from openstack_dashboard.dashboards.project.networks import workflows
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:networks:index')


def form_data_subnet(subnet,
                     name=None, cidr=None, ip_version=None,
                     gateway_ip='', enable_dhcp=None,
                     allocation_pools=None,
                     dns_nameservers=None,
                     host_routes=None):
    def get_value(value, default):
        return default if value is None else value

    data = {}
    data['subnet_name'] = get_value(name, subnet.name)
    data['cidr'] = get_value(cidr, subnet.cidr)
    data['ip_version'] = get_value(ip_version, subnet.ip_version)

    gateway_ip = subnet.gateway_ip if gateway_ip == '' else gateway_ip
    data['gateway_ip'] = gateway_ip or ''
    data['no_gateway'] = (gateway_ip is None)

    data['enable_dhcp'] = get_value(enable_dhcp, subnet.enable_dhcp)
    if data['ip_version'] == 6:
        data['ipv6_modes'] = subnet.ipv6_modes

    pools = get_value(allocation_pools, subnet.allocation_pools)
    data['allocation_pools'] = _str_allocation_pools(pools)
    nameservers = get_value(dns_nameservers, subnet.dns_nameservers)
    data['dns_nameservers'] = _str_dns_nameservers(nameservers)
    routes = get_value(host_routes, subnet.host_routes)
    data['host_routes'] = _str_host_routes(routes)

    return data


def form_data_no_subnet():
    return {'subnet_name': '',
            'cidr': '',
            'ip_version': 4,
            'gateway_ip': '',
            'no_gateway': False,
            'enable_dhcp': True,
            'allocation_pools': '',
            'dns_nameservers': '',
            'host_routes': ''}


def _str_allocation_pools(allocation_pools):
    if isinstance(allocation_pools, str):
        return allocation_pools
    return '\n'.join(['%s,%s' % (pool['start'], pool['end'])
                      for pool in allocation_pools])


def _str_dns_nameservers(dns_nameservers):
    if isinstance(dns_nameservers, str):
        return dns_nameservers
    return '\n'.join(dns_nameservers)


def _str_host_routes(host_routes):
    if isinstance(host_routes, str):
        return host_routes
    return '\n'.join(['%s,%s' % (route['destination'], route['nexthop'])
                      for route in host_routes])


class NetworkStubMixin(object):
    def _stub_net_list(self):
        all_networks = self.networks.list()
        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn([
                network for network in all_networks
                if network['tenant_id'] == self.tenant.id
            ])
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([
                network for network in all_networks
                if network.get('shared')
            ])
        api.neutron.network_list(
            IsA(http.HttpRequest),
            **{'router:external': True}).AndReturn([
                network for network in all_networks
                if network.get('router:external')
            ])


class NetworkTests(test.TestCase, NetworkStubMixin):

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        quota_data = self.quota_usages.first()
        quota_data['networks']['available'] = 5
        quota_data['subnets']['available'] = 5
        self._stub_net_list()
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/networks/index.html')
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index_network_list_exception(self):
        quota_data = self.neutron_quota_usages.first()
        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).MultipleTimes().AndRaise(self.exceptions.neutron)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/networks/index.html')
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail(self):
        self._test_network_detail()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_with_mac_learning(self):
        self._test_network_detail(mac_learning=True)

    def _test_network_detail(self, mac_learning=False):
        quota_data = self.neutron_quota_usages.first()
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_network_detail_network_exception(self):
        self._test_network_detail_network_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_network_detail_network_exception_with_mac_learning(self):
        self._test_network_detail_network_exception(mac_learning=True)

    def _test_network_detail_network_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:detail', args=[network_id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_subnet_exception(self):
        self._test_network_detail_subnet_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_subnet_exception_with_mac_learning(self):
        self._test_network_detail_subnet_exception(mac_learning=True)

    def _test_network_detail_subnet_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['networks']['available'] = 5
        quota_data['subnets']['available'] = 5
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertEqual(len(subnets), 0)
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_port_exception(self):
        self._test_network_detail_port_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_port_exception_with_mac_learning(self):
        self._test_network_detail_port_exception(mac_learning=True)

    def _test_network_detail_port_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['subnets']['available'] = 5
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        # Called from SubnetTable
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertEqual(len(ports), 0)

    @test.create_stubs({api.neutron: ('profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_network_create_get(self,
                                test_with_profile=False):
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:create')
        res = self.client.get(url)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.CreateNetwork.name)
        expected_objs = ['<CreateNetworkInfo: createnetworkinfoaction>',
                         '<CreateSubnetInfo: createsubnetinfoaction>',
                         '<CreateSubnetDetail: createsubnetdetailaction>']
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_get_with_profile(self):
        self.test_network_create_get(test_with_profile=True)

    @test.create_stubs({api.neutron: ('network_create',
                                      'profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_network_create_post(self,
                                 test_with_profile=False):
        network = self.networks.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up,
                  'shared': False}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     # subnet
                     'with_subnet': False}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_create',
                                      'profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_network_create_post_with_shared(self, test_with_profile=False):
        network = self.networks.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up,
                  'shared': True}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'shared': True,
                     # subnet
                     'with_subnet': False}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_with_profile(self):
        self.test_network_create_post(test_with_profile=True)

    @test.create_stubs({api.neutron: ('network_create',
                                      'subnet_create',
                                      'profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_network_create_post_with_subnet(self,
                                             test_with_profile=False,
                                             test_with_ipv6=True):
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up,
                  'shared': False}
        subnet_params = {'network_id': network.id,
                         'name': subnet.name,
                         'cidr': subnet.cidr,
                         'ip_version': subnet.ip_version,
                         'gateway_ip': subnet.gateway_ip,
                         'enable_dhcp': subnet.enable_dhcp}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        if not test_with_ipv6:
            subnet.ip_version = 4
            subnet_params['ip_version'] = subnet.ip_version
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  **subnet_params).AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_with_subnet_w_profile(self):
        self.test_network_create_post_with_subnet(test_with_profile=True)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_ipv6': False})
    def test_create_network_with_ipv6_disabled(self):
        self.test_network_create_post_with_subnet(test_with_ipv6=False)

    @test.create_stubs({api.neutron: ('network_create',
                                      'profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_network_create_post_network_exception(self,
                                                   test_with_profile=False):
        network = self.networks.first()
        params = {'name': network.name,
                  'shared': False,
                  'admin_state_up': network.admin_state_up}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     # subnet
                     'shared': False,
                     'with_subnet': False}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_nw_exception_w_profile(self):
        self.test_network_create_post_network_exception(
            test_with_profile=True)

    @test.create_stubs({api.neutron: ('network_create',
                                      'profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list')})
    def test_network_create_post_with_subnet_network_exception(
        self,
        test_with_profile=False,
        test_with_subnetpool=False,
    ):
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'shared': False,
                  'admin_state_up': network.admin_state_up}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_nw_create_post_w_subnet_nw_exception_w_profile(self):
        self.test_network_create_post_with_subnet_network_exception(
            test_with_profile=True)

    @test.create_stubs({api.neutron: ('network_create',
                                      'network_delete',
                                      'subnet_create',
                                      'profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_network_create_post_with_subnet_subnet_exception(
        self,
        test_with_profile=False,
    ):
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'shared': False,
                  'admin_state_up': network.admin_state_up}
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            params['net_profile_id'] = net_profile_id
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.network_delete(IsA(http.HttpRequest),
                                   network.id)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_nw_create_post_w_subnet_subnet_exception_w_profile(self):
        self.test_network_create_post_with_subnet_subnet_exception(
            test_with_profile=True)

    @test.create_stubs({api.neutron: ('profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_network_create_post_with_subnet_nocidr(self,
                                                    test_with_profile=False,
                                                    test_with_snpool=False):
        network = self.networks.first()
        subnet = self.subnets.first()
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'shared': False,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        if test_with_snpool:
            form_data['subnetpool_id'] = ''
            form_data['prefixlen'] = ''
        form_data.update(form_data_subnet(subnet, cidr='',
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, escape('Specify "Network Address" or '
                                        'clear "Create Subnet" checkbox'
                                        ' in previous step.'))

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_nw_create_post_w_subnet_no_cidr_w_profile(self):
        self.test_network_create_post_with_subnet_nocidr(
            test_with_profile=True)

    def test_network_create_post_with_subnet_nocidr_nosubnetpool(self):
        self.test_network_create_post_with_subnet_nocidr(
            test_with_snpool=True)

    @test.create_stubs({api.neutron: ('profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_network_create_post_with_subnet_cidr_without_mask(
        self,
        test_with_profile=False,
        test_with_subnetpool=False,
    ):
        network = self.networks.first()
        subnet = self.subnets.first()
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'shared': False,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        if test_with_subnetpool:
            subnetpool = self.subnetpools.first()
            form_data['subnetpool'] = subnetpool.id
            form_data['prefixlen'] = subnetpool.default_prefixlen
        form_data.update(form_data_subnet(subnet, cidr='10.0.0.0',
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = "The subnet in the Network Address is too small (/32)."
        self.assertContains(res, expected_msg)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_nw_create_post_w_subnet_cidr_without_mask_w_profile(self):
        self.test_network_create_post_with_subnet_cidr_without_mask(
            test_with_profile=True)

    def test_network_create_post_with_subnet_cidr_without_mask_w_snpool(self):
        self.test_network_create_post_with_subnet_cidr_without_mask(
            test_with_subnetpool=True)

    @test.create_stubs({api.neutron: ('profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_network_create_post_with_subnet_cidr_inconsistent(
        self,
        test_with_profile=False,
        test_with_subnetpool=False
    ):
        network = self.networks.first()
        subnet = self.subnets.first()
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)

        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = {'net_name': network.name,
                     'shared': False,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        if test_with_subnetpool:
            subnetpool = self.subnetpools.first()
            form_data['subnetpool'] = subnetpool.id
            form_data['prefixlen'] = subnetpool.default_prefixlen
        form_data.update(form_data_subnet(subnet, cidr=cidr,
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_with_subnet_cidr_inconsistent_w_profile(self):
        self.test_network_create_post_with_subnet_cidr_inconsistent(
            test_with_profile=True)

    def test_network_create_post_with_subnet_cidr_inconsistent_w_snpool(self):
        self.test_network_create_post_with_subnet_cidr_inconsistent(
            test_with_subnetpool=True)

    @test.create_stubs({api.neutron: ('profile_list',
                                      'is_extension_supported',
                                      'subnetpool_list',)})
    def test_network_create_post_with_subnet_gw_inconsistent(
        self,
        test_with_profile=False,
        test_with_subnetpool=False,
    ):
        network = self.networks.first()
        subnet = self.subnets.first()
        if test_with_profile:
            net_profiles = self.net_profiles.list()
            net_profile_id = self.net_profiles.first().id
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)

        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'subnet_allocation').\
            AndReturn(True)
        api.neutron.subnetpool_list(IsA(http.HttpRequest)).\
            AndReturn(self.subnetpools.list())
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = {'net_name': network.name,
                     'shared': False,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        if test_with_profile:
            form_data['net_profile_id'] = net_profile_id
        if test_with_subnetpool:
            subnetpool = self.subnetpools.first()
            form_data['subnetpool'] = subnetpool.id
            form_data['prefixlen'] = subnetpool.default_prefixlen
        form_data.update(form_data_subnet(subnet, gateway_ip=gateway_ip,
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_network_create_post_with_subnet_gw_inconsistent_w_profile(self):
        self.test_network_create_post_with_subnet_gw_inconsistent(
            test_with_profile=True)

    def test_network_create_post_with_subnet_gw_inconsistent_w_snpool(self):
        self.test_network_create_post_with_subnet_gw_inconsistent(
            test_with_subnetpool=True)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/update.html')

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()
        api.neutron.network_update(IsA(http.HttpRequest), network.id,
                                   name=network.name,
                                   admin_state_up=network.admin_state_up,
                                   shared=network.shared)\
            .AndReturn(network)
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'shared': False,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        api.neutron.network_update(IsA(http.HttpRequest), network.id,
                                   name=network.name,
                                   admin_state_up=network.admin_state_up,
                                   shared=False)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'shared': False,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'network_list',
                                      'network_delete')})
    def test_delete_network_no_subnet(self):
        network = self.networks.first()
        network.subnets = []
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id,
                                expand_subnet=False)\
            .AndReturn(network)
        self._stub_net_list()
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'network_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_with_subnet(self):
        network = self.networks.first()
        network.subnets = [subnet.id for subnet in network.subnets]
        subnet_id = network.subnets[0]
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id,
                                expand_subnet=False)\
            .AndReturn(network)
        self._stub_net_list()
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet_id)
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'network_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_exception(self):
        network = self.networks.first()
        network.subnets = [subnet.id for subnet in network.subnets]
        subnet_id = network.subnets[0]
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id,
                                expand_subnet=False)\
            .AndReturn(network)
        self._stub_net_list()
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet_id)
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)


class NetworkViewTests(test.TestCase, NetworkStubMixin):

    def _test_create_button_shown_when_quota_disabled(
            self,
            find_button_fn):
        # if quota_data doesnt contain a networks|subnets|routers key or
        # these keys are empty dicts, its disabled
        quota_data = self.neutron_quota_usages.first()

        quota_data['networks'].pop('available')
        quota_data['subnets'].pop('available')

        self._stub_net_list()
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/networks/index.html')

        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

        button = find_button_fn(res)
        self.assertFalse('disabled' in button.classes,
                         "The create button should not be disabled")
        return button

    def _test_create_button_disabled_when_quota_exceeded(
            self, find_button_fn, network_quota=5, subnet_quota=5, ):

        quota_data = self.neutron_quota_usages.first()

        quota_data['networks']['available'] = network_quota
        quota_data['subnets']['available'] = subnet_quota

        self._stub_net_list()
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/networks/index.html')

        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

        button = find_button_fn(res)
        self.assertTrue('disabled' in button.classes,
                        "The create button should be disabled")
        return button

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_create_button_disabled_when_quota_exceeded_index(self):
        networks_tables.CreateNetwork()

        def _find_net_button(res):
            return self.getAndAssertTableAction(res, 'networks', 'create')
        self._test_create_button_disabled_when_quota_exceeded(_find_net_button,
                                                              network_quota=0)

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_subnet_create_button_disabled_when_quota_exceeded_index(self):
        network_id = self.networks.first().id
        networks_tables.CreateSubnet()

        def _find_subnet_button(res):
            return self.getAndAssertTableRowAction(res, 'networks',
                                                   'subnet', network_id)

        self._test_create_button_disabled_when_quota_exceeded(
            _find_subnet_button, subnet_quota=0)

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_create_button_shown_when_quota_disabled_index(self):
        # if quota_data doesnt contain a networks["available"] key its disabled
        networks_tables.CreateNetwork()
        self._test_create_button_shown_when_quota_disabled(
            lambda res: self.getAndAssertTableAction(res, 'networks', 'create')
        )

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_subnet_create_button_shown_when_quota_disabled_index(self):
        # if quota_data doesnt contain a subnets["available"] key, its disabled
        network_id = self.networks.first().id

        def _find_subnet_button(res):
            return self.getAndAssertTableRowAction(res, 'networks',
                                                   'subnet', network_id)

        self._test_create_button_shown_when_quota_disabled(_find_subnet_button)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_subnet_create_button_disabled_when_quota_exceeded_detail(self):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['subnets']['available'] = 0

        api.neutron.network_get(
            IsA(http.HttpRequest), network_id)\
            .MultipleTimes().AndReturn(self.networks.first())
        api.neutron.subnet_list(
            IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn(self.subnets.list())
        api.neutron.port_list(
            IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'mac-learning')\
            .AndReturn(False)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))
        self.assertTemplateUsed(res, 'project/networks/detail.html')

        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, self.subnets.list())

        create_action = self.getAndAssertTableAction(res, 'subnets', 'create')
        self.assertTrue('disabled' in create_action.classes,
                        'The create button should be disabled')

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_attributes(self):
        create_action = self._test_create_button_shown_when_quota_disabled(
            lambda res: self.getAndAssertTableAction(res, 'networks', 'create')
        )

        self.assertEqual(set(['ajax-modal']), set(create_action.classes))
        self.assertEqual('horizon:project:networks:create', create_action.url)
        self.assertEqual('Create Network',
                         six.text_type(create_action.verbose_name))
        self.assertEqual((('network', 'create_network'),),
                         create_action.policy_rules)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_subnet_button_attributes(self):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['subnets']['available'] = 1

        api.neutron.network_get(
            IsA(http.HttpRequest), network_id)\
            .MultipleTimes().AndReturn(self.networks.first())
        api.neutron.subnet_list(
            IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn(self.subnets.list())
        api.neutron.port_list(
            IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'mac-learning')\
            .AndReturn(False)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))
        self.assertTemplateUsed(res, 'project/networks/detail.html')

        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, self.subnets.list())

        create_action = self.getAndAssertTableAction(res, 'subnets', 'create')

        self.assertEqual(set(['ajax-modal']), set(create_action.classes))
        self.assertEqual('horizon:project:networks:addsubnet',
                         create_action.url)
        self.assertEqual('Create Subnet',
                         six.text_type(create_action.verbose_name))
        self.assertEqual((('network', 'create_subnet'),),
                         create_action.policy_rules)
