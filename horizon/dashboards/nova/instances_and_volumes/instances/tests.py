# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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
from mox import IsA, IgnoreArg
from novaclient import exceptions as nova_exceptions

from horizon import api
from horizon import test
from .tabs import InstanceDetailTabs


INDEX_URL = reverse('horizon:nova:instances_and_volumes:index')


class InstanceViewTests(test.TestCase):
    def setUp(self):
        super(InstanceViewTests, self).setUp()
        self.now = self.override_times()

    def tearDown(self):
        super(InstanceViewTests, self).tearDown()
        self.reset_times()

    def test_terminate_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_terminate_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        exc = nova_exceptions.ClientException(500)
        api.server_delete(IsA(http.HttpRequest), server.id).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_pause_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_pause')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_pause(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_pause_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_pause')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        exc = nova_exceptions.ClientException(500)
        api.server_pause(IsA(http.HttpRequest), server.id).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_unpause_instance(self):
        server = self.servers.first()
        server.status = "PAUSED"
        self.mox.StubOutWithMock(api, 'server_unpause')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_unpause(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_unpause_instance_exception(self):
        server = self.servers.first()
        server.status = "PAUSED"
        self.mox.StubOutWithMock(api, 'server_unpause')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        exc = nova_exceptions.ClientException(500)
        api.server_unpause(IsA(http.HttpRequest), server.id).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_reboot_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_reboot')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_reboot(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_reboot_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_reboot')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        exc = nova_exceptions.ClientException(500)
        api.server_reboot(IsA(http.HttpRequest), server.id).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_suspend_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_suspend')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_suspend(IsA(http.HttpRequest), unicode(server.id))
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_suspend_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_suspend')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        exception = nova_exceptions.ClientException(500)
        api.server_suspend(IsA(http.HttpRequest),
                          unicode(server.id)).AndRaise(exception)
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_resume_instance(self):
        server = self.servers.first()
        server.status = "SUSPENDED"
        self.mox.StubOutWithMock(api, 'server_resume')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_resume(IsA(http.HttpRequest), unicode(server.id))
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_resume_instance_exception(self):
        server = self.servers.first()
        server.status = "SUSPENDED"
        self.mox.StubOutWithMock(api, 'server_resume')
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        exception = nova_exceptions.ClientException(500)
        api.server_resume(IsA(http.HttpRequest),
                          unicode(server.id)).AndRaise(exception)
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_log(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = 'output'

        self.mox.StubOutWithMock(api, 'server_console_output')
        api.server_console_output(IsA(http.HttpRequest),
                                  server.id).AndReturn(CONSOLE_OUTPUT)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:console',
                      args=[server.id])
        tg = InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)
        self.assertNoMessages()
        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)

    def test_instance_log_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_console_output')
        exc = nova_exceptions.ClientException(500)
        api.server_console_output(IsA(http.HttpRequest),
                                  server.id).AndRaise(exc)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:console',
                      args=[server.id])
        tg = InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)
        self.assertContains(res, "Unable to get log for")

    def test_instance_vnc(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'

        console_mock = self.mox.CreateMock(api.VNCConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api, 'server_vnc_console')
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_vnc_console(IgnoreArg(), server.id).AndReturn(console_mock)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_OUTPUT + '&title=%s(1)' % server.name
        self.assertRedirectsNoFollow(res, redirect)

    def test_instance_vnc_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_vnc_console')
        exc = nova_exceptions.ClientException(500)
        api.server_vnc_console(IsA(http.HttpRequest), server.id).AndRaise(exc)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_get(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/instances/update.html')

    def test_instance_update_get_server_get_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_get')
        exc = nova_exceptions.ClientException(500)
        api.server_get(IsA(http.HttpRequest), server.id).AndRaise(exc)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_post(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'server_update')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_update(IsA(http.HttpRequest), server.id, server.name)
        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': server.id,
                    'name': server.name,
                    'tenant_id': self.tenant.id}
        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_post_api_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'server_update')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        exc = nova_exceptions.ClientException(500)
        api.server_update(IsA(http.HttpRequest), server.id, server.name) \
                          .AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': server.id,
                    'name': server.name,
                    'tenant_id': self.tenant.id}
        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)
