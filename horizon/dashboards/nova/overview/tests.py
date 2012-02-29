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

import datetime

from django import http
from django.core.urlresolvers import reverse
from mox import IsA
from novaclient import exceptions as nova_exceptions

from horizon import api
from horizon import test
from horizon import usage


INDEX_URL = reverse('horizon:nova:overview:index')


class UsageViewTests(test.TestCase):
    def tearDown(self):
        super(UsageViewTests, self).tearDown()
        self.reset_times()  # override_times is called in the tests

    def test_usage(self):
        now = self.override_times()
        usage_obj = api.nova.Usage(self.usages.first())
        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.tenant.id,
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn(usage_obj)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))
        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
        self.assertContains(res, 'form-horizontal')

    def test_usage_csv(self):
        now = self.override_times()
        usage_obj = api.nova.Usage(self.usages.first())
        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1,
                                      now.hour, now.minute,
                                      now.second)
        api.usage_get(IsA(http.HttpRequest),
                      self.tenant.id,
                      timestamp,
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn(usage_obj)

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
                      self.tenant.id,
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
        usage_obj = api.nova.Usage(self.usages.first())
        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1,
                                      now.hour, now.minute,
                                      now.second)
        api.usage_get(IsA(http.HttpRequest),
                      self.tenant.id,
                      timestamp,
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn(usage_obj)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))
        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
