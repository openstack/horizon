# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from django import http
from django.core.urlresolvers import reverse
from mox import IsA
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import test


class InstanceViewTest(test.BaseAdminViewTests):
    def test_index(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        tenants = self.tenants.list()
        self.mox.StubOutWithMock(api.nova, 'server_list')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.keystone, 'tenant_list')
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True).\
                                 AndReturn(tenants)
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True).AndReturn(servers)
        api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn(flavors)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:instances:index'))
        self.assertTemplateUsed(res, 'syspanel/instances/index.html')
        instances = res.context['table'].data
        self.assertItemsEqual(instances, servers)

    def test_index_server_list_exception(self):
        self.mox.StubOutWithMock(api.nova, 'server_list')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        exception = novaclient_exceptions.ClientException('apiException')
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:instances:index'))
        self.assertTemplateUsed(res, 'syspanel/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
