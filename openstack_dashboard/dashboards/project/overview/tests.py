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

from django.core.urlresolvers import reverse  # noqa
from django import http
from django.test.utils import override_settings  # noqa
from django.utils import timezone

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard import usage


INDEX_URL = reverse('horizon:project:overview:index')


class UsageViewTests(test.TestCase):
    def test_usage(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                           datetime.datetime(now.year,
                                             now.month,
                                             now.day, 0, 0, 0, 0),
                           datetime.datetime(now.year,
                                             now.month,
                                             now.day, 23, 59, 59, 0)) \
                           .AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
                           .AndReturn(self.limits['absolute'])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(usages, usage.ProjectUsage))
        self.assertContains(res, 'form-horizontal')
        self.assertEqual(usages.limits['maxTotalFloatingIps'], float("inf"))

    def test_usage_nova_network(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                           datetime.datetime(now.year,
                                             now.month,
                                             now.day, 0, 0, 0, 0),
                           datetime.datetime(now.year,
                                             now.month,
                                             now.day, 23, 59, 59, 0)) \
                           .AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
                           .AndReturn(self.limits['absolute'])
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
                           .AndReturn(False)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(usages, usage.ProjectUsage))
        self.assertContains(res, 'form-horizontal')
        self.assertEqual(usages.limits['maxTotalFloatingIps'], 10)

    def test_unauthorized(self):
        exc = self.exceptions.nova_unauthorized
        now = timezone.now()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                           datetime.datetime(now.year,
                                             now.month,
                                             now.day, 0, 0, 0, 0),
                           datetime.datetime(now.year,
                                             now.month,
                                             now.day, 23, 59, 59, 0)) \
                           .AndRaise(exc)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
                           .AndReturn(self.limits['absolute'])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        url = reverse('horizon:project:overview:index')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertMessageCount(res, error=1)
        self.assertContains(res, 'Unauthorized:')

    def test_usage_csv(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           start, end).AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:project:overview:index') +
                              "?format=csv")
        self.assertTemplateUsed(res, 'project/overview/usage.csv')
        self.assertTrue(isinstance(res.context['usage'], usage.ProjectUsage))

    def test_usage_exception_usage(self):
        now = timezone.now()
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           start, end).AndRaise(self.exceptions.nova)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

    def test_usage_exception_quota(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           start, end).AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
                           .AndRaise(self.exceptions.nova)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].quotas, {})

    def test_usage_default_tenant(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           start, end).AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.ProjectUsage))

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_floating_ips(self):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mox.StubOutWithMock(api.nova, 'usage_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.neutron, 'is_extension_supported')
        self.mox.StubOutWithMock(api.neutron, 'tenant_quota_get')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        api.nova.usage_get(IsA(http.HttpRequest),
                           self.tenant.id,
                           start, end).AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
                           .AndReturn(True)
        api.neutron.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
                           .AndReturn(self.neutron_quotas.first())
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                           .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertContains(res, 'Floating IPs')

        # Make sure the floating IPs limit comes from Neutron (50 vs. 10)
        max_floating_ips = res.context['usage'].limits['maxTotalFloatingIps']
        self.assertEqual(max_floating_ips, 50)
