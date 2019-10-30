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

from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard import usage


INDEX_URL = reverse('horizon:project:overview:index')


class UsageViewTests(test.TestCase):

    @test.create_mocks({
        api.nova: ('usage_get', 'extension_supported',),
        api.neutron: ('is_quotas_extension_supported',)
    })
    def _stub_api_calls(self, nova_stu_enabled=True,
                        stu_exception=False, overview_days_range=1,
                        quota_usage_overrides=None,
                        quota_extension_support=True):
        self.mock_is_quotas_extension_supported.return_value = \
            quota_extension_support
        self.mock_extension_supported.side_effect = [nova_stu_enabled,
                                                     nova_stu_enabled]
        if nova_stu_enabled:
            self._nova_stu_enabled(stu_exception,
                                   overview_days_range=overview_days_range)

        self._stub_tenant_quota_usages(overrides=quota_usage_overrides)

    def _check_api_calls(self, nova_stu_enabled=True,
                         stu_exception=False, overview_days_range=1):
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_extension_supported, 2,
            mock.call('SimpleTenantUsage', test.IsHttpRequest()))
        if nova_stu_enabled:
            self._check_stu_enabled(stu_exception,
                                    overview_days_range=overview_days_range)
        else:
            self.mock_usage_get.assert_not_called()
        self._check_tenant_quota_usages()

    @staticmethod
    def _add_quota_usages(usages, quota_usages, excludes=None):
        excludes = excludes or []
        for k in quota_usages.usages:
            if k in excludes:
                continue
            quota = quota_usages[k]['quota']
            if quota == float('inf'):
                quota = -1
            usages.add_quota(api.base.Quota(k, quota))
            usages.tally(k, quota_usages[k]['used'])

    @test.create_mocks({usage.quotas: ('tenant_quota_usages',)})
    def _stub_tenant_quota_usages(self, overrides):
        usages_data = usage.quotas.QuotaUsage()
        self._add_quota_usages(usages_data, self.quota_usages.first(),
                               # At now, nova quota_usages contains
                               # volumes and gigabytes.
                               excludes=('volumes', 'gigabytes'))
        self._add_quota_usages(
            usages_data, self.neutron_quota_usages.first())
        self._add_quota_usages(usages_data, self.cinder_quota_usages.first())
        if overrides:
            for key, value in overrides.items():
                if 'quota' in value:
                    usages_data.add_quota(api.base.Quota(key, value['quota']))
                if 'used' in value:
                    usages_data.tally(key, value['used'])
        self.mock_tenant_quota_usages.return_value = usages_data

    def _check_tenant_quota_usages(self):
        self.mock_tenant_quota_usages.assert_called_once_with(
            test.IsHttpRequest())

    def _nova_stu_enabled(self, exception=False, overview_days_range=1):
        if exception:
            self.mock_usage_get.side_effect = exception
        else:
            usage = api.nova.NovaUsage(self.usages.first())
            self.mock_usage_get.return_value = usage

    def _check_stu_enabled(self, exception=False, overview_days_range=1):
        now = timezone.now()
        if overview_days_range:
            start_day = now - datetime.timedelta(days=overview_days_range)
        else:
            start_day = datetime.date(now.year, now.month, 1)
        start = datetime.datetime(start_day.year, start_day.month,
                                  start_day.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)

        self.mock_usage_get.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id, start, end)

    def _common_assertions(self, nova_stu_enabled,
                           maxTotalFloatingIps=50):
        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertIsInstance(usages, usage.ProjectUsage)
        self.assertEqual(nova_stu_enabled,
                         res.context['simple_tenant_usage_enabled'])
        if nova_stu_enabled:
            self.assertContains(res, 'form-inline')
        else:
            self.assertNotContains(res, 'form-inline')
        self.assertEqual(usages.limits['floatingip']['quota'],
                         maxTotalFloatingIps)

    @override_settings(OVERVIEW_DAYS_RANGE=None)
    def test_usage(self):
        self._test_usage(nova_stu_enabled=True, overview_days_range=None)

    def test_usage_1_day(self):
        self._test_usage(nova_stu_enabled=True)

    @override_settings(OVERVIEW_DAYS_RANGE=None)
    def test_usage_disabled(self):
        self._test_usage(nova_stu_enabled=False, overview_days_range=None)

    def _test_usage(self, nova_stu_enabled, overview_days_range=1):
        self._stub_api_calls(nova_stu_enabled,
                             overview_days_range=overview_days_range)

        self._common_assertions(nova_stu_enabled)

        self._check_api_calls(nova_stu_enabled,
                              overview_days_range=overview_days_range)

    def test_unauthorized(self):
        url = reverse('horizon:admin:volumes:index')

        # Avoid the log message in the test
        # when unauthorized exception will be logged
        logging.disable(logging.ERROR)
        res = self.client.get(url)
        logging.disable(logging.NOTSET)

        self.assertEqual(403, res.status_code)

    def test_usage_csv(self):
        self._test_usage_csv(nova_stu_enabled=True)

    @override_settings(OVERVIEW_DAYS_RANGE=1)
    def test_usage_csv_1_day(self):
        self._test_usage_csv(nova_stu_enabled=True, overview_days_range=1)

    def test_usage_csv_disabled(self):
        self._test_usage_csv(nova_stu_enabled=False)

    def _test_usage_csv(self, nova_stu_enabled=True, overview_days_range=1):
        self._stub_api_calls(nova_stu_enabled,
                             overview_days_range=overview_days_range)

        res = self.client.get(reverse('horizon:project:overview:index') +
                              "?format=csv")
        self.assertTemplateUsed(res, 'project/overview/usage.csv')
        self.assertIsInstance(res.context['usage'], usage.ProjectUsage)
        self._check_api_calls(nova_stu_enabled,
                              overview_days_range=overview_days_range)

    def test_usage_exception_usage(self):
        self._stub_api_calls(stu_exception=self.exceptions.nova)

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

        self._check_api_calls(stu_exception=self.exceptions.nova)

    def test_usage_default_tenant(self):
        self._stub_api_calls()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertIsInstance(res.context['usage'], usage.ProjectUsage)

        self._check_api_calls()

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron(self):
        self._test_usage_with_neutron(neutron_sg_enabled=True)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_nova_security_group(self):
        self._test_usage_with_neutron(neutron_sg_enabled=False)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_floating_ip_disabled(self):
        self._test_usage_with_neutron(neutron_fip_enabled=False)

    def _test_usage_with_neutron(self,
                                 neutron_sg_enabled=True,
                                 neutron_fip_enabled=True):
        self._stub_api_calls()
        self._test_usage_with_neutron_check(neutron_sg_enabled,
                                            neutron_fip_enabled)
        self._check_api_calls()

    def _test_usage_with_neutron_check(self, neutron_sg_enabled=True,
                                       neutron_fip_expected=True,
                                       max_fip_expected=50,
                                       max_sg_expected=20):
        res = self.client.get(reverse('horizon:project:overview:index'))
        if neutron_fip_expected:
            self.assertContains(res, 'Floating IPs')
        self.assertContains(res, 'Security Groups')

        res_limits = res.context['usage'].limits
        max_floating_ips = res_limits['floatingip']['quota']
        self.assertEqual(max_floating_ips, max_fip_expected)
        if neutron_sg_enabled:
            max_security_groups = res_limits['security_group']['quota']
            self.assertEqual(max_security_groups, max_sg_expected)

    def test_usage_cinder(self):
        self._stub_api_calls(
            quota_usage_overrides={'volumes': {'used': 4},
                                   'gigabytes': {'used': 400}}
        )

        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertIsInstance(usages, usage.ProjectUsage)

        self.assertEqual(usages.limits['volumes']['used'], 4)
        self.assertEqual(usages.limits['volumes']['quota'], 10)
        self.assertEqual(usages.limits['gigabytes']['used'], 400)
        self.assertEqual(usages.limits['gigabytes']['quota'], 1000)

        self._check_api_calls(nova_stu_enabled=True)

    def _test_usage_charts(self, quota_usage_overrides=None,
                           quota_extension_support=True):
        self._stub_api_calls(nova_stu_enabled=False,
                             quota_usage_overrides=quota_usage_overrides,
                             quota_extension_support=quota_extension_support)

        res = self.client.get(reverse('horizon:project:overview:index'))

        self._check_api_calls(nova_stu_enabled=False)

        return res

    def test_usage_charts_created(self):
        res = self._test_usage_charts(
            quota_usage_overrides={'floatingip': {'quota': -1, 'used': 1234}})
        self.assertIn('charts', res.context)
        charts = res.context['charts']

        self.assertEqual(['Compute', 'Volume', 'Network'],
                         [c['title'] for c in charts])

        compute_charts = [c for c in charts if c['title'] == 'Compute'][0]
        chart_ram = [c for c in compute_charts['charts']
                     if c['type'] == 'ram'][0]
        # Check mb_float_format filter is applied
        self.assertEqual(10000, chart_ram['quota'])
        self.assertEqual('9.8GB', chart_ram['quota_display'])
        self.assertEqual(0, chart_ram['used'])
        self.assertEqual('0Bytes', chart_ram['used_display'])

        volume_charts = [c for c in charts if c['title'] == 'Volume'][0]
        chart_gigabytes = [c for c in volume_charts['charts']
                           if c['type'] == 'gigabytes'][0]
        # Check diskgbformat filter is applied
        self.assertEqual(1000, chart_gigabytes['quota'])
        self.assertEqual('1000GB', chart_gigabytes['quota_display'])
        self.assertEqual(0, chart_gigabytes['used'])
        self.assertEqual('0Bytes', chart_gigabytes['used_display'])

        network_charts = [c for c in charts if c['title'] == 'Network'][0]
        chart_fip = [c for c in network_charts['charts']
                     if c['type'] == 'floatingip'][0]
        # Check intcomma default filter is applied
        self.assertEqual(float('inf'), chart_fip['quota'])
        self.assertEqual(float('inf'), chart_fip['quota_display'])
        self.assertEqual(1234, chart_fip['used'])
        self.assertEqual('1,234', chart_fip['used_display'])

    def test_disallowed_network_chart(self):
        res = self._test_usage_charts(
            quota_usage_overrides={'floatingip': {'quota': -1, 'used': 1234}},
            quota_extension_support=False)
        charts = res.context['charts']
        self.assertEqual(['Compute', 'Volume'],
                         [c['title'] for c in charts])

    def test_usage_charts_infinite_quota(self):
        res = self._test_usage_charts(
            quota_usage_overrides={'floatingip': {'quota': -1}})

        max_floating_ips = res.context['usage'].limits['floatingip']['quota']
        self.assertEqual(max_floating_ips, float("inf"))

        self.assertContains(res, '(No Limit)')
