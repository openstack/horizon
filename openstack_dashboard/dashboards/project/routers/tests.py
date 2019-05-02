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
import copy

from django.urls import reverse

import mock
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class RouterMixin(object):

    def _get_detail(self, router, extraroute=True):

        supported_extensions = {
            'extraroute': extraroute,
            'router_availability_zone': True,
        }

        def get_supported_extension(*args):
            alias = args[1]
            return supported_extensions[alias]

        self.mock_is_extension_supported.side_effect = get_supported_extension

        self.mock_router_get.return_value = router
        self.mock_port_list.return_value = [self.ports.first()]
        self._mock_external_network_get(router)

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router.id]))
        return res

    def _check_get_detail(self, router, extraroute=True):
        self.mock_is_extension_supported.assert_any_call(
            test.IsHttpRequest(), 'extraroute')
        self.mock_is_extension_supported.assert_any_call(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)
        self.mock_port_list.assert_called_once_with(test.IsHttpRequest(),
                                                    device_id=router.id)
        self._check_mock_external_network_get(router)

    def _mock_external_network_list(self, count=1, alter_ids=False):
        ext_nets = [n for n in self.networks.list() if n['router:external']]
        if alter_ids:
            for ext_net in ext_nets:
                ext_net.id += 'some extra garbage'
        self.mock_network_list.side_effect = [ext_nets for i in range(count)]

    def _check_mock_external_network_list(self, count=1):
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_list, count,
            mock.call(test.IsHttpRequest(), **{'router:external': True}))

    def _mock_external_network_get(self, router):
        ext_net = self.networks.list()[2]
        self.mock_network_get.return_value = ext_net

    def _check_mock_external_network_get(self, router):
        ext_net_id = router.external_gateway_info['network_id']
        self.mock_network_get.assert_called_once_with(
            test.IsHttpRequest(), ext_net_id, expand_subnet=False)


class RouterTestCase(object):

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

        self.mock_router_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_index_router_list_exception(self):
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.side_effect = self.exceptions.neutron
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)

        self.mock_router_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_set_external_network_empty(self):
        router = self.routers.first()
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.return_value = [router]
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list(alter_ids=True)

        res = self.client.get(self.INDEX_URL)

        table_data = res.context['table'].data
        self.assertEqual(len(table_data), 1)
        self.assertIn('(Not Found)',
                      table_data[0]['external_gateway_info']['network'])
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertMessageCount(res, error=1)

        self.mock_router_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 2,
            mock.call(test.IsHttpRequest(), targets=('router',)))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_get',
                                      'port_list',
                                      'network_get',
                                      'is_extension_supported')})
    def test_router_detail(self):
        router = self.routers.first()
        res = self._get_detail(router)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        ports = res.context['interfaces_table'].data
        self.assertItemsEqual(ports, [self.ports.first()])

        self._check_get_detail(router)

    @test.create_mocks({api.neutron: ('router_get',)})
    def test_router_detail_exception(self):
        router = self.routers.first()
        self.mock_router_get.side_effect = self.exceptions.neutron

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router.id]))
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.mock_router_get.assert_called_once_with(test.IsHttpRequest(),
                                                     router.id)

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'port_list',
                                      'router_delete',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_router_delete(self):
        router = self.routers.first()
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list(count=3)
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
            mock.call(test.IsHttpRequest(), tenant_id=self.tenant.id))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 4,
            mock.call(test.IsHttpRequest(), targets=('router', )))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 3,
            mock.call(test.IsHttpRequest(), 'router_availability_zone'))
        self._check_mock_external_network_list(count=3)
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
                        quotas: ('tenant_quota_usages',)})
    def test_router_with_interface_delete(self):
        router = self.routers.first()
        ports = self.ports.list()
        quota_data = self.neutron_quota_usages.first()
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list(count=3)
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
            mock.call(test.IsHttpRequest(), tenant_id=self.tenant.id))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 4,
            mock.call(test.IsHttpRequest(), targets=('router', )))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 3,
            mock.call(test.IsHttpRequest(), 'router_availability_zone'))
        self._check_mock_external_network_list(count=3)
        self.mock_port_list.assert_called_once_with(
            test.IsHttpRequest(), device_id=router.id, device_owner=mock.ANY)
        self.assertEqual(len(ports),
                         self.mock_router_remove_interface.call_count)
        self.mock_router_remove_interface.assert_has_calls(
            [mock.call(test.IsHttpRequest(), router.id, port_id=port.id)
             for port in ports]
        )
        self.mock_router_delete.assert_called_once_with(
            test.IsHttpRequest(), router.id)


