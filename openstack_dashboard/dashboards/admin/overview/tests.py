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

from django.core.urlresolvers import reverse
from django import http
from django.utils import encoding
from django.utils import timezone

from mox import IsA  # noqa

from horizon.templatetags import sizeformat

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard import usage


INDEX_URL = reverse('horizon:project:overview:index')


class UsageViewTests(test.BaseAdminViewTests):

    def _stub_api_calls(self, nova_stu_enabled):
        self.mox.StubOutWithMock(api.nova, 'usage_list')
        self.mox.StubOutWithMock(api.nova, 'tenant_absolute_limits')
        self.mox.StubOutWithMock(api.nova, 'extension_supported')
        self.mox.StubOutWithMock(api.keystone, 'tenant_list')
        self.mox.StubOutWithMock(api.neutron, 'is_extension_supported')
        self.mox.StubOutWithMock(api.network, 'floating_ip_supported')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'security_group_list')
        self.mox.StubOutWithMock(api.cinder, 'tenant_absolute_limits')

        api.nova.extension_supported(
            'SimpleTenantUsage', IsA(http.HttpRequest)) \
            .AndReturn(nova_stu_enabled)

    def test_usage(self):
        self._test_usage(nova_stu_enabled=True)

    def test_usage_disabled(self):
        self._test_usage(nova_stu_enabled=False)

    def test_usage_with_deleted_tenant(self):
        self._test_usage(tenant_deleted=True)

    def _test_usage(self, nova_stu_enabled=True, tenant_deleted=False):
        self._stub_api_calls(nova_stu_enabled)
        api.nova.extension_supported(
            'SimpleTenantUsage', IsA(http.HttpRequest)) \
            .AndReturn(nova_stu_enabled)
        now = timezone.now()
        usage_list = [api.nova.NovaUsage(u) for u in self.usages.list()]
        if tenant_deleted:
            api.keystone.tenant_list(IsA(http.HttpRequest)) \
                .AndReturn([[self.tenants.first()], False])
        else:
            api.keystone.tenant_list(IsA(http.HttpRequest)) \
                .AndReturn([self.tenants.list(), False])

        if nova_stu_enabled:
            api.nova.usage_list(IsA(http.HttpRequest),
                                datetime.datetime(now.year,
                                                  now.month,
                                                  1, 0, 0, 0, 0),
                                datetime.datetime(now.year,
                                                  now.month,
                                                  now.day, 23, 59, 59, 0)) \
                .AndReturn(usage_list)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndReturn(self.limits['absolute'])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'security-group').AndReturn(True)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.q_secgroups.list())
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndReturn(self.cinder_limits['absolute'])

        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:admin:overview:index'))
        self.assertTemplateUsed(res, 'admin/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.GlobalUsage))
        self.assertEqual(nova_stu_enabled,
                         res.context['simple_tenant_usage_enabled'])

        usage_table = encoding.smart_str(u'''
            <tr class="" data-object-id="1" id="global_usage__row__1">
              <td class="sortable normal_column">test_tenant</td>
              <td class="sortable normal_column">%s</td>
              <td class="sortable normal_column">%s</td>
              <td class="sortable normal_column">%s</td>
              <td class="sortable normal_column">%.2f</td>
              <td class="sortable normal_column">%.2f</td>
              <td class="sortable normal_column">%.2f</td>
            </tr>
            ''' % (usage_list[0].vcpus,
                   sizeformat.diskgbformat(usage_list[0].local_gb),
                   sizeformat.mb_float_format(usage_list[0].memory_mb),
                   usage_list[0].vcpu_hours,
                   usage_list[0].disk_gb_hours,
                   usage_list[0].memory_mb_hours)
        )

        # test for deleted project
        usage_table_deleted = encoding.smart_str(u'''
            <tr class="" data-object-id="3" id="global_usage__row__3">
              <td class="sortable normal_column">3 (Deleted)</td>
              <td class="sortable normal_column">%s</td>
              <td class="sortable normal_column">%s</td>
              <td class="sortable normal_column">%s</td>
              <td class="sortable normal_column">%.2f</td>
              <td class="sortable normal_column">%.2f</td>
              <td class="sortable normal_column">%.2f</td>
            </tr>
            ''' % (usage_list[1].vcpus,
                   sizeformat.diskgbformat(usage_list[1].local_gb),
                   sizeformat.mb_float_format(usage_list[1].memory_mb),
                   usage_list[1].vcpu_hours,
                   usage_list[1].disk_gb_hours,
                   usage_list[1].memory_mb_hours)
        )

        if nova_stu_enabled:
            self.assertContains(res, usage_table, html=True)
            if tenant_deleted:
                self.assertContains(res, usage_table_deleted, html=True)
            else:
                self.assertNotContains(res, usage_table_deleted, html=True)
        else:
            self.assertNotContains(res, usage_table, html=True)

    def test_usage_csv(self):
        self._test_usage_csv(nova_stu_enabled=True)

    def test_usage_csv_disabled(self):
        self._test_usage_csv(nova_stu_enabled=False)

    def _test_usage_csv(self, nova_stu_enabled=True):
        self._stub_api_calls(nova_stu_enabled)
        api.nova.extension_supported(
            'SimpleTenantUsage', IsA(http.HttpRequest)) \
            .AndReturn(nova_stu_enabled)
        now = timezone.now()
        usage_obj = [api.nova.NovaUsage(u) for u in self.usages.list()]
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
                    .AndReturn([self.tenants.list(), False])
        if nova_stu_enabled:
            api.nova.usage_list(IsA(http.HttpRequest),
                                datetime.datetime(now.year,
                                                  now.month,
                                                  1, 0, 0, 0, 0),
                                datetime.datetime(now.year,
                                                  now.month,
                                                  now.day, 23, 59, 59, 0)) \
                .AndReturn(usage_obj)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'security-group').AndReturn(True)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.q_secgroups.list())
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndReturn(self.cinder_limits['absolute'])
        self.mox.ReplayAll()

        csv_url = reverse('horizon:admin:overview:index') + "?format=csv"
        res = self.client.get(csv_url)
        self.assertTemplateUsed(res, 'admin/overview/usage.csv')
        self.assertTrue(isinstance(res.context['usage'], usage.GlobalUsage))
        hdr = 'Project Name,VCPUs,RAM (MB),Disk (GB),Usage (Hours)'
        self.assertContains(res, '%s\r\n' % hdr)

        if nova_stu_enabled:
            for obj in usage_obj:
                row = u'{0},{1},{2},{3},{4:.2f}\r\n'.format(obj.project_name,
                                                            obj.vcpus,
                                                            obj.memory_mb,
                                                            obj.disk_gb_hours,
                                                            obj.vcpu_hours)
                self.assertContains(res, row)
