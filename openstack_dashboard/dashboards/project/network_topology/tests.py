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

import django.test
from django.urls import reverse

import mock
from oslo_serialization import jsonutils

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.network_topology import views
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

JSON_URL = reverse('horizon:project:network_topology:json')
INDEX_URL = reverse('horizon:project:network_topology:index')


class NetworkTopologyTests(test.TestCase):
    trans = views.TranslationHelper()

    @test.create_mocks({api.nova: ('server_list',),
                        api.neutron: ('network_list_for_tenant',
                                      'network_list',
                                      'router_list',
                                      'port_list')})
    def test_json_view(self):
        self._test_json_view()

    @django.test.utils.override_settings(
        OPENSTACK_NEUTRON_NETWORK={'enable_router': False})
    @test.create_mocks({api.nova: ('server_list',),
                        api.neutron: ('network_list_for_tenant',
                                      'port_list')})
    def test_json_view_router_disabled(self):
        self._test_json_view(router_enable=False)

    @django.test.utils.override_settings(CONSOLE_TYPE=None)
    @test.create_mocks({api.nova: ('server_list',),
                        api.neutron: ('network_list_for_tenant',
                                      'network_list',
                                      'router_list',
                                      'port_list')})
    def test_json_view_console_disabled(self):
        self._test_json_view(with_console=False)

    def _test_json_view(self, router_enable=True, with_console=True):
        self.mock_server_list.return_value = [self.servers.list(), False]

        tenant_networks = [net for net in self.networks.list()
                           if not net['router:external']]
        external_networks = [net for net in self.networks.list()
                             if net['router:external']]
        self.mock_network_list_for_tenant.return_value = tenant_networks

        # router1 : gateway port not in the port list
        # router2 : no gateway port
        # router3 : gateway port included in port list
        routers = self.routers.list() + self.routers_with_rules.list()
        if router_enable:
            self.mock_router_list.return_value = routers
            self.mock_network_list.return_value = external_networks
        self.mock_port_list.return_value = self.ports.list()

        res = self.client.get(JSON_URL)

        self.assertEqual('text/json', res['Content-Type'])
        data = jsonutils.loads(res.content)

        # servers
        expect_server_urls = []
        for server in self.servers.list():
            expect_server = {
                'id': server.id,
                'name': server.name,
                'status': server.status.title(),
                'original_status': server.status,
                'task': None,
                'url': '/project/instances/%s/' % server.id
            }
            if server.status != 'BUILD' and with_console:
                expect_server['console'] = 'auto_console'
            expect_server_urls.append(expect_server)
        self.assertEqual(expect_server_urls, data['servers'])

        # routers
        if router_enable:
            expect_router_urls = [
                {'id': router.id,
                 'external_gateway_info':
                 router.external_gateway_info,
                 'name': router.name,
                 'status': router.status.title(),
                 'original_status': router.status,
                 'url': '/project/routers/%s/' % router.id}
                for router in routers]
            self.assertEqual(expect_router_urls, data['routers'])
        else:
            self.assertFalse(data['routers'])

        # networks
        expect_net_urls = []
        if router_enable:
            expect_net_urls += [{
                'id': net.id,
                'url': '/project/networks/%s/detail' % net.id,
                'name': net.name,
                'router:external': net.router__external,
                'status': net.status.title(),
                'original_status': net.status,
                'subnets': [{
                    'cidr': snet.cidr,
                    'id': snet.id,
                    'url': '/project/networks/subnets/%s/detail' % snet.id}
                    for snet in net.subnets]}
                for net in external_networks]
        expect_net_urls.extend([{
            'id': net.id,
            'url': '/project/networks/%s/detail' % net.id,
            'name': net.name,
            'router:external': net.router__external,
            'status': net.status.title(),
            'allow_delete_subnet': True,
            'original_status': net.status,
            'subnets': [{
                'cidr': subnet.cidr,
                'id': subnet.id,
                'url': '/project/networks/subnets/%s/detail' % subnet.id}
                for subnet in net.subnets]}
            for net in tenant_networks])
        for exp_net in expect_net_urls:
            if exp_net['url'] is None:
                del exp_net['url']
        self.assertEqual(expect_net_urls, data['networks'])

        valid_network_ids = [net.id for net in tenant_networks]
        if router_enable:
            valid_network_ids = [net.id for net in self.networks.list()]
        # ports
        expect_port_urls = [
            {'id': port.id,
             'device_id': port.device_id,
             'device_owner': port.device_owner,
             'fixed_ips': port.fixed_ips,
             'network_id': port.network_id,
             'status': port.status.title(),
             'original_status': port.status,
             'url': '/project/networks/ports/%s/detail' % port.id}
            for port in self.ports.list()
            if port.network_id in valid_network_ids]
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

        self.mock_server_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_network_list_for_tenant.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id,
            include_pre_auto_allocate=False)
        if router_enable:
            self.mock_router_list.assert_called_once_with(
                test.IsHttpRequest(), tenant_id=self.tenant.id)
            self.mock_network_list.assert_called_once_with(
                test.IsHttpRequest(), **{'router:external': True})
        self.mock_port_list.assert_called_once_with(
            test.IsHttpRequest())


