# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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

from __future__ import absolute_import

from django.conf import settings
from django import http
from django.test.utils import override_settings

from mox3.mox import IsA
from novaclient import api_versions
from novaclient import exceptions as nova_exceptions
from novaclient.v2 import flavor_access as nova_flavor_access
from novaclient.v2 import servers

from horizon import exceptions as horizon_exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class ServerWrapperTests(test.TestCase):

    def test_get_base_attribute(self):
        server = api.nova.Server(self.servers.first(), self.request)
        self.assertEqual(self.servers.first().id, server.id)

    def test_image_name(self):
        image = self.images.first()
        self.mox.StubOutWithMock(api.glance, 'image_get')
        api.glance.image_get(IsA(http.HttpRequest),
                             image.id).AndReturn(image)
        self.mox.ReplayAll()

        server = api.nova.Server(self.servers.first(), self.request)
        self.assertEqual(image.name, server.image_name)

    def test_image_name_no_glance_service(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api.glance, 'image_get')
        api.glance.image_get(IsA(http.HttpRequest),
                             server.image['id']).AndRaise(
            horizon_exceptions.ServiceCatalogException('image'))
        self.mox.ReplayAll()

        server = api.nova.Server(server, self.request)
        self.assertIsNone(server.image_name)


class ComputeApiTests(test.APITestCase):

    def test_server_reboot(self):
        server = self.servers.first()
        HARDNESS = servers.REBOOT_HARD

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.reboot(server.id, HARDNESS)
        self.mox.ReplayAll()

        ret_val = api.nova.server_reboot(self.request, server.id)
        self.assertIsNone(ret_val)

    def test_server_soft_reboot(self):
        server = self.servers.first()
        HARDNESS = servers.REBOOT_SOFT

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.reboot(server.id, HARDNESS)
        self.mox.ReplayAll()

        ret_val = api.nova.server_reboot(self.request, server.id, HARDNESS)
        self.assertIsNone(ret_val)

    def test_server_vnc_console(self):
        server = self.servers.first()
        console = self.servers.vnc_console_data
        console_type = console["console"]["type"]

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get_vnc_console(server.id,
                                           console_type).AndReturn(console)
        self.mox.ReplayAll()

        ret_val = api.nova.server_vnc_console(self.request,
                                              server.id,
                                              console_type)
        self.assertIsInstance(ret_val, api.nova.VNCConsole)

    def test_server_spice_console(self):
        server = self.servers.first()
        console = self.servers.spice_console_data
        console_type = console["console"]["type"]

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get_spice_console(server.id,
                                             console_type).AndReturn(console)
        self.mox.ReplayAll()

        ret_val = api.nova.server_spice_console(self.request,
                                                server.id,
                                                console_type)
        self.assertIsInstance(ret_val, api.nova.SPICEConsole)

    def test_server_rdp_console(self):
        server = self.servers.first()
        console = self.servers.rdp_console_data
        console_type = console["console"]["type"]

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get_rdp_console(server.id,
                                           console_type).AndReturn(console)
        self.mox.ReplayAll()

        ret_val = api.nova.server_rdp_console(self.request,
                                              server.id,
                                              console_type)
        self.assertIsInstance(ret_val, api.nova.RDPConsole)

    def test_server_list(self):
        servers = self.servers.list()

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.servers.list(True, {'all_tenants': True}).AndReturn(servers)
        self.mox.ReplayAll()

        ret_val, has_more = api.nova.server_list(
            self.request,
            search_opts={'all_tenants': True})
        for server in ret_val:
            self.assertIsInstance(server, api.nova.Server)

    def test_server_list_pagination(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.servers.list(True,
                                {'all_tenants': True,
                                 'marker': None,
                                 'limit': page_size + 1}).AndReturn(servers)
        self.mox.ReplayAll()

        ret_val, has_more = api.nova.server_list(self.request,
                                                 {'marker': None,
                                                  'paginate': True,
                                                  'all_tenants': True})
        for server in ret_val:
            self.assertIsInstance(server, api.nova.Server)
        self.assertFalse(has_more)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_server_list_pagination_more(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 1)
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.servers.list(True,
                                {'all_tenants': True,
                                 'marker': None,
                                 'limit': page_size + 1}) \
            .AndReturn(servers[:page_size + 1])
        self.mox.ReplayAll()

        ret_val, has_more = api.nova.server_list(self.request,
                                                 {'marker': None,
                                                  'paginate': True,
                                                  'all_tenants': True})
        for server in ret_val:
            self.assertIsInstance(server, api.nova.Server)
        self.assertEqual(page_size, len(ret_val))
        self.assertTrue(has_more)

    def test_usage_get(self):
        novaclient = self.stub_novaclient()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn(
            api_versions.APIVersion('2.1'))
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.get(self.tenant.id,
                             'start',
                             'end').AndReturn(self.usages.first())
        self.mox.ReplayAll()

        ret_val = api.nova.usage_get(self.request, self.tenant.id,
                                     'start', 'end')
        self.assertIsInstance(ret_val, api.nova.NovaUsage)

    def test_usage_get_paginated(self):
        novaclient = self.stub_novaclient()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn(
            api_versions.APIVersion('2.40'))
        novaclient.api_version = api_versions.APIVersion('2.40')
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.get(self.tenant.id, 'start', 'end')\
            .AndReturn(self.usages.first())
        novaclient.usage.get(
            self.tenant.id,
            'start',
            'end',
            marker=u'063cf7f3-ded1-4297-bc4c-31eae876cc93',
        ).AndReturn({})
        self.mox.ReplayAll()

        ret_val = api.nova.usage_get(self.request, self.tenant.id,
                                     'start', 'end')
        self.assertIsInstance(ret_val, api.nova.NovaUsage)

    def test_usage_list(self):
        usages = self.usages.list()

        novaclient = self.stub_novaclient()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn(
            api_versions.APIVersion('2.1'))
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.list('start', 'end', True).AndReturn(usages)
        self.mox.ReplayAll()

        ret_val = api.nova.usage_list(self.request, 'start', 'end')
        for usage in ret_val:
            self.assertIsInstance(usage, api.nova.NovaUsage)

    def test_usage_list_paginated(self):
        usages = self.usages.list()

        novaclient = self.stub_novaclient()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn(
            api_versions.APIVersion('2.40'))
        novaclient.api_version = api_versions.APIVersion('2.40')
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.list('start', 'end', True).AndReturn(usages)
        novaclient.usage.list(
            'start',
            'end',
            True,
            marker=u'063cf7f3-ded1-4297-bc4c-31eae876cc93',
        ).AndReturn({})
        self.mox.ReplayAll()

        ret_val = api.nova.usage_list(self.request, 'start', 'end')
        for usage in ret_val:
            self.assertIsInstance(usage, api.nova.NovaUsage)

    def test_server_get(self):
        server = self.servers.first()

        novaclient = self.stub_novaclient()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        self.mox.ReplayAll()

        ret_val = api.nova.server_get(self.request, server.id)
        self.assertIsInstance(ret_val, api.nova.Server)

    def test_server_metadata_update(self):
        server = self.servers.first()
        metadata = {'foo': 'bar'}

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.set_meta(server.id, metadata)
        self.mox.ReplayAll()

        ret_val = api.nova.server_metadata_update(self.request,
                                                  server.id,
                                                  metadata)
        self.assertIsNone(ret_val)

    def test_server_metadata_delete(self):
        server = self.servers.first()
        keys = ['a', 'b']

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.delete_meta(server.id, keys)
        self.mox.ReplayAll()

        ret_val = api.nova.server_metadata_delete(self.request,
                                                  server.id,
                                                  keys)
        self.assertIsNone(ret_val)

    def _test_absolute_limits(self, values, expected_results):
        limits = self.mox.CreateMockAnything()
        limits.absolute = []
        for key, val in values.items():
            limit = self.mox.CreateMockAnything()
            limit.name = key
            limit.value = val
            limits.absolute.append(limit)

        novaclient = self.stub_novaclient()
        novaclient.limits = self.mox.CreateMockAnything()
        novaclient.limits.get(reserved=True).AndReturn(limits)
        self.mox.ReplayAll()

        ret_val = api.nova.tenant_absolute_limits(self.request, reserved=True)
        for key in expected_results.keys():
            self.assertEqual(expected_results[key], ret_val[key])

    def test_absolute_limits_handle_unlimited(self):
        values = {"maxTotalCores": -1, "maxTotalInstances": 10}
        expected_results = {"maxTotalCores": float("inf"),
                            "maxTotalInstances": 10}
        self._test_absolute_limits(values, expected_results)

    def test_absolute_limits_negative_used_workaround(self):
        values = {"maxTotalCores": -1,
                  "maxTotalInstances": 10,
                  "totalInstancesUsed": -1,
                  "totalCoresUsed": -1,
                  "totalRAMUsed": -2048,
                  "totalSecurityGroupsUsed": 1,
                  "totalFloatingIpsUsed": 0,
                  }
        expected_results = {"maxTotalCores": float("inf"),
                            "maxTotalInstances": 10,
                            "totalInstancesUsed": 0,
                            "totalCoresUsed": 0,
                            "totalRAMUsed": 0,
                            "totalSecurityGroupsUsed": 1,
                            "totalFloatingIpsUsed": 0,
                            }
        self._test_absolute_limits(values, expected_results)

    def test_cold_migrate_host_succeed(self):
        hypervisor = self.hypervisors.first()
        novaclient = self.stub_novaclient()

        novaclient.hypervisors = self.mox.CreateMockAnything()
        novaclient.hypervisors.search('host', True).AndReturn([hypervisor])

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.migrate("test_uuid")

        self.mox.ReplayAll()

        ret_val = api.nova.migrate_host(self.request, "host", False, True,
                                        True)

        self.assertTrue(ret_val)

    def test_cold_migrate_host_fails(self):
        hypervisor = self.hypervisors.first()
        novaclient = self.stub_novaclient()

        novaclient.hypervisors = self.mox.CreateMockAnything()
        novaclient.hypervisors.search('host', True).AndReturn([hypervisor])

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.migrate("test_uuid").AndRaise(
            nova_exceptions.ClientException(404))

        self.mox.ReplayAll()

        self.assertRaises(nova_exceptions.ClientException,
                          api.nova.migrate_host,
                          self.request, "host", False, True, True)

    def test_live_migrate_host_with_active_vm(self):
        hypervisor = self.hypervisors.first()
        server = self.servers.first()
        novaclient = self.stub_novaclient()
        server_uuid = hypervisor.servers[0]["uuid"]

        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.hypervisors = self.mox.CreateMockAnything()
        novaclient.hypervisors.search('host', True).AndReturn([hypervisor])

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server_uuid).AndReturn(server)
        novaclient.servers.live_migrate(server_uuid, None, True, True)

        self.mox.ReplayAll()

        ret_val = api.nova.migrate_host(self.request, "host", True, True,
                                        True)

        self.assertTrue(ret_val)

    def test_live_migrate_host_with_paused_vm(self):
        hypervisor = self.hypervisors.first()
        server = self.servers.list()[3]
        novaclient = self.stub_novaclient()
        server_uuid = hypervisor.servers[0]["uuid"]

        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.hypervisors = self.mox.CreateMockAnything()
        novaclient.hypervisors.search('host', True).AndReturn([hypervisor])

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server_uuid).AndReturn(server)
        novaclient.servers.live_migrate(server_uuid, None, True, True)

        self.mox.ReplayAll()

        ret_val = api.nova.migrate_host(self.request, "host", True, True,
                                        True)

        self.assertTrue(ret_val)

    def test_live_migrate_host_without_running_vm(self):
        hypervisor = self.hypervisors.first()
        server = self.servers.list()[1]
        novaclient = self.stub_novaclient()
        server_uuid = hypervisor.servers[0]["uuid"]

        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.hypervisors = self.mox.CreateMockAnything()
        novaclient.hypervisors.search('host', True).AndReturn([hypervisor])

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server_uuid).AndReturn(server)
        novaclient.servers.migrate(server_uuid)

        self.mox.ReplayAll()

        ret_val = api.nova.migrate_host(self.request, "host", True, True,
                                        True)
        self.assertTrue(ret_val)

    """Flavor Tests"""

    def test_flavor_list_no_extras(self):
        flavors = self.flavors.list()
        novaclient = self.stub_novaclient()

        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.list(is_public=True).AndReturn(flavors)
        self.mox.ReplayAll()
        api_flavors = api.nova.flavor_list(self.request)
        self.assertEqual(len(flavors), len(api_flavors))

    def test_flavor_get_no_extras(self):
        flavor = self.flavors.list()[1]
        novaclient = self.stub_novaclient()

        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.get(flavor.id).AndReturn(flavor)

        self.mox.ReplayAll()
        api_flavor = api.nova.flavor_get(self.request, flavor.id)
        self.assertEqual(api_flavor.id, flavor.id)

    def _test_flavor_list_paged(self, reversed_order=False, paginate=True):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
        flavors = self.flavors.list()
        order = 'asc' if reversed_order else 'desc'
        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        if paginate:
            novaclient.flavors.list(is_public=True,
                                    marker=None,
                                    limit=page_size + 1,
                                    sort_key='name',
                                    sort_dir=order).AndReturn(flavors)
        else:
            novaclient.flavors.list(is_public=True).AndReturn(flavors)

        self.mox.ReplayAll()
        api_flavors, has_more, has_prev = api.nova\
                                             .flavor_list_paged(
                                                 self.request,
                                                 True,
                                                 False,
                                                 None,
                                                 paginate=paginate,
                                                 reversed_order=reversed_order)
        for flavor in api_flavors:
            self.assertIsInstance(flavor, type(flavors[0]))
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_flavor_list_pagination_more_and_prev(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 1)
        flavors = self.flavors.list()
        marker = flavors[0].id
        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.list(is_public=True,
                                marker=marker,
                                limit=page_size + 1,
                                sort_key='name',
                                sort_dir='desc')\
            .AndReturn(flavors[1:page_size + 2])

        self.mox.ReplayAll()
        api_flavors, has_more, has_prev = api.nova\
                                             .flavor_list_paged(
                                                 self.request,
                                                 True,
                                                 False,
                                                 marker,
                                                 paginate=True)
        for flavor in api_flavors:
            self.assertIsInstance(flavor, type(flavors[0]))
        self.assertEqual(page_size, len(api_flavors))
        self.assertTrue(has_more)
        self.assertTrue(has_prev)

    def test_flavor_list_paged_default_order(self):
        self._test_flavor_list_paged()

    def test_flavor_list_paged_reversed_order(self):
        self._test_flavor_list_paged(reversed_order=True)

    def test_flavor_list_paged_paginate_false(self):
        self._test_flavor_list_paged(paginate=False)

    def test_flavor_create(self):
        flavor = self.flavors.first()

        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.create(flavor.name, flavor.ram,
                                  flavor.vcpus, flavor.disk,
                                  flavorid='auto',
                                  ephemeral=0,
                                  swap=0,
                                  is_public=True,
                                  rxtx_factor=1).AndReturn(flavor)

        self.mox.ReplayAll()

        api_flavor = api.nova.flavor_create(self.request,
                                            flavor.name,
                                            flavor.ram,
                                            flavor.vcpus,
                                            flavor.disk)

        self.assertIsInstance(api_flavor, type(flavor))
        self.assertEqual(flavor.name, api_flavor.name)
        self.assertEqual(flavor.ram, api_flavor.ram)
        self.assertEqual(flavor.vcpus, api_flavor.vcpus)
        self.assertEqual(flavor.disk, api_flavor.disk)
        self.assertEqual(0, api_flavor.ephemeral)
        self.assertEqual(0, api_flavor.swap)
        self.assertTrue(api_flavor.is_public)
        self.assertEqual(1, api_flavor.rxtx_factor)

    def test_flavor_delete(self):
        flavor = self.flavors.first()
        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.delete(flavor.id)

        self.mox.ReplayAll()

        api_val = api.nova.flavor_delete(self.request, flavor.id)

        self.assertIsNone(api_val)

    @test.create_stubs({api.nova: ('flavor_access_list',)})
    def test_flavor_access_list(self):
        flavor_access = self.flavor_access.list()
        flavor = [f for f in self.flavors.list() if f.id ==
                  flavor_access[0].flavor_id][0]

        api.nova.flavor_access_list(self.request, flavor)\
            .AndReturn(flavor_access)

        self.mox.ReplayAll()
        api_flavor_access = api.nova.flavor_access_list(self.request, flavor)
        self.assertEqual(len(flavor_access), len(api_flavor_access))
        for access in api_flavor_access:
            self.assertIsInstance(access, nova_flavor_access.FlavorAccess)
            self.assertEqual(access.flavor_id, flavor.id)

    def test_add_tenant_to_flavor(self):
        flavor_access = [self.flavor_access.first()]
        flavor = [f for f in self.flavors.list() if f.id ==
                  flavor_access[0].flavor_id][0]
        tenant = [t for t in self.tenants.list() if t.id ==
                  flavor_access[0].tenant_id][0]
        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavor_access = self.mox.CreateMockAnything()

        novaclient.flavor_access\
                  .add_tenant_access(flavor=flavor,
                                     tenant=tenant)\
                  .AndReturn(flavor_access)

        self.mox.ReplayAll()
        api_flavor_access = api.nova.add_tenant_to_flavor(self.request,
                                                          flavor,
                                                          tenant)
        self.assertIsInstance(api_flavor_access, list)
        self.assertEqual(len(flavor_access), len(api_flavor_access))

        for access in api_flavor_access:
            self.assertEqual(access.flavor_id, flavor.id)
            self.assertEqual(access.tenant_id, tenant.id)

    def test_remove_tenant_from_flavor(self):
        flavor_access = [self.flavor_access.first()]
        flavor = [f for f in self.flavors.list() if f.id ==
                  flavor_access[0].flavor_id][0]
        tenant = [t for t in self.tenants.list() if t.id ==
                  flavor_access[0].tenant_id][0]

        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavor_access = self.mox.CreateMockAnything()

        novaclient.flavor_access\
                  .remove_tenant_access(flavor=flavor,
                                        tenant=tenant)\
                  .AndReturn([])

        self.mox.ReplayAll()
        api_val = api.nova.remove_tenant_from_flavor(self.request,
                                                     flavor,
                                                     tenant)
        self.assertEqual(len(api_val), len([]))
        self.assertIsInstance(api_val, list)

    def test_server_group_list(self):
        server_groups = self.server_groups.list()

        novaclient = self.stub_novaclient()
        novaclient.server_groups = self.mox.CreateMockAnything()
        novaclient.server_groups.list().AndReturn(server_groups)
        self.mox.ReplayAll()

        ret_val = api.nova.server_group_list(self.request)
        self.assertIsInstance(ret_val, list)
        self.assertEqual(len(ret_val), len(server_groups))
