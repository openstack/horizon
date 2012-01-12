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
from mox import IsA, IgnoreArg
from novaclient import exceptions as nova_exceptions

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:overview:index')


class InstanceViewTests(test.BaseViewTests):
    def setUp(self):
        super(InstanceViewTests, self).setUp()
        self.now = self.override_times()

        server = api.Server(None, self.request)
        server.id = "1"
        server.name = 'serverName'
        server.status = "ACTIVE"

        volume = api.Volume(self.request)
        volume.id = "1"

        self.servers = (server,)
        self.volumes = (volume,)

    def tearDown(self):
        super(InstanceViewTests, self).tearDown()
        self.reset_times()

    def test_usage(self):
        TEST_RETURN = 'testReturn'

        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.TEST_TENANT,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      now).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))

        self.assertTemplateUsed(res, 'nova/overview/usage.html')

        self.assertEqual(res.context['usage'], TEST_RETURN)

    def test_usage_csv(self):
        TEST_RETURN = 'testReturn'

        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(self.now.year, self.now.month, 1,
                                      self.now.hour, self.now.minute,
                                      self.now.second)
        api.usage_get(IsA(http.HttpRequest),
                      self.TEST_TENANT,
                      timestamp,
                      self.now).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index') +
                              "?format=csv")

        self.assertTemplateUsed(res, 'nova/overview/usage.csv')

        self.assertEqual(res.context['usage'], TEST_RETURN)

    def test_usage_exception(self):
        self.mox.StubOutWithMock(api, 'usage_get')

        timestamp = datetime.datetime(self.now.year, self.now.month, 1,
                                      self.now.hour, self.now.minute,
                                      self.now.second)
        exception = nova_exceptions.ClientException(500)
        api.usage_get(IsA(http.HttpRequest),
                      self.TEST_TENANT,
                      timestamp,
                      self.now).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))

        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertEqual(res.context['usage']._apiresource, None)

    def test_usage_default_tenant(self):
        TEST_RETURN = 'testReturn'

        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(self.now.year, self.now.month, 1,
                                      self.now.hour, self.now.minute,
                                      self.now.second)
        api.usage_get(IsA(http.HttpRequest),
                      self.TEST_TENANT,
                      timestamp,
                      self.now).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))

        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertEqual(res.context['usage'], TEST_RETURN)
