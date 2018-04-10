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

import django
from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IgnoreArg
from mox3.mox import IsA
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class RouterMixin(object):
    @test.create_stubs({
        api.neutron: ('router_get', 'port_list',
                      'network_get', 'is_extension_supported',
                      'list_l3_agent_hosting_router'),
    })
    def _get_detail(self, router, extraroute=True, lookup_l3=False,
                    support_l3_agent=True):
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'extraroute')\
            .MultipleTimes().AndReturn(extraroute)
        if lookup_l3:
            api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                               'l3_agent_scheduler')\
                .AndReturn(support_l3_agent)
        api.neutron.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=router.id)\
            .AndReturn([self.ports.first()])
        self._mock_external_network_get(router)
        if lookup_l3 and support_l3_agent:
            agent = self.agents.list()[1]
            api.neutron.list_l3_agent_hosting_router(
                IsA(http.HttpRequest), router.id).AndReturn([agent])
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router.id]))
        return res

    def _mock_external_network_list(self, alter_ids=False):
        search_opts = {'router:external': True}
        ext_nets = [n for n in self.networks.list() if n['router:external']]
        if alter_ids:
            for ext_net in ext_nets:
                ext_net.id += 'some extra garbage'
        api.neutron.network_list(
            IsA(http.HttpRequest),
            **search_opts).AndReturn(ext_nets)

    def _mock_external_network_get(self, router):
        ext_net_id = router.external_gateway_info['network_id']
        ext_net = self.networks.list()[2]
        api.neutron.network_get(IsA(http.HttpRequest), ext_net_id,
                                expand_subnet=False).AndReturn(ext_net)

    def _mock_network_list(self, tenant_id):
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=False,
            tenant_id=tenant_id).AndReturn(self.networks.list())
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])


class RouterTests(RouterMixin, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        quota_data = self.neutron_quota_usages.first()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)
        self._mock_external_network_list()
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        quotas: ('tenant_quota_usages',)})
    def test_index_router_list_exception(self):
        quota_data = self.neutron_quota_usages.first()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).MultipleTimes().AndRaise(
            self.exceptions.neutron)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)
        self._mock_external_network_list()
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        quotas: ('tenant_quota_usages',)})
    def test_set_external_network_empty(self):
        router = self.routers.first()
        quota_data = self.neutron_quota_usages.first()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).MultipleTimes().AndReturn([router])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)
        self._mock_external_network_list(alter_ids=True)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        table_data = res.context['table'].data
        self.assertEqual(len(table_data), 1)
        self.assertIn('(Not Found)',
                      table_data[0]['external_gateway_info']['network'])
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertMessageCount(res, error=1)

    def test_router_detail(self):
        router = self.routers.first()
        res = self._get_detail(router)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        ports = res.context['interfaces_table'].data
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('router_get',)})
    def test_router_detail_exception(self):
        router = self.routers.first()
        api.neutron.router_get(IsA(http.HttpRequest), router.id)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router.id]))
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_list', 'network_list',
                                      'port_list', 'router_delete',),
                        quotas: ('tenant_quota_usages',)})
    def test_router_delete(self):
        router = self.routers.first()
        quota_data = self.neutron_quota_usages.first()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)
        self._mock_external_network_list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        self._mock_external_network_list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        self._mock_external_network_list()
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=router.id, device_owner=IgnoreArg())\
            .AndReturn([])
        api.neutron.router_delete(IsA(http.HttpRequest), router.id)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        formData = {'action': 'routers__delete__' + router.id}
        res = self.client.post(self.INDEX_URL, formData, follow=True)
        self.assertNoFormErrors(res)
        self.assertMessageCount(response=res, success=1)
        self.assertIn('Deleted Router: ' + router.name,
                      res.content.decode('utf-8'))

    @test.create_stubs({api.neutron: ('router_list', 'network_list',
                                      'port_list', 'router_remove_interface',
                                      'router_delete',),
                        quotas: ('tenant_quota_usages',)})
    def test_router_with_interface_delete(self):
        router = self.routers.first()
        ports = self.ports.list()
        quota_data = self.neutron_quota_usages.first()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)
        self._mock_external_network_list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        self._mock_external_network_list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        self._mock_external_network_list()
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=router.id, device_owner=IgnoreArg())\
            .AndReturn(ports)
        for port in ports:
            api.neutron.router_remove_interface(IsA(http.HttpRequest),
                                                router.id, port_id=port.id)
        api.neutron.router_delete(IsA(http.HttpRequest), router.id)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        formData = {'action': 'routers__delete__' + router.id}
        res = self.client.post(self.INDEX_URL, formData, follow=True)
        self.assertNoFormErrors(res)
        self.assertMessageCount(response=res, success=1)
        self.assertIn('Deleted Router: ' + router.name,
                      res.content.decode('utf-8'))