class RouterTests(RouterMixin, RouterTestCase, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD


class RouterActionTests(test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported')})
    def test_router_create_post(self):
        router = self.routers.first()

        features = {
            ('ext-gw-mode', 'create_router_enable_snat'): True,
            ('dvr', 'create'): False,
            ('l3-ha', 'create'): False,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_network_list.return_value = self.networks.list()
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = False
        self.mock_router_create.return_value = router

        form_data = {'name': router.name,
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      'ext-gw-mode', 'create_router_enable_snat'),
            mock.call(test.IsHttpRequest(), 'dvr', 'create'),
            mock.call(test.IsHttpRequest(), 'l3-ha', 'create'),
        ])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=router.name,
            admin_state_up=router.admin_state_up)

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported')})
    def test_router_create_post_mode_server_default(self):
        router = self.routers.first()

        features = {
            ('ext-gw-mode', 'create_router_enable_snat'): True,
            ('dvr', 'create'): True,
            ('l3-ha', 'create'): True,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_network_list.return_value = self.networks.list()
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = False
        self.mock_router_create.return_value = router

        form_data = {'name': router.name,
                     'mode': 'server_default',
                     'ha': 'server_default',
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      'ext-gw-mode', 'create_router_enable_snat'),
            mock.call(test.IsHttpRequest(), 'dvr', 'create'),
            mock.call(test.IsHttpRequest(), 'l3-ha', 'create'),
        ])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=router.name,
            admin_state_up=router.admin_state_up)

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported')})
    def test_dvr_ha_router_create_post(self):
        router = self.routers.first()

        features = {
            ('ext-gw-mode', 'create_router_enable_snat'): True,
            ('dvr', 'create'): True,
            ('l3-ha', 'create'): True,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_network_list.return_value = self.networks.list()
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = False
        self.mock_router_create.return_value = router

        form_data = {'name': router.name,
                     'mode': 'distributed',
                     'ha': 'enabled',
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      'ext-gw-mode', 'create_router_enable_snat'),
            mock.call(test.IsHttpRequest(), 'dvr', 'create'),
            mock.call(test.IsHttpRequest(), 'l3-ha', 'create'),
        ])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=router.name, distributed=True, ha=True,
            admin_state_up=router.admin_state_up)

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported',
                                      'list_availability_zones')})
    def test_az_router_create_post(self):
        router = self.routers.first()

        features = {
            ('ext-gw-mode', 'create_router_enable_snat'): True,
            ('dvr', 'create'): False,
            ('l3-ha', 'create'): False,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_network_list.return_value = self.networks.list()
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = True
        self.mock_list_availability_zones.return_value = \
            self.neutron_availability_zones.list()
        self.mock_router_create.return_value = router

        form_data = {'name': router.name,
                     'mode': 'server_default',
                     'ha': 'server_default',
                     'az_hints': 'nova',
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      'ext-gw-mode', 'create_router_enable_snat'),
            mock.call(test.IsHttpRequest(), 'dvr', 'create'),
            mock.call(test.IsHttpRequest(), 'l3-ha', 'create'),
        ])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_list_availability_zones.assert_called_once_with(
            test.IsHttpRequest(), 'router', 'available')
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=router.name,
            availability_zone_hints=['nova'],
            admin_state_up=router.admin_state_up)

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported')})
    def test_router_create_post_with_admin_state_up(self):
        router = self.routers.first()
        self.mock_get_feature_permission.side_effect = [
            False,  # ext-gw-mode, create_router_enable_snat
            False,  # dvr, create
            False,  # l3-ha, create
        ]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_is_extension_supported.return_value = False
        self.mock_router_create.return_value = router

        form_data = {'name': router.name,
                     'admin_state_up': False}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls(
            [mock.call(test.IsHttpRequest(),
                       "ext-gw-mode", "create_router_enable_snat"),
             mock.call(test.IsHttpRequest(), "dvr", "create"),
             mock.call(test.IsHttpRequest(), "l3-ha", "create")])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), "router_availability_zone")
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(), name=router.name, admin_state_up=False)

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported')})
    def test_router_create_post_exception_error_case_409(self):
        router = self.routers.first()

        features = {
            ('ext-gw-mode', 'create_router_enable_snat'): True,
            ('dvr', 'create'): False,
            ('l3-ha', 'create'): False,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_network_list.return_value = self.networks.list()
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = False
        self.exceptions.neutron.status_code = 409
        self.mock_router_create.side_effect = self.exceptions.neutron

        form_data = {'name': router.name,
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      'ext-gw-mode', 'create_router_enable_snat'),
            mock.call(test.IsHttpRequest(), 'dvr', 'create'),
            mock.call(test.IsHttpRequest(), 'l3-ha', 'create'),
        ])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=router.name,
            admin_state_up=router.admin_state_up)

    @test.create_mocks({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list',
                                      'is_extension_supported')})
    def test_router_create_post_exception_error_case_non_409(self):
        router = self.routers.first()

        features = {
            ('ext-gw-mode', 'create_router_enable_snat'): True,
            ('dvr', 'create'): False,
            ('l3-ha', 'create'): False,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_network_list.return_value = self.networks.list()
        # router_availability_zone ext
        self.mock_is_extension_supported.return_value = False
        self.exceptions.neutron.status_code = 999
        self.mock_router_create.side_effect = self.exceptions.neutron

        form_data = {'name': router.name,
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.assertEqual(3, self.mock_get_feature_permission.call_count)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      'ext-gw-mode', 'create_router_enable_snat'),
            mock.call(test.IsHttpRequest(), 'dvr', 'create'),
            mock.call(test.IsHttpRequest(), 'l3-ha', 'create'),
        ])
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self.mock_router_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=router.name,
            admin_state_up=router.admin_state_up)

    @test.create_mocks({api.neutron: ('router_get',
                                      'get_feature_permission')})
    def _test_router_update_get(self, dvr_enabled=False,
                                current_dvr=False, ha_enabled=False):
        router = [r for r in self.routers.list()
                  if r.distributed == current_dvr][0]
        self.mock_router_get.return_value = router
        features = {
            ('dvr', 'update'): dvr_enabled,
            # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
            # PUT operation. It will be fixed in Kilo cycle.
            # ('l3-ha', 'update'): ha_enabled,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission

        url = reverse('horizon:%s:routers:update' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.get(url)

        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)
        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(), "dvr", "update"),
            # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
            # PUT operation. It will be fixed in Kilo cycle.
            # mock.call(test.IsHttpRequest(), "l3-ha", "update"),
        ])

        return res

    def test_router_update_get_dvr_disabled(self):
        res = self._test_router_update_get(dvr_enabled=False)

        self.assertTemplateUsed(res, 'project/routers/update.html')
        self.assertNotContains(res, 'Router Type')
        self.assertNotContains(res, 'id="id_mode"')

    def test_router_update_get_dvr_enabled_mode_centralized(self):
        res = self._test_router_update_get(dvr_enabled=True, current_dvr=False)

        self.assertTemplateUsed(res, 'project/routers/update.html')
        self.assertContains(res, 'Router Type')
        # Check both menu are displayed.
        self.assertContains(
            res,
            '<option value="centralized" selected="selected">'
            'Centralized</option>',
            html=True)
        self.assertContains(
            res,
            '<option value="distributed">Distributed</option>',
            html=True)

    def test_router_update_get_dvr_enabled_mode_distributed(self):
        res = self._test_router_update_get(dvr_enabled=True, current_dvr=True)

        self.assertTemplateUsed(res, 'project/routers/update.html')
        self.assertContains(res, 'Router Type')
        pattern = ('<input class="form-control" id="id_mode" name="mode" '
                   'readonly="readonly" type="text" value="distributed" '
                   'required/>')
        self.assertContains(res, pattern, html=True)
        self.assertNotContains(res, 'centralized')

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_update',
                                      'get_feature_permission')})
    def test_router_update_post_dvr_ha_disabled(self):
        router = self.routers.first()
        features = {
            ('dvr', 'update'): False,
            # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
            # PUT operation. It will be fixed in Kilo cycle.
            # ('l3-ha', 'update'): False,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_router_update.return_value = router
        self.mock_router_get.return_value = router

        form_data = {'router_id': router.id,
                     'name': router.name,
                     'admin_state': router.admin_state_up}
        url = reverse('horizon:%s:routers:update' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(), "dvr", "update"),
            # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
            # PUT operation. It will be fixed in Kilo cycle.
            # mock.call(test.IsHttpRequest(), "l3-ha", "update"),
        ])
        self.mock_router_update.assert_called_once_with(
            test.IsHttpRequest(), router.id,
            name=router.name, admin_state_up=router.admin_state_up)
        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_update',
                                      'get_feature_permission')})
    def test_router_update_post_dvr_ha_enabled(self):
        router = self.routers.first()
        features = {
            ('dvr', 'update'): True,
            # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
            # PUT operation. It will be fixed in Kilo cycle.
            # ('l3-ha', 'update'): True,
        }

        def fake_get_feature_permission(*args):
            return features[(args[1], args[2])]

        self.mock_get_feature_permission.side_effect = \
            fake_get_feature_permission
        self.mock_router_update.return_value = router
        self.mock_router_get.return_value = router

        form_data = {'router_id': router.id,
                     'name': router.name,
                     'admin_state': router.admin_state_up,
                     'mode': 'distributed',
                     'ha': True}
        url = reverse('horizon:%s:routers:update' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, self.INDEX_URL)

        self.mock_get_feature_permission.assert_has_calls([
            mock.call(test.IsHttpRequest(), "dvr", "update"),
            # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
            # PUT operation. It will be fixed in Kilo cycle.
            # mock.call(test.IsHttpRequest(), "l3-ha", "update"),
        ])
        self.mock_router_update.assert_called_once_with(
            test.IsHttpRequest(), router.id,
            name=router.name,
            admin_state_up=router.admin_state_up,
            # ha=True,
            distributed=True)
        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)

    def _test_router_addinterface(self, raise_error=False):
        router = self.routers.first()
        subnet = self.subnets.first()
        port = self.ports.first()

        if raise_error:
            self.mock_router_add_interface.side_effect = \
                self.exceptions.neutron
        else:
            self.mock_router_add_interface.return_value = {
                'subnet_id': subnet.id,
                'port_id': port.id
            }
            self.mock_port_get.return_value = port

        self._check_router_addinterface(router, subnet)

        self.mock_router_add_interface.assert_called_once_with(
            test.IsHttpRequest(), router.id, subnet_id=subnet.id)
        if not raise_error:
            self.mock_port_get.assert_called_once_with(
                test.IsHttpRequest(), port.id)

    def _check_router_addinterface(self, router, subnet, ip_address=''):
        self.mock_router_get.return_value = router
        self.mock_port_list.return_value = []
        self.mock_network_list.side_effect = [self.networks.list(), []]

        form_data = {'router_id': router.id,
                     'router_name': router.name,
                     'subnet_id': subnet.id,
                     'ip_address': ip_address}

        url = reverse('horizon:%s:routers:addinterface' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[router.id])
        self.assertRedirectsNoFollow(res, detail_url)

        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)
        self.mock_port_list.assert_called_once_with(
            test.IsHttpRequest(), device_id=router.id)
        self.assertEqual(2, self.mock_network_list.call_count)
        self.mock_network_list.assert_has_calls([
            mock.call(test.IsHttpRequest(),
                      shared=False,
                      tenant_id=router['tenant_id']),
            mock.call(test.IsHttpRequest(),
                      shared=True),
        ])

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_add_interface',
                                      'port_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface(self):
        self._test_router_addinterface()

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_add_interface',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface_exception(self):
        self._test_router_addinterface(raise_error=True)

    def _test_router_addinterface_ip_addr(self, errors=None):
        errors = errors or []
        router = self.routers.first()
        subnet = self.subnets.first()
        port = self.ports.first()
        ip_addr = port['fixed_ips'][0]['ip_address']
        self._setup_mock_addinterface_ip_addr(
            router, subnet, port, ip_addr, errors)
        self._check_router_addinterface(
            router, subnet, ip_addr)
        self._check_mock_addinterface_ip_addr(
            router, subnet, port, ip_addr, errors)

    def _setup_mock_addinterface_ip_addr(self, router, subnet, port, ip_addr,
                                         errors=None):
        errors = errors or []

        if 'subnet_get' in errors:
            self.mock_subnet_get.side_effect = self.exceptions.neutron
            return

        self.mock_subnet_get.return_value = subnet

        if 'port_create' in errors:
            self.mock_port_create.side_effect = self.exceptions.neutron
            return

        self.mock_port_create.return_value = port

        if 'add_interface' not in errors:
            self.mock_router_add_interface.return_value = None
            return

        self.mock_router_add_interface.side_effect = self.exceptions.neutron

        if 'port_delete' in errors:
            self.mock_port_delete.side_effect = self.exceptions.neutron
        else:
            self.mock_port_delete.return_value = None

    def _check_mock_addinterface_ip_addr(self, router, subnet, port, ip_addr,
                                         errors=None):
        errors = errors or []

        self.mock_subnet_get.assert_called_once_with(
            test.IsHttpRequest(), subnet.id)
        if 'subnet_get' in errors:
            return

        params = {'network_id': subnet.network_id,
                  'fixed_ips': [{'subnet_id': subnet.id,
                                 'ip_address': ip_addr}]}
        self.mock_port_create.assert_called_once_with(
            test.IsHttpRequest(), **params)
        if 'port_create' in errors:
            return

        self.mock_router_add_interface.assert_called_once_with(
            test.IsHttpRequest(), router.id, port_id=port.id)
        if 'add_interface' not in errors:
            return

        self.mock_port_delete.assert_called_once_with(
            test.IsHttpRequest(), port.id)

    @test.create_mocks({api.neutron: ('router_add_interface',
                                      'subnet_get',
                                      'port_create',
                                      'router_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr(self):
        self._test_router_addinterface_ip_addr()

    @test.create_mocks({api.neutron: ('subnet_get',
                                      'router_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_subnet_get(self):
        self._test_router_addinterface_ip_addr(errors=['subnet_get'])

    @test.create_mocks({api.neutron: ('subnet_get',
                                      'port_create',
                                      'router_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_port_create(self):
        self._test_router_addinterface_ip_addr(errors=['port_create'])

    @test.create_mocks({api.neutron: ('router_add_interface',
                                      'subnet_get',
                                      'port_create',
                                      'port_delete',
                                      'router_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_add_interface(self):
        self._test_router_addinterface_ip_addr(errors=['add_interface'])

    @test.create_mocks({api.neutron: ('router_add_interface',
                                      'subnet_get',
                                      'port_create',
                                      'port_delete',
                                      'router_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_port_delete(self):
        self._test_router_addinterface_ip_addr(errors=['add_interface',
                                                       'port_delete'])

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_add_gateway',
                                      'network_list',
                                      'is_extension_supported',
                                      'get_feature_permission')})
    def test_router_add_gateway(self):
        router = self.routers.first()
        network = self.networks.first()

        self.mock_router_add_gateway.return_value = None
        self.mock_router_get.return_value = router
        self.mock_network_list.return_value = [network]
        # ext-gw-mode
        self.mock_is_extension_supported.return_value = True
        # ext-gw-mode and update_router_enable_snat
        self.mock_get_feature_permission.return_value = True

        form_data = {'router_id': router.id,
                     'router_name': router.name,
                     'network_id': network.id,
                     'enable_snat': True}

        url = reverse('horizon:%s:routers:setgateway' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = self.INDEX_URL
        self.assertRedirectsNoFollow(res, detail_url)

        self.mock_router_add_gateway.assert_called_once_with(
            test.IsHttpRequest(), router.id, network.id, True)
        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'ext-gw-mode')
        self.mock_get_feature_permission.assert_called_once_with(
            test.IsHttpRequest(), 'ext-gw-mode', 'update_router_enable_snat')

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_add_gateway',
                                      'network_list',
                                      'is_extension_supported',
                                      'get_feature_permission')})
    def test_router_add_gateway_exception(self):
        router = self.routers.first()
        network = self.networks.first()

        self.mock_router_add_gateway.side_effect = self.exceptions.neutron
        self.mock_router_get.return_value = router
        self.mock_network_list.return_value = [network]
        # ext-gw-mode
        self.mock_is_extension_supported.return_value = True
        # ext-gw-mode and update_router_enable_snat
        self.mock_get_feature_permission.return_value = True

        form_data = {'router_id': router.id,
                     'router_name': router.name,
                     'network_id': network.id,
                     'enable_snat': True}

        url = reverse('horizon:%s:routers:setgateway' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = self.INDEX_URL
        self.assertRedirectsNoFollow(res, detail_url)

        self.mock_router_add_gateway.assert_called_once_with(
            test.IsHttpRequest(), router.id, network.id, True)
        self.mock_router_get.assert_called_once_with(
            test.IsHttpRequest(), router.id)
        self.mock_network_list.assert_called_once_with(
            test.IsHttpRequest(), **{'router:external': True})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'ext-gw-mode')
        self.mock_get_feature_permission.assert_called_once_with(
            test.IsHttpRequest(), 'ext-gw-mode', 'update_router_enable_snat')


class RouterRouteTestCase(object):

    @test.create_mocks({api.neutron: ('router_get',
                                      'port_list',
                                      'network_get',
                                      'is_extension_supported')})
    def test_extension_hides_without_routes(self):
        router = self.routers_with_routes.first()
        res = self._get_detail(router, extraroute=False)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertNotIn('extra_routes_table', res.context)

        self._check_get_detail(router, extraroute=False)

    @test.create_mocks({api.neutron: ('router_get',
                                      'port_list',
                                      'network_get',
                                      'is_extension_supported')})
    def test_routerroute_detail(self):
        router = self.routers_with_routes.first()
        res = self._get_detail(router, extraroute=True)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        routes = res.context['extra_routes_table'].data
        routes_dict = [r._apidict for r in routes]
        self.assertItemsEqual(routes_dict, router['routes'])

        self._check_get_detail(router, extraroute=True)

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_update')})
    def _test_router_addrouterroute(self, ipv6=False, raise_error=False):
        pre_router = self.routers_with_routes.first()
        post_router = copy.deepcopy(pre_router)
        if ipv6:
            route = {'nexthop': 'fdb6:b88a:488e::5', 'destination': '2002::/64'}
        else:
            route = {'nexthop': '10.0.0.5', 'destination': '40.0.1.0/24'}
        post_router['routes'].insert(0, route)
        self.mock_router_get.return_value = pre_router
        if raise_error:
            self.mock_router_update.side_effect = self.exceptions.neutron
        else:
            self.mock_router_update.return_value = {'router': post_router}

        form_data = copy.deepcopy(route)
        form_data['router_id'] = pre_router.id
        url = reverse('horizon:%s:routers:addrouterroute' % self.DASHBOARD,
                      args=[pre_router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[pre_router.id])
        self.assertRedirectsNoFollow(res, detail_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_router_get, 2,
            mock.call(test.IsHttpRequest(), pre_router.id))
        self.mock_router_update.assert_called_once_with(
            test.IsHttpRequest(), pre_router.id, routes=post_router['routes'])

    def test_router_addrouterroute(self):
        if self.DASHBOARD == 'project':
            self._test_router_addrouterroute()
            self.assertMessageCount(success=1)

    def test_router_addrouterroute_exception(self):
        if self.DASHBOARD == 'project':
            self._test_router_addrouterroute(raise_error=True)
            self.assertMessageCount(error=1)

    def test_router_addrouteripv6route(self):
        if self.DASHBOARD == 'project':
            self._test_router_addrouterroute(ipv6=True)
            self.assertMessageCount(success=1)

    def test_router_addrouteripv6route_exception(self):
        if self.DASHBOARD == 'project':
            self._test_router_addrouterroute(ipv6=True, raise_error=True)
            self.assertMessageCount(error=1)

    @test.create_mocks({api.neutron: ('router_get',
                                      'router_update',
                                      'network_get',
                                      'port_list',
                                      'is_extension_supported')})
    def test_router_removeroute(self):
        if self.DASHBOARD == 'admin':
            return
        pre_router = self.routers_with_routes.first()
        post_router = copy.deepcopy(pre_router)
        route = post_router['routes'].pop()
        self.mock_is_extension_supported.return_value = True
        self.mock_router_get.return_value = pre_router
        self.mock_router_update.return_value = {'router': post_router}
        self.mock_port_list.return_value = [self.ports.first()]
        self._mock_external_network_get(pre_router)

        form_route_id = route['nexthop'] + ":" + route['destination']
        form_data = {'action': 'extra_routes__delete__%s' % form_route_id}
        url = reverse(self.DETAIL_PATH, args=[pre_router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)

        self._check_mock_external_network_get(pre_router)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(test.IsHttpRequest(), 'extraroute'))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_router_get, 2,
            mock.call(test.IsHttpRequest(), pre_router.id))
        self.mock_router_update.assert_called_once_with(
            test.IsHttpRequest(), pre_router.id,
            routes=post_router['routes'])
        self.mock_port_list.assert_called_once_with(
            test.IsHttpRequest(), device_id=pre_router.id)


class RouterRouteTests(RouterMixin, RouterRouteTestCase, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD


class RouterViewTests(RouterMixin, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_disabled_when_quota_exceeded(self):
        quota_data = self.neutron_quota_usages.first()
        quota_data['router']['available'] = 0
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

        routers = res.context['routers_table'].data
        self.assertItemsEqual(routers, self.routers.list())

        create_action = self.getAndAssertTableAction(res, 'routers', 'create')
        self.assertIn('disabled', create_action.classes,
                      'Create button is not disabled')
        self.assertEqual('Create Router (Quota exceeded)',
                         create_action.verbose_name)

        self.mock_router_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), targets=('router', )))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_shown_when_quota_disabled(self):
        quota_data = self.neutron_quota_usages.first()
        quota_data['router'].pop('available')
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

        routers = res.context['routers_table'].data
        self.assertItemsEqual(routers, self.routers.list())

        create_action = self.getAndAssertTableAction(res, 'routers', 'create')
        self.assertFalse('disabled' in create_action.classes,
                         'Create button should not be disabled')
        self.assertEqual('Create Router',
                         create_action.verbose_name)

        self.mock_router_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), targets=('router', )))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self._check_mock_external_network_list()

    @test.create_mocks({api.neutron: ('router_list',
                                      'network_list',
                                      'is_extension_supported'),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_attributes(self):
        quota_data = self.neutron_quota_usages.first()
        quota_data['router']['available'] = 10
        self.mock_router_list.return_value = self.routers.list()
        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_is_extension_supported.return_value = True
        self._mock_external_network_list()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

        routers = res.context['routers_table'].data
        self.assertItemsEqual(routers, self.routers.list())

        create_action = self.getAndAssertTableAction(res, 'routers', 'create')
        self.assertEqual(set(['ajax-modal']), set(create_action.classes))
        self.assertEqual('Create Router',
                         six.text_type(create_action.verbose_name))
        self.assertEqual('horizon:project:routers:create', create_action.url)
        self.assertEqual((('network', 'create_router'),),
                         create_action.policy_rules)

        self.mock_router_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), targets=('router', )))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'router_availability_zone')
        self._check_mock_external_network_list()
