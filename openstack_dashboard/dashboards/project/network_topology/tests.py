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
import django.test

from mox3.mox import IsA  # noqa
from oslo_serialization import jsonutils

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.network_topology.views import \
    TranslationHelper
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

JSON_URL = reverse('horizon:project:network_topology:json')
INDEX_URL = reverse('horizon:project:network_topology:index')


class NetworkTopologyTests(test.TestCase):
    trans = TranslationHelper()

    @test.create_stubs({api.nova: ('server_list',),
                        api.neutron: ('network_list_for_tenant',
                                      'network_list',
                                      'router_list',
                                      'port_list')})
    def test_json_view(self):
        self._test_json_view()

    @django.test.utils.override_settings(
        OPENSTACK_NEUTRON_NETWORK={'enable_router': False})
    @test.create_stubs({api.nova: ('server_list',),
                        api.neutron: ('network_list_for_tenant',
                                      'port_list')})
    def test_json_view_router_disabled(self):
        self._test_json_view(router_enable=False)

    def _test_json_view(self, router_enable=True):
        api.nova.server_list(
            IsA(http.HttpRequest)).AndReturn([self.servers.list(), False])
        tenant_networks = [net for net in self.networks.list()
                           if not net['router:external']]
        external_networks = [net for net in self.networks.list()
                             if net['router:external']]
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest),
            self.tenant.id).AndReturn(tenant_networks)
        if router_enable:
            api.neutron.network_list(
                IsA(http.HttpRequest),
                **{'router:external': True}).AndReturn(external_networks)

        # router1 : gateway port not in the port list
        # router2 : no gateway port
        # router3 : gateway port included in port list
        routers = self.routers.list() + self.routers_with_rules.list()
        if router_enable:
            api.neutron.router_list(
                IsA(http.HttpRequest),
                tenant_id=self.tenant.id).AndReturn(routers)
        api.neutron.port_list(
            IsA(http.HttpRequest)).AndReturn(self.ports.list())

        self.mox.ReplayAll()

        res = self.client.get(JSON_URL)
        self.assertEqual('text/json', res['Content-Type'])
        data = jsonutils.loads(res.content)

        # servers
        # result_server_urls = [(server['id'], server['url'])
        #                       for server in data['servers']]
        expect_server_urls = [
            {'id': server.id,
             'name': server.name,
             'status': self.trans.instance[server.status],
             'original_status': server.status,
             'task': None,
             'url': '/project/instances/%s/' % server.id}
            for server in self.servers.list()]
        self.assertEqual(expect_server_urls, data['servers'])

        # routers
        # result_router_urls = [(router['id'], router['url'])
        #                       for router in data['routers']]
        if router_enable:
            expect_router_urls = [
                {'id': router.id,
                 'external_gateway_info':
                 router.external_gateway_info,
                 'name': router.name,
                 'status': self.trans.router[router.status],
                 'original_status': router.status,
                 'url': '/project/routers/%s/' % router.id}
                for router in routers]
            self.assertEqual(expect_router_urls, data['routers'])
        else:
            self.assertFalse(data['routers'])

        # networks
        expect_net_urls = []
        if router_enable:
            expect_net_urls += [{'id': net.id,
                                 'url': '/project/networks/%s/detail' % net.id,
                                 'name': net.name,
                                 'router:external': net.router__external,
                                 'status': self.trans.network[net.status],
                                 'original_status': net.status,
                                 'subnets': []}
                                for net in external_networks]
        expect_net_urls += [{'id': net.id,
                             'url': '/project/networks/%s/detail' % net.id,
                             'name': net.name,
                             'router:external': net.router__external,
                             'status': self.trans.network[net.status],
                             'original_status': net.status,
                             'subnets': [{'cidr': subnet.cidr,
                                          'id': subnet.id,
                                          'url':
                                          '/project/networks/subnets/%s/detail'
                                          % subnet.id}
                                         for subnet in net.subnets]}
                            for net in tenant_networks]
        for exp_net in expect_net_urls:
            if exp_net['url'] is None:
                del exp_net['url']
        self.assertEqual(expect_net_urls, data['networks'])

        # ports
        expect_port_urls = [
            {'id': port.id,
             'device_id': port.device_id,
             'device_owner': port.device_owner,
             'fixed_ips': port.fixed_ips,
             'network_id': port.network_id,
             'status': self.trans.port[port.status],
             'original_status': port.status,
             'url': '/project/networks/ports/%s/detail' % port.id}
            for port in self.ports.list()]
        if router_enable:
            # fake port for router1 gateway (router1 on ext_net)
            router1 = routers[0]
            ext_net = external_networks[0]
            expect_port_urls.append(
                {'id': 'gateway%s' % ext_net.id,
                 'device_id': router1.id,
                 'network_id': ext_net.id,
                 'fixed_ips': []})
        self.assertEqual(expect_port_urls, data['ports'])


class NetworkTopologyCreateTests(test.TestCase):

    def _test_new_button_disabled_when_quota_exceeded(
            self, expected_string, networks_quota=10,
            routers_quota=10, instances_quota=10):
        quota_data = self.quota_usages.first()
        quota_data['networks']['available'] = networks_quota
        quota_data['routers']['available'] = routers_quota
        quota_data['instances']['available'] = instances_quota

        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/network_topology/index.html')

        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The create button is not disabled")

    @test.create_stubs({quotas: ('tenant_quota_usages',)})
    def test_create_network_button_disabled_when_quota_exceeded(self):
        url = reverse('horizon:project:network_topology:createnetwork')
        classes = 'btn btn-default btn-sm ajax-modal'
        link_name = "Create Network (Quota exceeded)"
        expected_string = "<a href='%s' class='%s disabled' "\
            "id='networks__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, classes, link_name)

        self._test_new_button_disabled_when_quota_exceeded(
            expected_string, networks_quota=0)

    @test.create_stubs({quotas: ('tenant_quota_usages',)})
    def test_create_router_button_disabled_when_quota_exceeded(self):
        url = reverse('horizon:project:network_topology:createrouter')
        classes = 'btn btn-default btn-sm ajax-modal'
        link_name = "Create Router (Quota exceeded)"
        expected_string = "<a href='%s' class='%s disabled' "\
            "id='Routers__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, classes, link_name)

        self._test_new_button_disabled_when_quota_exceeded(
            expected_string, routers_quota=0)

    @test.create_stubs({quotas: ('tenant_quota_usages',)})
    def test_launch_instance_button_disabled_when_quota_exceeded(self):
        url = reverse('horizon:project:network_topology:launchinstance')
        classes = 'btn btn-default btn-sm btn-launch ajax-modal'
        link_name = "Launch Instance (Quota exceeded)"
        expected_string = "<a href='%s' class='%s disabled' "\
            "id='instances__action_launch'>" \
            "<span class='fa fa-cloud-upload'></span>%s</a>" \
            % (url, classes, link_name)

        self._test_new_button_disabled_when_quota_exceeded(
            expected_string, instances_quota=0)
