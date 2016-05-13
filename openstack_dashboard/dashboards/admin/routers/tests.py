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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers import tests as r_test
from openstack_dashboard.test import helpers as test


class RouterTests(test.BaseAdminViewTests, r_test.RouterTests):
    DASHBOARD = 'admin'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        api.keystone: ('tenant_list',)})
    def test_index(self):
        tenants = self.tenants.list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

    @test.create_stubs({api.neutron: ('router_list',),
                        api.keystone: ('tenant_list',)})
    def test_index_router_list_exception(self):
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('agent_list',
                                      'router_list_on_l3_agent',
                                      'network_list'),
                        api.keystone: ('tenant_list',)})
    def test_list_by_l3_agent(self):
        tenants = self.tenants.list()
        agent = self.agents.list()[1]
        api.neutron.agent_list(
            IsA(http.HttpRequest),
            id=agent.id).AndReturn([agent])
        api.neutron.router_list_on_l3_agent(
            IsA(http.HttpRequest),
            agent.id,
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()

        self.mox.ReplayAll()
        l3_list_url = reverse('horizon:admin:routers:l3_agent_list',
                              args=[agent.id])
        res = self.client.get(l3_list_url)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

    @test.create_stubs({api.neutron: ('router_list', 'network_list'),
                        api.keystone: ('tenant_list',)})
    def test_set_external_network_empty(self):
        router = self.routers.first()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn([router])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([self.tenants.list(), False])
        self._mock_external_network_list(alter_ids=True)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        table_data = res.context['table'].data
        self.assertEqual(len(table_data), 1)
        self.assertIn('(Not Found)',
                      table_data[0]['external_gateway_info']['network'])
        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('router_list', 'network_list',
                                      'port_list', 'router_delete',),
                        api.keystone: ('tenant_list',)})
    def test_router_delete(self):
        router = self.routers.first()
        tenants = self.tenants.list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=router.id, device_owner=IgnoreArg())\
            .AndReturn([])
        api.neutron.router_delete(IsA(http.HttpRequest), router.id)
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()
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
                        api.keystone: ('tenant_list',)})
    def test_router_with_interface_delete(self):
        router = self.routers.first()
        ports = self.ports.list()
        tenants = self.tenants.list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=router.id, device_owner=IgnoreArg())\
            .AndReturn(ports)
        for port in ports:
            api.neutron.router_remove_interface(IsA(http.HttpRequest),
                                                router.id, port_id=port.id)
        api.neutron.router_delete(IsA(http.HttpRequest), router.id)
        api.neutron.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        self._mock_external_network_list()
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        formData = {'action': 'routers__delete__' + router.id}
        res = self.client.post(self.INDEX_URL, formData, follow=True)
        self.assertNoFormErrors(res)
        self.assertMessageCount(response=res, success=1)
        self.assertIn('Deleted Router: ' + router.name,
                      res.content.decode('utf-8'))


class RouterRouteTest(test.BaseAdminViewTests, r_test.RouterRouteTests):
    DASHBOARD = 'admin'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD
