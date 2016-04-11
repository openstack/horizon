# Copyright 2013 Kylin, Inc.
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

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

INDEX_URL = reverse('horizon:admin:defaults:index')


class ServicesViewTests(test.BaseAdminViewTests):
    def test_index(self):
        self._test_index(neutron_enabled=True)

    def test_index_with_neutron_disabled(self):
        self._test_index(neutron_enabled=False)

    def test_index_with_neutron_sg_disabled(self):
        self._test_index(neutron_enabled=True,
                         neutron_sg_enabled=False)

    def _test_index(self, neutron_enabled=True, neutron_sg_enabled=True):
        # Neutron does not have an API for getting default system
        # quotas. When not using Neutron, the floating ips quotas
        # should be in the list.
        self.mox.StubOutWithMock(api.nova, 'default_quota_get')
        self.mox.StubOutWithMock(api.cinder, 'default_quota_get')
        self.mox.StubOutWithMock(api.cinder, 'is_volume_service_enabled')
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        if neutron_enabled:
            self.mox.StubOutWithMock(api.neutron, 'is_extension_supported')

        api.cinder.is_volume_service_enabled(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(neutron_enabled)

        api.nova.default_quota_get(IsA(http.HttpRequest),
                                   self.tenant.id).AndReturn(self.quotas.nova)
        api.cinder.default_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.cinder_quotas.first())
        if neutron_enabled:
            api.neutron.is_extension_supported(
                IsA(http.HttpRequest),
                'security-group').AndReturn(neutron_sg_enabled)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'admin/defaults/index.html')

        quotas_tab = res.context['tab_group'].get_tab('quotas')
        expected_tabs = ['<Quota: (injected_file_content_bytes, 1)>',
                         '<Quota: (metadata_items, 1)>',
                         '<Quota: (injected_files, 1)>',
                         '<Quota: (gigabytes, 1000)>',
                         '<Quota: (ram, 10000)>',
                         '<Quota: (instances, 10)>',
                         '<Quota: (snapshots, 1)>',
                         '<Quota: (volumes, 1)>',
                         '<Quota: (cores, 10)>',
                         '<Quota: (floating_ips, 1)>',
                         '<Quota: (fixed_ips, 10)>',
                         '<Quota: (security_groups, 10)>',
                         '<Quota: (security_group_rules, 20)>']
        if neutron_enabled:
            expected_tabs.remove('<Quota: (floating_ips, 1)>')
            expected_tabs.remove('<Quota: (fixed_ips, 10)>')
            if neutron_sg_enabled:
                expected_tabs.remove('<Quota: (security_groups, 10)>')
                expected_tabs.remove('<Quota: (security_group_rules, 20)>')

        self.assertQuerysetEqual(quotas_tab._tables['quotas'].data,
                                 expected_tabs,
                                 ordered=False)


class UpdateDefaultQuotasTests(test.BaseAdminViewTests):
    def _get_quota_info(self, quota):
        quota_data = {}
        for field in (quotas.QUOTA_FIELDS + quotas.MISSING_QUOTA_FIELDS):
            if field != 'fixed_ips':
                limit = quota.get(field).limit or 10
                quota_data[field] = int(limit)
        return quota_data

    @test.create_stubs({api.nova: ('default_quota_update', ),
                        api.cinder: ('default_quota_update', ),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas')})
    def test_update_default_quotas(self):
        quota = self.quotas.first()

        # init
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        # update some fields
        quota[0].limit = 123
        quota[1].limit = -1
        updated_quota = self._get_quota_info(quota)

        # handle
        nova_fields = quotas.NOVA_QUOTA_FIELDS + quotas.MISSING_QUOTA_FIELDS
        nova_updated_quota = dict([(key, updated_quota[key]) for key in
                                   nova_fields if key != 'fixed_ips'])
        api.nova.default_quota_update(IsA(http.HttpRequest),
                                      **nova_updated_quota)

        cinder_updated_quota = dict([(key, updated_quota[key]) for key in
                                    quotas.CINDER_QUOTA_FIELDS])
        api.cinder.default_quota_update(IsA(http.HttpRequest),
                                        **cinder_updated_quota)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:defaults:update_defaults')
        res = self.client.post(url, updated_quota)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