class RouterActionTests(RouterMixin, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_stubs({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list')})
    def test_router_create_post(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "create")\
            .AndReturn(False)
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "l3-ha", "create")\
            .AndReturn(False)
        api.neutron.network_list(IsA(http.HttpRequest))\
            .AndReturn(self.networks.list())
        params = {'name': router.name,
                  'admin_state_up': router.admin_state_up}
        api.neutron.router_create(IsA(http.HttpRequest), **params)\
            .AndReturn(router)

        self.mox.ReplayAll()
        form_data = {'name': router.name,
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list')})
    def test_router_create_post_mode_server_default(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "create")\
            .AndReturn(True)
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "l3-ha", "create")\
            .AndReturn(True)
        api.neutron.network_list(IsA(http.HttpRequest))\
            .AndReturn(self.networks.list())
        params = {'name': router.name,
                  'admin_state_up': router.admin_state_up}
        api.neutron.router_create(IsA(http.HttpRequest), **params)\
            .AndReturn(router)

        self.mox.ReplayAll()
        form_data = {'name': router.name,
                     'mode': 'server_default',
                     'ha': 'server_default',
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list')})
    def test_dvr_ha_router_create_post(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "create")\
            .MultipleTimes().AndReturn(True)
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "l3-ha", "create")\
            .MultipleTimes().AndReturn(True)
        api.neutron.network_list(IsA(http.HttpRequest))\
            .AndReturn(self.networks.list())
        param = {'name': router.name,
                 'distributed': True,
                 'ha': True,
                 'admin_state_up': router.admin_state_up}
        api.neutron.router_create(IsA(http.HttpRequest), **param)\
            .AndReturn(router)

        self.mox.ReplayAll()
        form_data = {'name': router.name,
                     'mode': 'distributed',
                     'ha': 'enabled',
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list')})
    def test_router_create_post_exception_error_case_409(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "create")\
            .MultipleTimes().AndReturn(False)
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "l3-ha", "create")\
            .AndReturn(False)
        self.exceptions.neutron.status_code = 409
        api.neutron.network_list(IsA(http.HttpRequest))\
            .MultipleTimes().AndReturn(self.networks.list())
        params = {'name': router.name,
                  'admin_state_up': router.admin_state_up}
        api.neutron.router_create(IsA(http.HttpRequest), **params)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'name': router.name,
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_create',
                                      'get_feature_permission',
                                      'network_list')})
    def test_router_create_post_exception_error_case_non_409(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "create")\
            .MultipleTimes().AndReturn(False)
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "l3-ha", "create")\
            .MultipleTimes().AndReturn(False)
        self.exceptions.neutron.status_code = 999
        api.neutron.network_list(IsA(http.HttpRequest))\
            .MultipleTimes().AndReturn(self.networks.list())
        params = {'name': router.name,
                  'admin_state_up': router.admin_state_up}
        api.neutron.router_create(IsA(http.HttpRequest), **params)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'name': router.name,
                     'admin_state_up': router.admin_state_up}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_get',
                                      'get_feature_permission')})
    def _test_router_update_get(self, dvr_enabled=False,
                                current_dvr=False,
                                ha_enabled=False):
        router = [r for r in self.routers.list()
                  if r.distributed == current_dvr][0]
        api.neutron.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "update")\
            .AndReturn(dvr_enabled)
        # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
        # PUT operation. It will be fixed in Kilo cycle.
        # api.neutron.get_feature_permission(IsA(http.HttpRequest),
        #                                    "l3-ha", "update")\
        #     .AndReturn(ha_enabled)
        self.mox.ReplayAll()

        url = reverse('horizon:%s:routers:update' % self.DASHBOARD,
                      args=[router.id])
        return self.client.get(url)

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
        if django.VERSION >= (1, 10):
            pattern = ('<input class="form-control" id="id_mode" name="mode" '
                       'readonly="readonly" type="text" value="distributed" '
                       'required/>')
        else:
            pattern = ('<input class="form-control" id="id_mode" name="mode" '
                       'readonly="readonly" type="text" '
                       'value="distributed" />')
        self.assertContains(res, pattern, html=True)
        self.assertNotContains(res, 'centralized')

    @test.create_stubs({api.neutron: ('router_get',
                                      'router_update',
                                      'get_feature_permission')})
    def test_router_update_post_dvr_ha_disabled(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "update")\
            .AndReturn(False)
        # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
        # PUT operation. It will be fixed in Kilo cycle.
        # api.neutron.get_feature_permission(IsA(http.HttpRequest),
        #                                    "l3-ha", "update")\
        #     .AndReturn(False)
        api.neutron.router_update(IsA(http.HttpRequest), router.id,
                                  name=router.name,
                                  admin_state_up=router.admin_state_up)\
            .AndReturn(router)
        api.neutron.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'name': router.name,
                     'admin_state': router.admin_state_up}
        url = reverse('horizon:%s:routers:update' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.neutron: ('router_get',
                                      'router_update',
                                      'get_feature_permission')})
    def test_router_update_post_dvr_ha_enabled(self):
        router = self.routers.first()
        api.neutron.get_feature_permission(IsA(http.HttpRequest),
                                           "dvr", "update")\
            .AndReturn(True)
        # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
        # PUT operation. It will be fixed in Kilo cycle.
        # api.neutron.get_feature_permission(IsA(http.HttpRequest),
        #                                    "l3-ha", "update")\
        #     .AndReturn(True)
        api.neutron.router_update(IsA(http.HttpRequest), router.id,
                                  name=router.name,
                                  admin_state_up=router.admin_state_up,
                                  # ha=True,
                                  distributed=True).AndReturn(router)
        api.neutron.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'name': router.name,
                     'admin_state': router.admin_state_up,
                     'mode': 'distributed',
                     'ha': True}
        url = reverse('horizon:%s:routers:update' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    def _test_router_addinterface(self, raise_error=False):
        router = self.routers.first()
        subnet = self.subnets.first()
        port = self.ports.first()

        add_interface = api.neutron.router_add_interface(
            IsA(http.HttpRequest), router.id, subnet_id=subnet.id)
        if raise_error:
            add_interface.AndRaise(self.exceptions.neutron)
        else:
            add_interface.AndReturn({'subnet_id': subnet.id,
                                     'port_id': port.id})
            api.neutron.port_get(IsA(http.HttpRequest), port.id)\
                .AndReturn(port)
        self._check_router_addinterface(router, subnet)

    def _check_router_addinterface(self, router, subnet, ip_address=''):
        # mock APIs used to show router detail
        api.neutron.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        api.neutron.port_list(IsA(http.HttpRequest), device_id=router.id)\
            .AndReturn([])
        self._mock_network_list(router['tenant_id'])
        self.mox.ReplayAll()

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

    @test.create_stubs({api.neutron: ('router_get',
                                      'router_add_interface',
                                      'port_get',
                                      'network_list',
                                      'port_list')})
    def test_router_addinterface(self):
        self._test_router_addinterface()

    @test.create_stubs({api.neutron: ('router_get',
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
        self._setup_mock_addinterface_ip_addr(router, subnet, port,
                                              ip_addr, errors)
        self._check_router_addinterface(router, subnet, ip_addr)

    def _setup_mock_addinterface_ip_addr(self, router, subnet, port,
                                         ip_addr, errors=None):
        errors = errors or []
        subnet_get = api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)
        if 'subnet_get' in errors:
            subnet_get.AndRaise(self.exceptions.neutron)
            return
        subnet_get.AndReturn(subnet)

        params = {'network_id': subnet.network_id,
                  'fixed_ips': [{'subnet_id': subnet.id,
                                 'ip_address': ip_addr}]}
        port_create = api.neutron.port_create(IsA(http.HttpRequest), **params)
        if 'port_create' in errors:
            port_create.AndRaise(self.exceptions.neutron)
            return
        port_create.AndReturn(port)

        add_inf = api.neutron.router_add_interface(
            IsA(http.HttpRequest), router.id, port_id=port.id)
        if 'add_interface' not in errors:
            return

        add_inf.AndRaise(self.exceptions.neutron)
        port_delete = api.neutron.port_delete(IsA(http.HttpRequest), port.id)
        if 'port_delete' in errors:
            port_delete.AndRaise(self.exceptions.neutron)

    @test.create_stubs({api.neutron: ('router_add_interface', 'subnet_get',
                                      'port_create',
                                      'router_get', 'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr(self):
        self._test_router_addinterface_ip_addr()

    @test.create_stubs({api.neutron: ('subnet_get', 'router_get',
                                      'network_list', 'port_list')})
    def test_router_addinterface_ip_addr_exception_subnet_get(self):
        self._test_router_addinterface_ip_addr(errors=['subnet_get'])

    @test.create_stubs({api.neutron: ('subnet_get', 'port_create',
                                      'router_get', 'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_port_create(self):
        self._test_router_addinterface_ip_addr(errors=['port_create'])

    @test.create_stubs({api.neutron: ('router_add_interface', 'subnet_get',
                                      'port_create', 'port_delete',
                                      'router_get', 'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_add_interface(self):
        self._test_router_addinterface_ip_addr(errors=['add_interface'])

    @test.create_stubs({api.neutron: ('router_add_interface', 'subnet_get',
                                      'port_create', 'port_delete',
                                      'router_get', 'network_list',
                                      'port_list')})
    def test_router_addinterface_ip_addr_exception_port_delete(self):
        self._test_router_addinterface_ip_addr(errors=['add_interface',
                                                       'port_delete'])

    @test.create_stubs({api.neutron: ('router_get',
                                      'router_add_gateway',
                                      'network_list')})
    def test_router_add_gateway(self):
        router = self.routers.first()
        network = self.networks.first()
        api.neutron.router_add_gateway(
            IsA(http.HttpRequest),
            router.id,
            network.id).AndReturn(None)
        api.neutron.router_get(
            IsA(http.HttpRequest), router.id).AndReturn(router)
        search_opts = {'router:external': True}
        api.neutron.network_list(
            IsA(http.HttpRequest), **search_opts).AndReturn([network])
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'router_name': router.name,
                     'network_id': network.id}

        url = reverse('horizon:%s:routers:setgateway' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = self.INDEX_URL
        self.assertRedirectsNoFollow(res, detail_url)

    @test.create_stubs({api.neutron: ('router_get',
                                      'router_add_gateway',
                                      'network_list')})
    def test_router_add_gateway_exception(self):
        router = self.routers.first()
        network = self.networks.first()
        api.neutron.router_add_gateway(
            IsA(http.HttpRequest),
            router.id,
            network.id).AndRaise(self.exceptions.neutron)
        api.neutron.router_get(
            IsA(http.HttpRequest), router.id).AndReturn(router)
        search_opts = {'router:external': True}
        api.neutron.network_list(
            IsA(http.HttpRequest), **search_opts).AndReturn([network])
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'router_name': router.name,
                     'network_id': network.id}

        url = reverse('horizon:%s:routers:setgateway' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = self.INDEX_URL
        self.assertRedirectsNoFollow(res, detail_url)


class RouterRouteTests(RouterMixin, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    def test_extension_hides_without_routes(self):
        router = self.routers_with_routes.first()
        res = self._get_detail(router, extraroute=False)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertNotIn('extra_routes_table', res.context)

    def test_routerroute_detail(self):
        router = self.routers_with_routes.first()
        res = self._get_detail(router, extraroute=True)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        routes = res.context['extra_routes_table'].data
        routes_dict = [r._apidict for r in routes]
        self.assertItemsEqual(routes_dict, router['routes'])

    @test.create_stubs({api.neutron: ('router_get', 'router_update')})
    def _test_router_addrouterroute(self, raise_error=False):
        pre_router = self.routers_with_routes.first()
        post_router = copy.deepcopy(pre_router)
        route = {'nexthop': '10.0.0.5', 'destination': '40.0.1.0/24'}
        post_router['routes'].insert(0, route)
        api.neutron.router_get(IsA(http.HttpRequest), pre_router.id)\
                   .MultipleTimes().AndReturn(pre_router)
        params = {}
        params['routes'] = post_router['routes']
        router_update = api.neutron.router_update(IsA(http.HttpRequest),
                                                  pre_router.id, **params)
        if raise_error:
            router_update.AndRaise(self.exceptions.neutron)
        else:
            router_update.AndReturn({'router': post_router})
        self.mox.ReplayAll()

        form_data = copy.deepcopy(route)
        form_data['router_id'] = pre_router.id
        url = reverse('horizon:%s:routers:addrouterroute' % self.DASHBOARD,
                      args=[pre_router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[pre_router.id])
        self.assertRedirectsNoFollow(res, detail_url)

    def test_router_addrouterroute(self):
        if self.DASHBOARD == 'project':
            self._test_router_addrouterroute()
            self.assertMessageCount(success=1)

    def test_router_addrouterroute_exception(self):
        if self.DASHBOARD == 'project':
            self._test_router_addrouterroute(raise_error=True)
            self.assertMessageCount(error=1)

    @test.create_stubs({api.neutron: ('router_get', 'router_update',
                                      'network_get', 'port_list',
                                      'is_extension_supported')})
    def test_router_removeroute(self):
        if self.DASHBOARD == 'admin':
            return
        pre_router = self.routers_with_routes.first()
        post_router = copy.deepcopy(pre_router)
        route = post_router['routes'].pop()
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'extraroute')\
            .MultipleTimes().AndReturn(True)
        api.neutron.router_get(IsA(http.HttpRequest),
                               pre_router.id).AndReturn(pre_router)
        params = {}
        params['routes'] = post_router['routes']
        api.neutron.router_get(IsA(http.HttpRequest),
                               pre_router.id).AndReturn(pre_router)
        router_update = api.neutron.router_update(IsA(http.HttpRequest),
                                                  pre_router.id, **params)
        router_update.AndReturn({'router': post_router})
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=pre_router.id)\
            .AndReturn([self.ports.first()])
        self._mock_external_network_get(pre_router)
        self.mox.ReplayAll()
        form_route_id = route['nexthop'] + ":" + route['destination']
        form_data = {'action': 'extra_routes__delete__%s' % form_route_id}
        url = reverse(self.DETAIL_PATH, args=[pre_router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)


class RouterViewTests(RouterMixin, test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_disabled_when_quota_exceeded(self):
        quota_data = self.neutron_quota_usages.first()
        quota_data['routers']['available'] = 0
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)

        self._mock_external_network_list()
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

        routers = res.context['routers_table'].data
        self.assertItemsEqual(routers, self.routers.list())

        create_action = self.getAndAssertTableAction(res, 'routers', 'create')
        self.assertIn('disabled', create_action.classes,
                      'Create button is not disabled')
        self.assertEqual('Create Router (Quota exceeded)',
                         create_action.verbose_name)

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_shown_when_quota_disabled(self):
        quota_data = self.neutron_quota_usages.first()
        quota_data['routers'].pop('available')
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)

        self._mock_external_network_list()
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

        routers = res.context['routers_table'].data
        self.assertItemsEqual(routers, self.routers.list())

        create_action = self.getAndAssertTableAction(res, 'routers', 'create')
        self.assertFalse('disabled' in create_action.classes,
                         'Create button should not be disabled')
        self.assertEqual('Create Router',
                         create_action.verbose_name)

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_attributes(self):
        quota_data = self.neutron_quota_usages.first()
        quota_data['routers']['available'] = 10
        api.neutron.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).AndReturn(self.routers.list())
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('routers', )) \
            .MultipleTimes().AndReturn(quota_data)

        self._mock_external_network_list()
        self.mox.ReplayAll()

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
