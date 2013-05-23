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
from django.utils import timezone

from mox import IsA, Func

from openstack_dashboard import api
from openstack_dashboard import usage
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:overview:index')


class UsageViewTests(test.TestCase):
    def test_usage(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        quota_data = self.quota_usages.first()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(quotas, 'tenant_quota_usages')
        api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                           datetime.datetime(now.year, now.month, 1, 0, 0, 0),
                           Func(usage.almost_now)) \
                           .AndReturn(usage_obj)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
        self.assertContains(res, 'form-horizontal')

    def test_unauthorized(self):
        exc = self.exceptions.nova_unauthorized
        now = timezone.now()
        quota_data = self.quota_usages.first()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(quotas, 'tenant_quota_usages')
        api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                           datetime.datetime(now.year, now.month, 1, 0, 0, 0),
                           Func(usage.almost_now)) \
                           .AndRaise(exc)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(quota_data)
        self.mox.ReplayAll()

        url = reverse('horizon:project:overview:index')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertMessageCount(res, error=1)
        self.assertContains(res, 'Unauthorized:')

    def test_usage_csv(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        quota_data = self.quota_usages.first()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(quotas, 'tenant_quota_usages')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           timestamp,
                           Func(usage.almost_now)) \
                           .AndReturn(usage_obj)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(quota_data)

        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:project:overview:index') +
                              "?format=csv")
        self.assertTemplateUsed(res, 'project/overview/usage.csv')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))

    def test_usage_exception_usage(self):
        now = timezone.now()
        quota_data = self.quota_usages.first()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(quotas, 'tenant_quota_usages')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           timestamp,
                           Func(usage.almost_now)) \
                           .AndRaise(self.exceptions.nova)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

    def test_usage_exception_quota(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(quotas, 'tenant_quota_usages')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           timestamp,
                           Func(usage.almost_now)) \
                           .AndReturn(usage_obj)
        quotas.tenant_quota_usages(IsA(http.HttpRequest))\
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].quotas, {})

    def test_usage_default_tenant(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        quota_data = self.quota_usages.first()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(quotas, 'tenant_quota_usages')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           timestamp,
                           Func(usage.almost_now)) \
                           .AndReturn(usage_obj)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
