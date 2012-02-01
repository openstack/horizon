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
from django.core.urlresolvers import reverse
from mox import IsA
from novaclient import exceptions as nova_exceptions
from novaclient.v1_1 import usage as nova_usage

from horizon import api
from horizon import test
from horizon import usage


INDEX_URL = reverse('horizon:nova:overview:index')
USAGE_DATA = {
    'total_memory_mb_usage': 64246.89777777778,
    'total_vcpus_usage': 125.48222222222223,
    'total_hours': 125.48222222222223,
    'total_local_gb_usage': 0.0,
    'tenant_id': u'99e7c0197c3643289d89e9854469a4ae',
    'stop': u'2012-01-3123: 30: 46',
    'start': u'2012-01-0100: 00: 00',
    'server_usages': [
        {
            u'memory_mb': 512,
            u'uptime': 442321,
            u'started_at': u'2012-01-2620: 38: 21',
            u'ended_at': None,
            u'name': u'testing',
            u'tenant_id': u'99e7c0197c3643289d89e9854469a4ae',
            u'state': u'active',
            u'hours': 122.87361111111112,
            u'vcpus': 1,
            u'flavor': u'm1.tiny',
            u'local_gb': 0
        },
        {
            u'memory_mb': 512,
            u'uptime': 9367,
            u'started_at': u'2012-01-3120: 54: 15',
            u'ended_at': None,
            u'name': u'instance2',
            u'tenant_id': u'99e7c0197c3643289d89e9854469a4ae',
            u'state': u'active',
            u'hours': 2.608611111111111,
            u'vcpus': 1,
            u'flavor': u'm1.tiny',
            u'local_gb': 0
        }
    ]
}


class UsageViewTests(test.BaseViewTests):
    def setUp(self):
        super(UsageViewTests, self).setUp()
        usage_resource = nova_usage.Usage(nova_usage.UsageManager, USAGE_DATA)
        self.usage = api.nova.Usage(usage_resource)
        self.usages = (self.usage,)

    def tearDown(self):
        super(UsageViewTests, self).tearDown()
        self.reset_times()

    def test_usage(self):
        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.TEST_TENANT,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn(self.usage)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))

        self.assertTemplateUsed(res, 'nova/overview/usage.html')

        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))

    def test_usage_csv(self):
        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1,
                                      now.hour, now.minute,
                                      now.second)
        api.usage_get(IsA(http.HttpRequest),
                      self.TEST_TENANT,
                      timestamp,
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn(self.usage)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index') +
                              "?format=csv")

        self.assertTemplateUsed(res, 'nova/overview/usage.csv')

        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))

    def test_usage_exception(self):
        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1, now.hour,
                                      now.minute, now.second)
        exception = nova_exceptions.ClientException(500)
        api.usage_get(IsA(http.HttpRequest),
                      self.TEST_TENANT,
                      timestamp,
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))

        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

    def test_usage_default_tenant(self):
        now = self.override_times()

        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1,
                                      now.hour, now.minute,
                                      now.second)
        api.usage_get(IsA(http.HttpRequest),
                      self.TEST_TENANT,
                      timestamp,
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn(self.usage)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))

        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
