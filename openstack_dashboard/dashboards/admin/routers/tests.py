# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from mox import IsA
from django import http
from django.core.urlresolvers import reverse

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers import tests as r_test
from openstack_dashboard.test import helpers as test


class RouterTests(test.BaseAdminViewTests, r_test.RouterTests):
    DASHBOARD = 'admin'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_stubs({api.quantum: ('router_list', 'network_list'),
                        api.keystone: ('tenant_list',)})
    def test_index(self):
        tenants = self.tenants.list()
        api.quantum.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndReturn(self.routers.list())
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        self._mock_external_network_list()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

    @test.create_stubs({api.quantum: ('router_list',),
                        api.keystone: ('tenant_list',)})
    def test_index_router_list_exception(self):
        tenants = self.tenants.list()
        api.quantum.router_list(
            IsA(http.HttpRequest),
            search_opts=None).AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.quantum: ('router_list', 'router_create'),
                        api.keystone: ('tenant_list',)})
    def test_router_create_post(self):
        router = self.routers.first()
        tenants = self.tenants.list()
        api.quantum.router_create(
            IsA(http.HttpRequest),
            name=router.name,
            tenant_id=router.tenant_id).AndReturn(router)
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)

        self.mox.ReplayAll()

        form_data = {'name': router.name,
                     'tenant_id': router.tenant_id}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.quantum: ('router_list', 'router_create'),
                        api.keystone: ('tenant_list',)})
    def test_router_create_post_exception(self):
        router = self.routers.first()
        tenants = self.tenants.list()
        api.quantum.router_create(
            IsA(http.HttpRequest),
            name=router.name,
            tenant_id=router.tenant_id).AndRaise(self.exceptions.quantum)
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        self.mox.ReplayAll()

        form_data = {'name': router.name,
                     'tenant_id': router.tenant_id}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)
