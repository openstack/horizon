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

    @test.create_mocks({api.nova: (
        'usage_get',
        ('tenant_absolute_limits', 'nova_tenant_absolute_limits'),
        'extension_supported',
    )})
    def _stub_nova_api_calls(self,
                             nova_stu_enabled=True,
                             tenant_limits_exception=False,
                             stu_exception=False, overview_days_range=1):
        self.mock_extension_supported.side_effect = [nova_stu_enabled,
                                                     nova_stu_enabled]
        if tenant_limits_exception:
            self.mock_nova_tenant_absolute_limits.side_effect = \
                tenant_limits_exception
        else:
            self.mock_nova_tenant_absolute_limits.return_value = \
                self.limits['absolute']
        if nova_stu_enabled:
            self._nova_stu_enabled(stu_exception,
                                   overview_days_range=overview_days_range)

    def _check_nova_api_calls(self,
                              nova_stu_enabled=True,
                              tenant_limits_exception=False,
                              stu_exception=False, overview_days_range=1):
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_extension_supported, 2,
            mock.call('SimpleTenantUsage', test.IsHttpRequest()))
        self.mock_nova_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), reserved=True)
        if nova_stu_enabled:
            self._check_stu_enabled(stu_exception,
                                    overview_days_range=overview_days_range)
        else:
            self.mock_usage_get.assert_not_called()

    @test.create_mocks({api.cinder: (
        ('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
    )})
    def _stub_cinder_api_calls(self):
        self.mock_cinder_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

    def _check_cinder_api_calls(self):
        self.mock_cinder_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('security_group_list',
                                      'tenant_floating_ip_list',
                                      'floating_ip_supported',
                                      'is_extension_supported')})
    def _stub_neutron_api_calls(self, neutron_sg_enabled=True):
        self.mock_is_extension_supported.return_value = neutron_sg_enabled
        self.mock_floating_ip_supported.return_value = True
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        if neutron_sg_enabled:
            self.mock_security_group_list.return_value = \
                self.security_groups.list()

    def _check_neutron_api_calls(self, neutron_sg_enabled=True):
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'security-group')
        self.mock_floating_ip_supported.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        if neutron_sg_enabled:
            self.mock_security_group_list.assert_called_once_with(
                test.IsHttpRequest())
        else:
            self.mock_security_group_list.assert_not_called()

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
                           maxTotalFloatingIps=float("inf")):
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
        self.assertEqual(usages.limits['maxTotalFloatingIps'],
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
        self._stub_nova_api_calls(nova_stu_enabled,
                                  overview_days_range=overview_days_range)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()

        self._common_assertions(nova_stu_enabled)

        self._check_nova_api_calls(nova_stu_enabled,
                                   overview_days_range=overview_days_range)
        self._check_neutron_api_calls()
        self._check_cinder_api_calls()

    def test_usage_nova_network(self):
        self._test_usage_nova_network(nova_stu_enabled=True)

    def test_usage_nova_network_disabled(self):
        self._test_usage_nova_network(nova_stu_enabled=False)

    @test.create_mocks({api.base: ('is_service_enabled',),
                        api.cinder: ('is_volume_service_enabled',)})
    def _test_usage_nova_network(self, nova_stu_enabled):
        self._stub_nova_api_calls(nova_stu_enabled)
        self.mock_is_service_enabled.return_value = False
        self.mock_is_volume_service_enabled.return_value = False

        self._common_assertions(nova_stu_enabled, maxTotalFloatingIps=10)
        self._check_nova_api_calls(nova_stu_enabled)
        self.mock_is_service_enabled.assert_called_once_with(
            test.IsHttpRequest(), 'network')
        self.mock_is_volume_service_enabled.assert_called_once_with(
            test.IsHttpRequest())

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
        self._stub_nova_api_calls(nova_stu_enabled,
                                  overview_days_range=overview_days_range)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()

        res = self.client.get(reverse('horizon:project:overview:index') +
                              "?format=csv")
        self.assertTemplateUsed(res, 'project/overview/usage.csv')
        self.assertIsInstance(res.context['usage'], usage.ProjectUsage)
        self._check_nova_api_calls(nova_stu_enabled,
                                   overview_days_range=overview_days_range)
        self._check_neutron_api_calls()
        self._check_cinder_api_calls()

    def test_usage_exception_usage(self):
        self._stub_nova_api_calls(stu_exception=self.exceptions.nova)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

        self._check_nova_api_calls(stu_exception=self.exceptions.nova)
        self._check_neutron_api_calls()
        self._check_cinder_api_calls()

    def test_usage_exception_quota(self):
        self._stub_nova_api_calls(tenant_limits_exception=self.exceptions.nova)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertEqual(res.context['usage'].quotas, {})

        self._check_nova_api_calls(
            tenant_limits_exception=self.exceptions.nova)
        self._check_neutron_api_calls()
        self._check_cinder_api_calls()

    def test_usage_default_tenant(self):
        self._stub_nova_api_calls()
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()

        res = self.client.get(reverse('horizon:project:overview:index'))
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertIsInstance(res.context['usage'], usage.ProjectUsage)

        self._check_nova_api_calls()
        self._check_neutron_api_calls()
        self._check_cinder_api_calls()

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron(self):
        self._test_usage_with_neutron(neutron_sg_enabled=True)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_nova_security_group(self):
        self._test_usage_with_neutron(neutron_sg_enabled=False)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_usage_with_neutron_floating_ip_disabled(self):
        self._test_usage_with_neutron(neutron_fip_enabled=False)

    def _test_usage_with_neutron_prepare(self):
        self._stub_nova_api_calls()
        self._stub_cinder_api_calls()

    def _check_nova_cinder_calls_with_neutron_prepare(self):
        self._check_nova_api_calls()
        self._check_cinder_api_calls()

    @test.create_mocks({api.neutron: ('tenant_quota_get',
                                      'is_extension_supported',
                                      'floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list')})
    def _test_usage_with_neutron(self,
                                 neutron_sg_enabled=True,
                                 neutron_fip_enabled=True):
        self._test_usage_with_neutron_prepare()

        self.mock_is_extension_supported.side_effect = [True,
                                                        neutron_sg_enabled]
        self.mock_floating_ip_supported.return_value = neutron_fip_enabled
        if neutron_fip_enabled:
            self.mock_tenant_floating_ip_list.return_value = \
                self.floating_ips.list()
        if neutron_sg_enabled:
            self.mock_security_group_list.return_value = \
                self.security_groups.list()
        self.mock_tenant_quota_get.return_value = self.neutron_quotas.first()

        self._test_usage_with_neutron_check(neutron_sg_enabled,
                                            neutron_fip_enabled)

        self.mock_is_extension_supported.assert_has_calls([
            mock.call(test.IsHttpRequest(), 'quotas'),
            mock.call(test.IsHttpRequest(), 'security-group'),
        ])
        self.assertEqual(2, self.mock_is_extension_supported.call_count)
        self.mock_floating_ip_supported.assert_called_once_with(
            test.IsHttpRequest())
        if neutron_fip_enabled:
            self.mock_tenant_floating_ip_list.assert_called_once_with(
                test.IsHttpRequest())
        else:
            self.mock_tenant_floating_ip_list.assert_not_called()
        if neutron_sg_enabled:
            self.mock_security_group_list.assert_called_once_with(
                test.IsHttpRequest())
        else:
            self.mock_security_group_list.assert_not_called()
        self.mock_tenant_quota_get.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id)

        self._check_nova_cinder_calls_with_neutron_prepare()

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
    @mock.patch.object(api.neutron, 'is_extension_supported')
    def test_usage_with_neutron_quotas_ext_error(self,
                                                 mock_is_extension_supported):
        self._test_usage_with_neutron_prepare()
        mock_is_extension_supported.side_effect = self.exceptions.neutron

        self._test_usage_with_neutron_check(neutron_fip_expected=False,
                                            max_fip_expected=float("inf"),
                                            max_sg_expected=float("inf"))

        mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'quotas')
        self._check_nova_cinder_calls_with_neutron_prepare()

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    @mock.patch.object(api.neutron, 'is_extension_supported')
    def test_usage_with_neutron_sg_ext_error(self,
                                             mock_is_extension_supported):
        self._test_usage_with_neutron_prepare()
        mock_is_extension_supported.side_effect = [
            True,  # quotas
            self.exceptions.neutron,  # security-group
        ]

        self._test_usage_with_neutron_check(neutron_fip_expected=False,
                                            max_fip_expected=float("inf"),
                                            max_sg_expected=float("inf"))

        self.assertEqual(2, mock_is_extension_supported.call_count)
        mock_is_extension_supported.assert_has_calls([
            mock.call(test.IsHttpRequest(), 'quotas'),
            mock.call(test.IsHttpRequest(), 'security-group'),
        ])
        self._check_nova_cinder_calls_with_neutron_prepare()

    def test_usage_with_cinder(self):
        self._test_usage_cinder(cinder_enabled=True)

    def test_usage_without_cinder(self):
        self._test_usage_cinder(cinder_enabled=False)

    @test.create_mocks({api.base: ('is_service_enabled',),
                        api.cinder: ('is_volume_service_enabled',)})
    def _test_usage_cinder(self, cinder_enabled):
        self._stub_nova_api_calls(nova_stu_enabled=True)

        if cinder_enabled:
            self._stub_cinder_api_calls()

        self.mock_is_service_enabled.return_value = False
        self.mock_is_volume_service_enabled.return_value = cinder_enabled

        res = self.client.get(reverse('horizon:project:overview:index'))
        usages = res.context['usage']
        self.assertTemplateUsed(res, 'project/overview/usage.html')
        self.assertIsInstance(usages, usage.ProjectUsage)
        if cinder_enabled:
            self.assertEqual(usages.limits['totalVolumesUsed'], 4)
            self.assertEqual(usages.limits['maxTotalVolumes'], 20)
            self.assertEqual(usages.limits['totalGigabytesUsed'], 400)
            self.assertEqual(usages.limits['maxTotalVolumeGigabytes'], 1000)
        else:
            self.assertNotIn('totalVolumesUsed', usages.limits)

        self._check_nova_api_calls(nova_stu_enabled=True)
        if cinder_enabled:
            self._check_cinder_api_calls()

        self.mock_is_service_enabled.assert_called_once_with(
            test.IsHttpRequest(), 'network')
        self.mock_is_volume_service_enabled.assert_called_once_with(
            test.IsHttpRequest())

    def _test_usage_charts(self):
        self._stub_nova_api_calls(nova_stu_enabled=False)
        self._stub_neutron_api_calls()
        self._stub_cinder_api_calls()

        res = self.client.get(reverse('horizon:project:overview:index'))

        self._check_nova_api_calls(nova_stu_enabled=False)
        self._check_neutron_api_calls()
        self._check_cinder_api_calls()

        return res

    def test_usage_charts_created(self):
        res = self._test_usage_charts()
        self.assertIn('charts', res.context)

    def test_usage_charts_infinite_quota(self):
        res = self._test_usage_charts()

        max_floating_ips = res.context['usage'].limits['maxTotalFloatingIps']
        self.assertEqual(max_floating_ips, float("inf"))

        self.assertContains(res, '(No Limit)')
