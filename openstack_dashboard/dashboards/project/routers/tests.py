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
from openstack_dashboard.test import helpers as test


class RouterTests(test.TestCase):
    DASHBOARD = 'project'
    INDEX_URL = reverse('horizon:%s:routers:index' % DASHBOARD)
    DETAIL_PATH = 'horizon:%s:routers:detail' % DASHBOARD

    @test.create_stubs({api.quantum: ('router_list',)})
    def test_index(self):
        api.quantum.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            search_opts=None).AndReturn(self.routers.list())

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        routers = res.context['table'].data
        self.assertItemsEqual(routers, self.routers.list())

    @test.create_stubs({api.quantum: ('router_list',)})
    def test_index_router_list_exception(self):
        api.quantum.router_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            search_opts=None).AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/routers/index.html' % self.DASHBOARD)
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.quantum: ('router_get', 'port_list')})
    def test_router_detail(self):
        router_id = self.routers.first().id
        api.quantum.router_get(IsA(http.HttpRequest), router_id)\
            .AndReturn(self.routers.first())
        api.quantum.port_list(IsA(http.HttpRequest),
                              device_id=router_id)\
            .AndReturn([self.ports.first()])

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router_id]))

        self.assertTemplateUsed(res, '%s/routers/detail.html' % self.DASHBOARD)
        ports = res.context['interfaces_table'].data
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.quantum: ('router_get', 'port_list')})
    def test_router_detail_exception(self):
        router_id = self.routers.first().id
        api.quantum.router_get(IsA(http.HttpRequest), router_id)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.port_list(IsA(http.HttpRequest),
                              device_id=router_id)\
            .AndReturn([self.ports.first()])
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:%s'
                                      ':routers:detail' % self.DASHBOARD,
                                      args=[router_id]))
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.quantum: ('router_create',)})
    def test_router_create_post(self):
        router = self.routers.first()
        api.quantum.router_create(IsA(http.HttpRequest), name=router.name)\
            .AndReturn(router)
        self.mox.ReplayAll()

        form_data = {'name': router.name}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.quantum: ('router_create',)})
    def test_router_create_post_exception(self):
        router = self.routers.first()
        api.quantum.router_create(IsA(http.HttpRequest), name=router.name)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'name': router.name}
        url = reverse('horizon:%s:routers:create' % self.DASHBOARD)
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.INDEX_URL)

    @test.create_stubs({api.quantum: ('router_get',
                                      'router_add_interface',
                                      'network_list')})
    def test_router_addinterface(self):
        router = self.routers.first()
        subnet = self.subnets.first()
        api.quantum.router_add_interface(
            IsA(http.HttpRequest),
            router.id,
            subnet_id=subnet.id).AndReturn(None)
        api.quantum.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        api.quantum.network_list(
            IsA(http.HttpRequest),
            shared=False,
            tenant_id=router['tenant_id']).AndReturn(self.networks.list())
        api.quantum.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'subnet_id': subnet.id}

        url = reverse('horizon:%s:routers:addinterface' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[router.id])
        self.assertRedirectsNoFollow(res, detail_url)

    @test.create_stubs({api.quantum: ('router_get',
                                      'router_add_interface',
                                      'network_list')})
    def test_router_addinterface_exception(self):
        router = self.routers.first()
        subnet = self.subnets.first()
        api.quantum.router_add_interface(
            IsA(http.HttpRequest),
            router.id,
            subnet_id=subnet.id).AndRaise(self.exceptions.quantum)
        api.quantum.router_get(IsA(http.HttpRequest), router.id)\
            .AndReturn(router)
        api.quantum.network_list(
            IsA(http.HttpRequest),
            shared=False,
            tenant_id=router['tenant_id']).AndReturn(self.networks.list())
        api.quantum.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'subnet_id': subnet.id}

        url = reverse('horizon:%s:routers:addinterface' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[router.id])
        self.assertRedirectsNoFollow(res, detail_url)

    @test.create_stubs({api.quantum: ('router_get',
                                      'router_add_gateway',
                                      'network_list')})
    def test_router_add_gateway(self):
        router = self.routers.first()
        network = self.networks.first()
        api.quantum.router_add_gateway(
            IsA(http.HttpRequest),
            router.id,
            network.id).AndReturn(None)
        api.quantum.router_get(
            IsA(http.HttpRequest), router.id).AndReturn(router)
        search_opts = {'router:external': True}
        api.quantum.network_list(
            IsA(http.HttpRequest), **search_opts).AndReturn([network])
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'network_id': network.id}

        url = reverse('horizon:%s:routers:setgateway' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[router.id])
        self.assertRedirectsNoFollow(res, detail_url)

    @test.create_stubs({api.quantum: ('router_get',
                                      'router_add_gateway',
                                      'network_list')})
    def test_router_add_gateway_exception(self):
        router = self.routers.first()
        network = self.networks.first()
        api.quantum.router_add_gateway(
            IsA(http.HttpRequest),
            router.id,
            network.id).AndRaise(self.exceptions.quantum)
        api.quantum.router_get(
            IsA(http.HttpRequest), router.id).AndReturn(router)
        search_opts = {'router:external': True}
        api.quantum.network_list(
            IsA(http.HttpRequest), **search_opts).AndReturn([network])
        self.mox.ReplayAll()

        form_data = {'router_id': router.id,
                     'network_id': network.id}

        url = reverse('horizon:%s:routers:setgateway' % self.DASHBOARD,
                      args=[router.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(self.DETAIL_PATH, args=[router.id])
        self.assertRedirectsNoFollow(res, detail_url)
