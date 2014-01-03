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

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

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