class NetworkTopologyCreateTests(test.TestCase):

    def _test_new_button_disabled_when_quota_exceeded(
            self, expected_string,
            networks_quota=10, routers_quota=10, instances_quota=10):
        quota_data = self.quota_usages.first()
        quota_data['network']['available'] = networks_quota
        quota_data['router']['available'] = routers_quota
        quota_data['instances']['available'] = instances_quota

        self.mock_tenant_quota_usages.return_value = quota_data

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/network_topology/index.html')

        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The create button is not disabled")

        self.mock_tenant_quota_usages.assert_has_calls([
            mock.call(test.IsHttpRequest(), targets=('instances', )),
            mock.call(test.IsHttpRequest(), targets=('network', )),
            mock.call(test.IsHttpRequest(), targets=('router', )),
        ] * 3)

    @test.create_mocks({quotas: ('tenant_quota_usages',)})
    def test_create_network_button_disabled_when_quota_exceeded(self):
        url = reverse('horizon:project:network_topology:createnetwork')
        classes = 'btn btn-default ajax-modal'
        link_name = "Create Network (Quota exceeded)"
        expected_string = "<a href='%s' class='%s disabled' "\
            "id='networks__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, classes, link_name)

        self._test_new_button_disabled_when_quota_exceeded(expected_string,
                                                           networks_quota=0)

    @test.create_mocks({quotas: ('tenant_quota_usages',)})
    def test_create_router_button_disabled_when_quota_exceeded(self):
        url = reverse('horizon:project:network_topology:createrouter')
        classes = 'btn btn-default ajax-modal'
        link_name = "Create Router (Quota exceeded)"
        expected_string = "<a href='%s' class='%s disabled' "\
            "id='Routers__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, classes, link_name)

        self._test_new_button_disabled_when_quota_exceeded(expected_string,
                                                           routers_quota=0)

    @test.update_settings(LAUNCH_INSTANCE_LEGACY_ENABLED=True)
    @test.create_mocks({quotas: ('tenant_quota_usages',)})
    def test_launch_instance_button_disabled_when_quota_exceeded(self):
        url = reverse('horizon:project:network_topology:launchinstance')
        classes = 'btn btn-default btn-launch ajax-modal'
        link_name = "Launch Instance (Quota exceeded)"
        expected_string = "<a href='%s' class='%s disabled' "\
            "id='instances__action_launch'>" \
            "<span class='fa fa-cloud-upload'></span>%s</a>" \
            % (url, classes, link_name)

        self._test_new_button_disabled_when_quota_exceeded(expected_string,
                                                           instances_quota=0)
