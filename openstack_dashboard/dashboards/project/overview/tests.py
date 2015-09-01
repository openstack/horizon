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
import logging

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME  # noqa
from django.core.urlresolvers import reverse
from django import http
from django.utils import timezone

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard import usage


INDEX_URL = reverse('horizon:project:overview:index')


class UsageViewTests(test.TestCase):

    @test.create_stubs({api.nova: ('usage_get',
                                   'tenant_absolute_limits',
                                   'extension_supported')})
    def _stub_nova_api_calls(self, nova_stu_enabled=True,
                             tenant_limits_exception=False,
                             stu_exception=False):
        api.nova.extension_supported(
            'SimpleTenantUsage', IsA(http.HttpRequest)) \
            .AndReturn(nova_stu_enabled)
        api.nova.extension_supported(
            'SimpleTenantUsage', IsA(http.HttpRequest)) \
            .AndReturn(nova_stu_enabled)

        if tenant_limits_exception:
            api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
                .AndRaise(tenant_limits_exception)
        else:
            api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
                .AndReturn(self.limits['absolute'])

        if nova_stu_enabled:
            self._nova_stu_enabled(stu_exception)

    @test.create_stubs({api.cinder: ('tenant_absolute_limits',)})
    def _stub_cinder_api_calls(self):
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndReturn(self.cinder_limits['absolute'])

    @test.create_stubs({api.neutron: ('is_extension_supported',),
                        api.network: ('floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list')})
    def _stub_neutron_api_calls(self, neutron_sg_enabled=True):
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'security-group').AndReturn(neutron_sg_enabled)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        if neutron_sg_enabled:
            api.network.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.q_secgroups.list())

    def _nova_stu_enabled(self, exception=False):
        now = timezone.now()
        start = datetime.datetime(now.year, now.month, 1, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)

        if exception:
            api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                               start, end) \
                .AndRaise(exception)
        else:
            api.nova.usage_get(IsA(http.HttpRequest), self.tenant.id,
                               start, end) \
                .AndReturn(api.nova.NovaUsage(self.usages.first()))

    def _common_assertions(self, nova_stu_enabled,
                           maxTotalFloatingIps=float("inf")):
        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(usages, usage.ProjectUsage))
        self.assertEqual(nova_stu_enabled,
                         res.context['simple_tenant_usage_enabled'])
        if nova_stu_enabled:
            self.assertContains(res, 'form-inline')
        else:
            self.assertNotContains(res, 'form-inline')
        self.assertEqual(usages.limits['maxTotalFloatingIps'],
                         maxTotalFloatingIps)

    def test_usage(self):
        self._test_usage(nova_stu_enabled=True)

    def test_usage_disabled(self):
        self._test_usage(nova_stu_enabled=False)

    def _test_usage(self, nova_stu_enabled):
        self._stub_nova_api_calls(nova_stu_enabled)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()
        self.mox.ReplayAll()

        self._common_assertions(nova_stu_enabled)

    def test_usage_nova_network(self):
        self._test_usage_nova_network(nova_stu_enabled=True)

    def test_usage_nova_network_disabled(self):
        self._test_usage_nova_network(nova_stu_enabled=False)

    @test.create_stubs({api.base: ('is_service_enabled',)})
    def _test_usage_nova_network(self, nova_stu_enabled):
        self._stub_nova_api_calls(nova_stu_enabled)

        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(False)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
            .MultipleTimes().AndReturn(False)

        self.mox.ReplayAll()

        self._common_assertions(nova_stu_enabled, maxTotalFloatingIps=10)

    @test.create_stubs({api.nova: ('usage_get',
                                   'extension_supported')})
    def _stub_nova_api_calls_unauthorized(self, exception):
        api.nova.extension_supported(
            'SimpleTenantUsage', IsA(http.HttpRequest)) \
            .AndReturn(True)
        self._nova_stu_enabled(exception)

    def test_unauthorized(self):
        self._stub_nova_api_calls_unauthorized(
            self.exceptions.nova_unauthorized)
        self.mox.ReplayAll()

        url = reverse('horizon:project:overview:index')

        # Avoid the log message in the test
        # when unauthorized exception will be logged
        logging.disable(logging.ERROR)
        res = self.client.get(url)
        logging.disable(logging.NOTSET)

        self.assertEqual(302, res.status_code)
        self.assertEqual(('Location', settings.TESTSERVER +
                          settings.LOGIN_URL + '?' +
                          REDIRECT_FIELD_NAME + '=' + url),
                         res._headers.get('location', None),)

    def test_usage_csv(self):
        self._test_usage_csv(nova_stu_enabled=True)

    def test_usage_csv_disabled(self):
        self._test_usage_csv(nova_stu_enabled=False)

    def _test_usage_csv(self, nova_stu_enabled=True):
        self._stub_nova_api_calls(nova_stu_enabled)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()
        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:project:overview:index') +
                              "?format=csv")
        self.assertTemplateUsed(res, 'project/overview/usage.csv')
        self.assertTrue(isinstance(res.context['usage'], usage.ProjectUsage))

    def test_usage_exception_usage(self):
        self._stub_nova_api_calls(stu_exception=self.exceptions.nova)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

    def test_usage_exception_quota(self):
        self._stub_nova_api_calls(tenant_limits_exception=self.exceptions.nova)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].quotas, {})

    def test_usage_default_tenant(self):
        self._stub_nova_api_calls()
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.ProjectUsage))

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron(self):
        self._test_usage_with_neutron(neutron_sg_enabled=True)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_nova_security_group(self):
        self._test_usage_with_neutron(neutron_sg_enabled=False)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_floating_ip_disabled(self):
        self._test_usage_with_neutron(neutron_fip_enabled=False)

    @test.create_stubs({api.neutron: ('tenant_quota_get',
                                      'is_extension_supported'),
                        api.network: ('floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list')})
    def _test_usage_with_neutron_prepare(self):
        self._stub_nova_api_calls()
        self._stub_cinder_api_calls()

    def _test_usage_with_neutron(self, neutron_sg_enabled=True,
                                 neutron_fip_enabled=True):
        self._test_usage_with_neutron_prepare()
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'quotas').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'security-group').AndReturn(neutron_sg_enabled)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(neutron_fip_enabled)
        if neutron_fip_enabled:
            api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        if neutron_sg_enabled:
            api.network.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.q_secgroups.list())
        api.neutron.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.neutron_quotas.first())
        self.mox.ReplayAll()

        self._test_usage_with_neutron_check(neutron_sg_enabled,
                                            neutron_fip_enabled)

    def _test_usage_with_neutron_check(self, neutron_sg_enabled=True,
                                       neutron_fip_expected=True,
                                       max_fip_expected=50,
                                       max_sg_expected=20):
        res = self.client.get(reverse('horizon:project:overview:index'))
        if neutron_fip_expected:
            self.assertContains(res, 'Floating IPs')
        self.assertContains(res, 'Security Groups')

        res_limits = res.context['usage'].limits
        # Make sure the floating IPs comes from Neutron (50 vs. 10)
        max_floating_ips = res_limits['maxTotalFloatingIps']
        self.assertEqual(max_floating_ips, max_fip_expected)
        if neutron_sg_enabled:
            # Make sure the security group limit comes from Neutron (20 vs. 10)
            max_security_groups = res_limits['maxSecurityGroups']
            self.assertEqual(max_security_groups, max_sg_expected)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_quotas_ext_error(self):
        self._test_usage_with_neutron_prepare()
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'quotas').AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()
        self._test_usage_with_neutron_check(neutron_fip_expected=False,
                                            max_fip_expected=float("inf"),
                                            max_sg_expected=float("inf"))

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_sg_ext_error(self):
        self._test_usage_with_neutron_prepare()
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'quotas').AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'security-group').AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()
        self._test_usage_with_neutron_check(neutron_fip_expected=False,
                                            max_fip_expected=float("inf"),
                                            max_sg_expected=float("inf"))

    def test_usage_with_cinder(self):
        self._test_usage_cinder(cinder_enabled=True)

    def test_usage_without_cinder(self):
        self._test_usage_cinder(cinder_enabled=False)

    @test.create_stubs({api.base: ('is_service_enabled',)})
    def _test_usage_cinder(self, cinder_enabled):
        self._stub_nova_api_calls(True)

        if cinder_enabled:
            self._stub_cinder_api_calls()

        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(False)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
            .MultipleTimes().AndReturn(cinder_enabled)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertTrue(isinstance(usages, usage.ProjectUsage))
        if cinder_enabled:
            self.assertEqual(usages.limits['totalVolumesUsed'], 1)
            self.assertEqual(usages.limits['maxTotalVolumes'], 10)
            self.assertEqual(usages.limits['totalGigabytesUsed'], 5)
            self.assertEqual(usages.limits['maxTotalVolumeGigabytes'], 1000)
        else:
            self.assertNotIn('totalVolumesUsed', usages.limits)

    def _test_usage_charts(self):
        self._stub_nova_api_calls(False)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()
        self.mox.ReplayAll()

        return self.client.get(reverse('horizon:project:overview:index'))

    def test_usage_charts_created(self):
        res = self._test_usage_charts()
        self.assertTrue('charts' in res.context)

    def test_usage_charts_infinite_quota(self):
        res = self._test_usage_charts()

        max_floating_ips = res.context['usage'].limits['maxTotalFloatingIps']
        self.assertEqual(max_floating_ips, float("inf"))

        self.assertContains(res, '(No Limit)')
