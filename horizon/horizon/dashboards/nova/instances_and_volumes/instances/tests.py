# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from mox import IsA, IgnoreArg
from novaclient import exceptions as nova_exceptions

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:instances_and_volumes:index')


class InstanceViewTests(test.BaseViewTests):
    def setUp(self):
        super(InstanceViewTests, self).setUp()
        self.now = self.override_times()

        server = api.Server(None, self.request)
        server.id = "1"
        server.name = 'serverName'
        server.status = "ACTIVE"
        server.flavor = {'id': '1'}

        flavor = api.nova.Flavor(None)
        flavor.id = '1'

        volume = api.Volume(self.request)
        volume.id = "1"

        self.servers = (server,)
        self.volumes = (volume,)
        self.flavors = (flavor,)

    def tearDown(self):
        super(InstanceViewTests, self).tearDown()
        self.reset_times()

    def test_terminate_instance(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')

        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors)
        api.server_delete(IsA(http.HttpRequest),
                          self.servers[0].id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % self.servers[0].id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_terminate_instance_exception(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')

        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors)
        exception = nova_exceptions.ClientException(500)
        api.server_delete(IsA(http.HttpRequest),
                          self.servers[0].id).AndRaise(exception)

        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % self.servers[0].id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_reboot_instance(self):
        self.mox.StubOutWithMock(api, 'server_reboot')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)
        api.server_reboot(IsA(http.HttpRequest), unicode(self.servers[0].id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % self.servers[0].id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_reboot_instance_exception(self):
        self.mox.StubOutWithMock(api, 'server_reboot')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)
        exception = nova_exceptions.ClientException(500)
        api.server_reboot(IsA(http.HttpRequest),
                          unicode(self.servers[0].id)).AndRaise(exception)

        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % self.servers[0].id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_console(self):
        CONSOLE_OUTPUT = 'output'
        INSTANCE_ID = self.servers[0].id

        self.mox.StubOutWithMock(api, 'server_console_output')
        api.server_console_output(IsA(http.HttpRequest),
                                  unicode(INSTANCE_ID),
                                  tail_length=None).AndReturn(CONSOLE_OUTPUT)

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:instances:console',
                        args=[INSTANCE_ID]))

        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)

    def test_instance_vnc(self):
        INSTANCE_ID = self.servers[0].id
        CONSOLE_OUTPUT = '/vncserver'

        console_mock = self.mox.CreateMock(api.VNCConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api, 'server_vnc_console')
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.servers[0].id)).AndReturn(self.servers[0])
        api.server_vnc_console(IgnoreArg(),
                               unicode(INSTANCE_ID)).AndReturn(console_mock)

        self.mox.ReplayAll()

        res = self.client.get(
                    reverse('horizon:nova:instances_and_volumes:instances:vnc',
                            args=[INSTANCE_ID]))

        self.assertRedirectsNoFollow(res,
                CONSOLE_OUTPUT + '&title=serverName(1)')

    def test_instance_vnc_exception(self):
        INSTANCE_ID = self.servers[0].id

        exception = nova_exceptions.ClientException(500)

        self.mox.StubOutWithMock(api, 'server_vnc_console')
        api.server_vnc_console(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(
                    reverse('horizon:nova:instances_and_volumes:instances:vnc',
                            args=[INSTANCE_ID]))

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_get(self):
        INSTANCE_ID = self.servers[0].id

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndReturn(self.servers[0])

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:instances:update',
                        args=[INSTANCE_ID]))

        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/instances/update.html')

    def test_instance_update_get_server_get_exception(self):
        INSTANCE_ID = self.servers[0].id

        exception = nova_exceptions.ClientException(500)
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:instances:update',
                        args=[INSTANCE_ID]))

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_post(self):
        INSTANCE_ID = self.servers[0].id
        NAME = 'myname'
        formData = {'method': 'UpdateInstance',
                    'instance': self.servers[0].id,
                    'name': NAME,
                    'tenant_id': self.TEST_TENANT}

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndReturn(self.servers[0])

        self.mox.StubOutWithMock(api, 'server_update')
        api.server_update(IsA(http.HttpRequest),
                          str(INSTANCE_ID), NAME)

        self.mox.ReplayAll()

        res = self.client.post(
                reverse('horizon:nova:instances_and_volumes:instances:update',
                        args=[INSTANCE_ID]), formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_post_api_exception(self):
        SERVER = self.servers[0]

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'server_update')

        api.server_get(IsA(http.HttpRequest), unicode(SERVER.id)) \
                      .AndReturn(self.servers[0])
        exception = nova_exceptions.ClientException(500)
        api.server_update(IsA(http.HttpRequest), str(SERVER.id), SERVER.name) \
                          .AndRaise(exception)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': SERVER.id,
                    'name': SERVER.name,
                    'tenant_id': self.TEST_TENANT}
        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[SERVER.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
