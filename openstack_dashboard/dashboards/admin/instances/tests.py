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

from collections import OrderedDict
import uuid

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:admin:instances:index')


class InstanceViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('flavor_list', 'server_list',
                                   'extension_supported',),
                        api.keystone: ('tenant_list',),
                        api.network: ('servers_update_addresses',)})
    def test_index(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        tenants = self.tenants.list()
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.keystone.tenant_list(IsA(http.HttpRequest)).\
            AndReturn([tenants, False])
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True, search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers,
                                             all_tenants=True)
        api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn(flavors)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/instances/index.html')
        instances = res.context['table'].data
        self.assertItemsEqual(instances, servers)

    @test.create_stubs({api.nova: ('flavor_list', 'flavor_get',
                                   'server_list', 'extension_supported',),
                        api.keystone: ('tenant_list',),
                        api.network: ('servers_update_addresses',)})
    def test_index_flavor_list_exception(self):
        servers = self.servers.list()
        tenants = self.tenants.list()
        flavors = self.flavors.list()
        full_flavors = OrderedDict([(f.id, f) for f in flavors])

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True, search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers,
                                             all_tenants=True)
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)). \
            AndRaise(self.exceptions.nova)
        api.keystone.tenant_list(IsA(http.HttpRequest)).\
            AndReturn([tenants, False])
        for server in servers:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                AndReturn(full_flavors[server.flavor["id"]])

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/instances/index.html')
        instances = res.context['table'].data
        self.assertItemsEqual(instances, servers)

    @test.create_stubs({api.nova: ('flavor_list', 'flavor_get',
                                   'server_list', 'extension_supported', ),
                        api.keystone: ('tenant_list',),
                        api.network: ('servers_update_addresses',)})
    def test_index_flavor_get_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        tenants = self.tenants.list()
        # UUIDs generated using indexes are unlikely to match
        # any of existing flavor ids and are guaranteed to be deterministic.
        for i, server in enumerate(servers):
            server.flavor['id'] = str(uuid.UUID(int=i))

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True, search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers,
                                             all_tenants=True)
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)). \
            AndReturn(flavors)
        api.keystone.tenant_list(IsA(http.HttpRequest)).\
            AndReturn([tenants, False])
        for server in servers:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        instances = res.context['table'].data
        self.assertTemplateUsed(res, 'admin/instances/index.html')
        # Since error messages produced for each instance are identical,
        # there will be only one error message for all instances
        # (messages de-duplication).
        self.assertMessageCount(res, error=1)
        self.assertItemsEqual(instances, servers)

    @test.create_stubs({api.nova: ('server_list',)})
    def test_index_server_list_exception(self):
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True, search_opts=search_opts) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)

    @test.create_stubs({api.nova: ('server_get', 'flavor_get',
                                   'extension_supported', ),
                        api.keystone: ('tenant_get',)})
    def test_ajax_loading_instances(self):
        server = self.servers.first()
        flavor = self.flavors.list()[0]
        tenant = self.tenants.list()[0]
        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_get(IsA(http.HttpRequest),
                            server.flavor['id']).AndReturn(flavor)
        api.keystone.tenant_get(IsA(http.HttpRequest),
                                server.tenant_id,
                                admin=True).AndReturn(tenant)
        self.mox.ReplayAll()

        url = (INDEX_URL +
               "?action=row_update&table=instances&obj_id=" + server.id)

        res = self.client.get(url, {},
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertTemplateUsed(res, "horizon/common/_data_table_row.html")
        self.assertContains(res, "test_tenant", 1, 200)
        self.assertContains(res, "instance-host", 1, 200)
        # two instances of name, other name comes from row data-display
        self.assertContains(res, "server_1", 2, 200)
        self.assertContains(res, "10.0.0.1", 1, 200)
        self.assertContains(res, "RAM</th><td>512MB", 1, 200)
        self.assertContains(res, "VCPUs</th><td>1", 1, 200)
        self.assertContains(res, "Size</th><td>0 GB", 1, 200)
        self.assertContains(res, "Active", 1, 200)
        self.assertContains(res, "Running", 1, 200)

    @test.create_stubs({api.nova: ('flavor_list', 'server_list',
                                   'extension_supported', ),
                        api.keystone: ('tenant_list',),
                        api.network: ('servers_update_addresses',)})
    def test_index_options_before_migrate(self):
        servers = self.servers.list()
        api.keystone.tenant_list(IsA(http.HttpRequest)).\
            AndReturn([self.tenants.list(), False])
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True, search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers,
                                             all_tenants=True)
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)).\
            AndReturn(self.flavors.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__migrate")
        self.assertNotContains(res, "instances__confirm")
        self.assertNotContains(res, "instances__revert")

    @test.create_stubs({api.nova: ('flavor_list', 'server_list',
                                   'extension_supported', ),
                        api.keystone: ('tenant_list',),
                        api.network: ('servers_update_addresses',)})
    def test_index_options_after_migrate(self):
        servers = self.servers.list()
        server1 = servers[0]
        server1.status = "VERIFY_RESIZE"
        server2 = servers[2]
        server2.status = "VERIFY_RESIZE"
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])
        search_opts = {'marker': None, 'paginate': True}
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True, search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers,
                                             all_tenants=True)
        api.nova.flavor_list(IsA(http.HttpRequest)).\
            AndReturn(self.flavors.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__confirm")
        self.assertContains(res, "instances__revert")
        self.assertNotContains(res, "instances__migrate")

    @test.create_stubs({api.nova: ('host_list',
                                   'server_get',)})
    def test_instance_live_migrate_get(self):
        server = self.servers.first()
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.host_list(IsA(http.HttpRequest)) \
            .AndReturn(self.hosts.list())

        self.mox.ReplayAll()

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/instances/live_migrate.html')

    @test.create_stubs({api.nova: ('server_get',)})
    def test_instance_live_migrate_get_server_get_exception(self):
        server = self.servers.first()
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('host_list',
                                   'server_get',)})
    def test_instance_live_migrate_list_hypervisor_get_exception(self):
        server = self.servers.first()
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.host_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()
        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('host_list',
                                   'server_get',)})
    def test_instance_live_migrate_list_hypervisor_without_current(self):
        server = self.servers.first()
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.host_list(IsA(http.HttpRequest)) \
            .AndReturn(self.hosts.list())

        self.mox.ReplayAll()

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)
        self.assertNotContains(
            res, "<option value=\"instance-host\">devstack004</option>")
        self.assertContains(
            res, "<option value=\"devstack001\">devstack001</option>")
        self.assertNotContains(
            res, "<option value=\"devstack002\">devstack002</option>")
        self.assertContains(
            res, "<option value=\"devstack003\">devstack003</option>")

    @test.create_stubs({api.nova: ('host_list',
                                   'server_get',
                                   'server_live_migrate',)})
    def test_instance_live_migrate_post(self):
        server = self.servers.first()
        host = self.hosts.first().host_name

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.host_list(IsA(http.HttpRequest)) \
            .AndReturn(self.hosts.list())
        api.nova.server_live_migrate(IsA(http.HttpRequest), server.id, host,
                                     block_migration=False,
                                     disk_over_commit=False) \
            .AndReturn([])

        self.mox.ReplayAll()

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.post(url, {'host': host, 'instance_id': server.id})
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('host_list',
                                   'server_get',
                                   'server_live_migrate',)})
    def test_instance_live_migrate_post_api_exception(self):
        server = self.servers.first()
        host = self.hosts.first().host_name

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.host_list(IsA(http.HttpRequest)) \
            .AndReturn(self.hosts.list())
        api.nova.server_live_migrate(IsA(http.HttpRequest), server.id, host,
                                     block_migration=False,
                                     disk_over_commit=False) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.post(url, {'host': host, 'instance_id': server.id})
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_get',)})
    def test_instance_details_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
