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

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class ServerWrapperTests(test.TestCase):
    def test_get_base_attribute(self):
        server = api.nova.Server(self.servers.first(), self.request)
        self.assertEqual(server.id, self.servers.first().id)

    def test_image_name(self):
        image = self.images.first()
        self.mox.StubOutWithMock(api.glance, 'image_get')
        api.glance.image_get(IsA(http.HttpRequest),
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
        self.assertIsInstance(ret_val, api.nova.NovaUsage)

    def test_usage_list(self):
        usages = self.usages.list()

        novaclient = self.stub_novaclient()
        novaclient.usage = self.mox.CreateMockAnything()
        novaclient.usage.list('start', 'end', True).AndReturn(usages)
        self.mox.ReplayAll()

        ret_val = api.usage_list(self.request, 'start', 'end')
        for usage in ret_val:
            self.assertIsInstance(usage, api.NovaUsage)

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
