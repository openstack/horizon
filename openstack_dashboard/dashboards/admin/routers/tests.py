# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

import mock

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers import tests as r_test
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class RouterMixin(r_test.RouterMixin):

    support_l3_agent = True

    def _get_detail(self, router, extraroute=True):

        supported_extensions = {
            'extraroute': extraroute,
            'router_availability_zone': True,
            'l3_agent_scheduler': self.support_l3_agent,
        }

        def get_supported_extension(*args):
            alias = args[1]
            return supported_extensions[alias]

        self.mock_is_extension_supported.side_effect = get_supported_extension

        self.mock_router_get.return_value = router
        self.mock_port_list.return_value = [self.ports.first()]
        self._mock_external_network_get(router)
        if self.support_l3_agent:
            agent = self.agents.list()[1]
            self.mock_list_l3_agent_hosting_router.return_value = [agent]

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router.id]))
        return res

    def _check_get_detail(self, router, extraroute=True):
        super(RouterMixin, self)._check_get_detail(router, extraroute)
        self.mock_is_extension_supported.assert_any_call(
            test.IsHttpRequest(), 'l3_agent_scheduler')
        if self.support_l3_agent:
            self.mock_list_l3_agent_hosting_router.assert_called_once_with(
                test.IsHttpRequest(), router.id)
        else:
            self.mock_list_l3_agent_hosting_router.assert_not_called()


class RouterTests(RouterMixin, r_test.RouterTestCase, test.BaseAdminViewTests):
    DASHBOARD = 'admin'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        tenants = self.tenants.list()
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

        self.mock_router_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), "router_availability_zone")
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_index_router_list_exception(self):
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.side_effect = self.exceptions.neutron
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)
        self.mock_router_list.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), "router_availability_zone")

    @test.create_mocks({api.neutron: ('agent_list',
                                      'router_list_on_l3_agent',
                                      'network_list',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_list_by_l3_agent(self):
        tenants = self.tenants.list()
        quota_data = self.neutron_quota_usages.first()
        agent = self.agents.list()[1]
        self.mock_agent_list.return_value = [agent]
        self.mock_router_list_on_l3_agent.return_value = self.routers.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        l3_list_url = reverse('horizon:admin:routers:l3_agent_list',
                              args=[agent.id])
        res = self.client.get(l3_list_url)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

        self.mock_agent_list.assert_called_once_with(
            test.IsHttpRequest(), id=agent.id)
        self.mock_router_list_on_l3_agent.assert_called_once_with(
            test.IsHttpRequest(), agent.id, search_opts=None)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), "router_availability_zone")
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_set_external_network_empty(self):
        router = self.routers.first()
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.return_value = [router]
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self._mock_external_network_list(alter_ids=True)

        res = self.client.get(self.INDEX_URL)

        table_data = res.context['table'].data
        self.assertEqual(len(table_data), 1)
        self.assertIn('(Not Found)',
                      table_data[0]['external_gateway_info']['network'])
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertMessageCount(res, error=1)

        self.mock_router_list.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), "router_availability_zone")
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('list_l3_agent_hosting_router',)})
    def test_router_detail(self):
        super(RouterTests, self).test_router_detail()

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'port_list',
                                      'router_delete',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_router_delete(self):
        router = self.routers.first()
        tenants = self.tenants.list()
        quota_data = self.neutron_quota_usages.first()

        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self._mock_external_network_list(count=3)
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self.mock_port_list.return_value = []
        self.mock_router_delete.return_value = None

        res = self.client.get(self.INDEX_URL)

        formData = {'action': 'routers__delete__' + router.id}
        res = self.client.post(self.INDEX_URL, formData, follow=True)
        self.assertNoFormErrors(res)
        self.assertMessageCount(response=res, success=1)
        self.assertIn('Deleted Router: ' + router.name,
                      res.content.decode('utf-8'))

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_router_list, 3,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_list, 3,
            mock.call(test.IsHttpRequest()))
        self._check_mock_external_network_list(count=3)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 4,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 3,
            mock.call(test.IsHttpRequest(), 'router_availability_zone'))
        self.mock_port_list.assert_called_once_with(
            test.IsHttpRequest(), device_id=router.id, device_owner=mock.ANY)
        self.mock_router_delete.assert_called_once_with(
            test.IsHttpRequest(), router.id)

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'port_list',
                                      'router_remove_interface',
                                      'router_delete',
                                      'is_extension_supported'),
                        api.keystone: ('tenant_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_router_with_interface_delete(self):
        router = self.routers.first()
        ports = self.ports.list()
        tenants = self.tenants.list()
        quota_data = self.neutron_quota_usages.first()

        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_list.return_value = [tenants, False]
        self._mock_external_network_list(count=3)
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self.mock_port_list.return_value = ports
        self.mock_router_remove_interface.return_value = None
        self.mock_router_delete.return_value = None

        res = self.client.get(self.INDEX_URL)

        formData = {'action': 'routers__delete__' + router.id}
        res = self.client.post(self.INDEX_URL, formData, follow=True)
        self.assertNoFormErrors(res)
        self.assertMessageCount(response=res, success=1)
        self.assertIn('Deleted Router: ' + router.name,
                      res.content.decode('utf-8'))

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_router_list, 3,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_list, 3,
            mock.call(test.IsHttpRequest()))
        self._check_mock_external_network_list(count=3)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 4,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 3,
            mock.call(test.IsHttpRequest(), 'router_availability_zone'))
        self.mock_port_list.assert_called_once_with(
            test.IsHttpRequest(), device_id=router.id, device_owner=mock.ANY)
        self.mock_router_remove_interface.assert_has_calls(
            [mock.call(test.IsHttpRequest(), router.id, port_id=port.id)
             for port in ports]
        )
        self.mock_router_delete.assert_called_once_with(
            test.IsHttpRequest(), router.id)

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    @test.update_settings(FILTER_DATA_FIRST={'admin.routers': True})
    def test_routers_list_with_admin_filter_first(self):
        quota_data = self.neutron_quota_usages.first()
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, [])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')

    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        api.keystone: ('tenant_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_routers_list_with_non_exist_tenant_filter(self):
        self.mock_is_extension_supported.return_value = True
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        quota_data = self.neutron_quota_usages.first()
        self.mock_tenant_quota_usages.return_value = quota_data

        self.client.post(
            self.INDEX_URL,
            data={'routers__filter_admin_routers__q_field': 'project',
                  'routers__filter_admin_routers__q': 'non_exist_tenant'})
        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, [])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(test.IsHttpRequest(), "router_availability_zone"))
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())


class RouterViewTests(r_test.RouterViewTests):
    DASHBOARD = 'admin'


class RouterTestsNoL3Agent(RouterTests):

    support_l3_agent = False


class RouterRouteTests(RouterMixin,
                       r_test.RouterRouteTestCase,
                       test.BaseAdminViewTests):
    DASHBOARD = 'admin'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_mocks({api.neutron: ('list_l3_agent_hosting_router',)})
    def test_extension_hides_without_routes(self):
        super(RouterRouteTests, self).test_extension_hides_without_routes()

    @test.create_mocks({api.neutron: ('list_l3_agent_hosting_router',)})
    def test_routerroute_detail(self):
        super(RouterRouteTests, self).test_routerroute_detail()
