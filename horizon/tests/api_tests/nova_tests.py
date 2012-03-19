# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import http
from mox import IsA
from novaclient.v1_1 import servers

from horizon import api
from horizon import test


class ServerWrapperTests(test.TestCase):
    def test_get_base_attribute(self):
        server = api.nova.Server(self.servers.first(), self.request)
        self.assertEqual(server.id, self.servers.first().id)

    def test_image_name(self):
        image = api.Image(self.images.first())
        self.mox.StubOutWithMock(api.glance, 'image_get_meta')
        api.glance.image_get_meta(IsA(http.HttpRequest),
                                  image.id).AndReturn(image)
        self.mox.ReplayAll()

        server = api.Server(self.servers.first(), self.request)
        self.assertEqual(server.image_name, image.name)


class ComputeApiTests(test.APITestCase):
    def test_server_reboot(self):
        server = self.servers.first()
        HARDNESS = servers.REBOOT_HARD

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        novaclient.servers.reboot(server.id, HARDNESS)
        self.mox.ReplayAll()

        ret_val = api.nova.server_reboot(self.request, server.id)
        self.assertIsNone(ret_val)

    def test_server_vnc_console(self):
        server = self.servers.first()
        console = self.servers.console_data
        console_type = console["console"]["type"]

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get_vnc_console(server.id,
                                           console_type).AndReturn(console)
        self.mox.ReplayAll()

        ret_val = api.server_vnc_console(self.request,
                                         server.id,
                                         console_type)
        self.assertIsInstance(ret_val, api.nova.VNCConsole)

    def test_server_list(self):
        servers = self.servers.list()

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.list(True, {'all_tenants': True}).AndReturn(servers)
        self.mox.ReplayAll()

        ret_val = api.nova.server_list(self.request, all_tenants=True)
        for server in ret_val:
            self.assertIsInstance(server, api.Server)

    def test_usage_get(self):
        novaclient = self.stub_novaclient()
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.get(self.tenant.id,
                             'start',
                             'end').AndReturn(self.usages.first())
        self.mox.ReplayAll()

        ret_val = api.usage_get(self.request, self.tenant.id, 'start', 'end')
        self.assertIsInstance(ret_val, api.nova.Usage)

    def test_usage_list(self):
        usages = self.usages.list()

        novaclient = self.stub_novaclient()
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.list('start', 'end', True).AndReturn(usages)
        self.mox.ReplayAll()

        ret_val = api.usage_list(self.request, 'start', 'end')
        for usage in ret_val:
            self.assertIsInstance(usage, api.Usage)

    def test_server_get(self):
        server = self.servers.first()

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        self.mox.ReplayAll()

        ret_val = api.server_get(self.request, server.id)
        self.assertIsInstance(ret_val, api.nova.Server)

    def test_server_remove_floating_ip(self):
        server = api.nova.Server(self.servers.first(), self.request)
        floating_ip = self.floating_ips.first()

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        novaclient.floating_ips.get(floating_ip.id).AndReturn(floating_ip)
        novaclient.servers.remove_floating_ip(server.id, floating_ip.ip) \
                          .AndReturn(server)
        self.mox.ReplayAll()

        server = api.server_remove_floating_ip(self.request,
                                               server.id,
                                               floating_ip.id)
        self.assertIsInstance(server, api.nova.Server)

    def test_server_add_floating_ip(self):
        server = api.nova.Server(self.servers.first(), self.request)
        floating_ip = self.floating_ips.first()
        novaclient = self.stub_novaclient()

        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        novaclient.floating_ips.get(floating_ip.id).AndReturn(floating_ip)
        novaclient.servers.add_floating_ip(server.id, floating_ip.ip) \
                          .AndReturn(server)
        self.mox.ReplayAll()

        server = api.server_add_floating_ip(self.request,
                                            server.id,
                                            floating_ip.id)
        self.assertIsInstance(server, api.nova.Server)

    def test_tenant_quota_usages(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        floating_ips = self.floating_ips.list()
        quotas = self.quotas.first()
        novaclient = self.stub_novaclient()

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.list(True, {'project_id': '1'}).AndReturn(servers)
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.list().AndReturn(flavors)
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.list().AndReturn(floating_ips)
        novaclient.quotas = self.mox.CreateMockAnything()
        novaclient.quotas.get(self.tenant.id).AndReturn(quotas)
        self.mox.ReplayAll()

        quota_usages = api.tenant_quota_usages(self.request)

        self.assertIsInstance(quota_usages, dict)
        self.assertEquals(quota_usages,
              {'gigabytes': {'available': 1000,
                             'used': 0,
                             'flavor_fields': ['disk',
                                               'OS-FLV-EXT-DATA:ephemeral'],
                             'quota': 1000},
               'instances': {'available': 8,
                             'used': 2,
                             'flavor_fields': [],
                             'quota': 10},
               'ram': {'available': 8976,
                       'used': 1024,
                       'flavor_fields': ['ram'],
                       'quota': 10000},
               'cores': {'available': 8,
                         'used': 2,
                         'flavor_fields': ['vcpus'],
                         'quota': 10},
               'floating_ips': {'available': 0,
                                'used': 1,
                                'flavor_fields': [],
                                'quota': 1}
              })
