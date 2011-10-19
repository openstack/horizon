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

import datetime

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack import utils
from django_openstack.tests.view_tests import base
from openstackx.api import exceptions as api_exceptions
from mox import IsA, IgnoreArg


class InstanceViewTests(base.BaseViewTests):
    def setUp(self):
        super(InstanceViewTests, self).setUp()
        server = self.mox.CreateMock(api.Server)
        server.id = 1
        server.name = 'serverName'
        server.attrs = {'description': 'mydesc'}
        self.servers = (server,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances',
                                      args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
            'django_openstack/dash/instances/index.html')
        self.assertItemsEqual(res.context['instances'], self.servers)

        self.mox.VerifyAll()

    def test_index_server_list_exception(self):
        self.mox.StubOutWithMock(api, 'server_list')
        exception = api_exceptions.ApiException('apiException')
        api.server_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances',
                                      args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/instances/index.html')
        self.assertEqual(len(res.context['instances']), 0)

        self.mox.VerifyAll()

    def test_terminate_instance(self):
        formData = {'method': 'TerminateInstance',
                    'instance': self.servers[0].id,
                    }

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.servers[0].id)).AndReturn(self.servers[0])
        self.mox.StubOutWithMock(api, 'server_delete')
        api.server_delete(IsA(http.HttpRequest),
                          self.servers[0])

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_instances',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_terminate_instance_exception(self):
        formData = {'method': 'TerminateInstance',
                    'instance': self.servers[0].id,
                    }

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.servers[0].id)).AndReturn(self.servers[0])

        exception = api_exceptions.ApiException('ApiException',
                                                message='apiException')
        self.mox.StubOutWithMock(api, 'server_delete')
        api.server_delete(IsA(http.HttpRequest),
                          self.servers[0]).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(unicode))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_instances',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_reboot_instance(self):
        formData = {'method': 'RebootInstance',
                    'instance': self.servers[0].id,
                    }

        self.mox.StubOutWithMock(api, 'server_reboot')
        api.server_reboot(IsA(http.HttpRequest), unicode(self.servers[0].id))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_instances',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_reboot_instance_exception(self):
        formData = {'method': 'RebootInstance',
                    'instance': self.servers[0].id,
                    }

        self.mox.StubOutWithMock(api, 'server_reboot')
        exception = api_exceptions.ApiException('ApiException',
                                                message='apiException')
        api.server_reboot(IsA(http.HttpRequest),
                          unicode(self.servers[0].id)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_instances',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def override_times(self, time=datetime.datetime.now):
        now = datetime.datetime.utcnow()
        utils.time.override_time = \
                datetime.time(now.hour, now.minute, now.second)
        utils.today.override_time = datetime.date(now.year, now.month, now.day)
        utils.utcnow.override_time = now

        return now

    def reset_times(self):
        utils.time.override_time = None
        utils.today.override_time = None
        utils.utcnow.override_time = None

    def test_instance_usage(self):
        TEST_RETURN = 'testReturn'

        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.TEST_TENANT,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      now).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_usage', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/instances/usage.html')

        self.assertEqual(res.context['usage'], TEST_RETURN)

        self.mox.VerifyAll()

        self.reset_times()

    def test_instance_csv_usage(self):
        TEST_RETURN = 'testReturn'

        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.TEST_TENANT,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      now).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_usage', args=[self.TEST_TENANT]) +
                                                    "?format=csv")

        self.assertTemplateUsed(res,
                'django_openstack/dash/instances/usage.csv')

        self.assertEqual(res.context['usage'], TEST_RETURN)

        self.mox.VerifyAll()

        self.reset_times()

    def test_instance_usage_exception(self):
        now = self.override_times()

        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')
        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.TEST_TENANT,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      now).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_usage', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/instances/usage.html')

        self.assertEqual(res.context['usage'], {})

        self.mox.VerifyAll()

        self.reset_times()

    def test_instance_usage_default_tenant(self):
        TEST_RETURN = 'testReturn'

        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.TEST_TENANT,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      now).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_overview'))

        self.assertTemplateUsed(res,
                'django_openstack/dash/instances/usage.html')

        self.assertEqual(res.context['usage'], TEST_RETURN)

        self.mox.VerifyAll()

        self.reset_times()

    def test_instance_console(self):
        CONSOLE_OUTPUT = 'output'
        INSTANCE_ID = self.servers[0].id

        console_mock = self.mox.CreateMock(api.Console)
        console_mock.output = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api, 'console_create')
        api.console_create(IgnoreArg(),
                           unicode(INSTANCE_ID),
                           IgnoreArg()).AndReturn(console_mock)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances_console',
                                      args=[self.TEST_TENANT, INSTANCE_ID]))

        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)

        self.mox.VerifyAll()

    def test_instance_console_exception(self):
        INSTANCE_ID = self.servers[0].id

        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')

        self.mox.StubOutWithMock(api, 'console_create')
        api.console_create(IgnoreArg(),
                           unicode(INSTANCE_ID),
                           IgnoreArg()).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IgnoreArg(), IsA(unicode))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances_console',
                                      args=[self.TEST_TENANT, INSTANCE_ID]))

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_instance_vnc(self):
        INSTANCE_ID = self.servers[0].id
        CONSOLE_OUTPUT = '/vncserver'

        console_mock = self.mox.CreateMock(api.Console)
        console_mock.output = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api, 'console_create')
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.servers[0].id)).AndReturn(self.servers[0])
        api.console_create(IgnoreArg(),
                           unicode(INSTANCE_ID),
                           'vnc').AndReturn(console_mock)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances_vnc',
                                      args=[self.TEST_TENANT, INSTANCE_ID]))

        self.assertRedirectsNoFollow(res,
                CONSOLE_OUTPUT + '&title=serverName(1)')

        self.mox.VerifyAll()

    def test_instance_vnc_exception(self):
        INSTANCE_ID = self.servers[0].id

        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')

        self.mox.StubOutWithMock(api, 'console_create')
        api.console_create(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID),
                           'vnc').AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances_vnc',
                                      args=[self.TEST_TENANT, INSTANCE_ID]))

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_instance_update_get(self):
        INSTANCE_ID = self.servers[0].id

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndReturn(self.servers[0])

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances_update',
                                      args=[self.TEST_TENANT, INSTANCE_ID]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/instances/update.html')

        self.mox.VerifyAll()

    def test_instance_update_get_server_get_exception(self):
        INSTANCE_ID = self.servers[0].id

        exception = api_exceptions.ApiException('apiException')
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_instances_update',
                                      args=[self.TEST_TENANT, INSTANCE_ID]))

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_instance_update_post(self):
        INSTANCE_ID = self.servers[0].id
        NAME = 'myname'
        DESC = 'mydesc'
        formData = {'method': 'UpdateInstance',
                    'instance': self.servers[0].id,
                    'name': NAME,
                    'tenant_id': self.TEST_TENANT,
                    'description': DESC}

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndReturn(self.servers[0])

        self.mox.StubOutWithMock(api, 'server_update')
        api.server_update(IsA(http.HttpRequest),
                          str(INSTANCE_ID), NAME, DESC)

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_instances_update',
                                       args=[self.TEST_TENANT,
                                             INSTANCE_ID]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_instance_update_post_api_exception(self):
        INSTANCE_ID = self.servers[0].id
        NAME = 'myname'
        DESC = 'mydesc'
        formData = {'method': 'UpdateInstance',
                    'instance': INSTANCE_ID,
                    'name': NAME,
                    'tenant_id': self.TEST_TENANT,
                    'description': DESC}

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                           unicode(INSTANCE_ID)).AndReturn(self.servers[0])

        exception = api_exceptions.ApiException('apiException')
        self.mox.StubOutWithMock(api, 'server_update')
        api.server_update(IsA(http.HttpRequest),
                          str(INSTANCE_ID), NAME, DESC).\
                          AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_instances_update',
                                       args=[self.TEST_TENANT,
                                             INSTANCE_ID]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()
