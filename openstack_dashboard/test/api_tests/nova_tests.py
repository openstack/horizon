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

from mox3.mox import IsA  # noqa
from novaclient import exceptions as nova_exceptions
from novaclient.v2 import servers
import six

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
        novaclient.servers.list(True, {'all_tenants': True}).AndReturn(servers)
        self.mox.ReplayAll()

        ret_val, has_more = api.nova.server_list(self.request,
                                                 all_tenants=True)
        for server in ret_val:
            self.assertIsInstance(server, api.nova.Server)

    def test_server_list_pagination(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.list(True,
                                {'all_tenants': True,
                                 'marker': None,
                                 'limit': page_size + 1}).AndReturn(servers)
        self.mox.ReplayAll()

        ret_val, has_more = api.nova.server_list(self.request,
                                                 {'marker': None,
                                                  'paginate': True},
                                                 all_tenants=True)
        for server in ret_val:
            self.assertIsInstance(server, api.nova.Server)
        self.assertFalse(has_more)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_server_list_pagination_more(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 1)
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.list(True,
                                {'all_tenants': True,
                                 'marker': None,
                                 'limit': page_size + 1}) \
            .AndReturn(servers[:page_size + 1])
        self.mox.ReplayAll()

        ret_val, has_more = api.nova.server_list(self.request,
                                                 {'marker': None,
                                                  'paginate': True},
                                                 all_tenants=True)
        for server in ret_val:
            self.assertIsInstance(server, api.nova.Server)
        self.assertEqual(page_size, len(ret_val))
        self.assertTrue(has_more)

    def test_usage_get(self):
        novaclient = self.stub_novaclient()
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.get(self.tenant.id,
                             'start',
                             'end').AndReturn(self.usages.first())
        self.mox.ReplayAll()

        ret_val = api.nova.usage_get(self.request, self.tenant.id,
                                     'start', 'end')
        self.assertIsInstance(ret_val, api.nova.NovaUsage)

    def test_usage_list(self):
        usages = self.usages.list()

        novaclient = self.stub_novaclient()
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.list('start', 'end', True).AndReturn(usages)
        self.mox.ReplayAll()

        ret_val = api.nova.usage_list(self.request, 'start', 'end')
        for usage in ret_val:
            self.assertIsInstance(usage, api.nova.NovaUsage)

    def test_server_get(self):
        server = self.servers.first()

        novaclient = self.stub_novaclient()
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
        for key, val in six.iteritems(values):
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

        novaclient.hypervisors = self.mox.CreateMockAnything()
        novaclient.hypervisors.search('host', True).AndReturn([hypervisor])

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server_uuid).AndReturn(server)
        novaclient.servers.migrate(server_uuid)

        self.mox.ReplayAll()

        ret_val = api.nova.migrate_host(self.request, "host", True, True,
                                        True)
        self.assertTrue(ret_val)
