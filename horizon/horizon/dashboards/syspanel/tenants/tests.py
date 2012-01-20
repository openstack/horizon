# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import http
from django.core.urlresolvers import reverse
from mox import IgnoreArg, IsA
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:syspanel:tenants:index')


class FakeQuotaSet(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TenantsViewTests(test.BaseAdminViewTests):
    def setUp(self):
        super(TenantsViewTests, self).setUp()

        self.tenant = api.keystone.Tenant(None)
        self.tenant.id = self.TEST_TENANT
        self.tenant.name = self.TEST_TENANT_NAME
        self.tenant.enabled = True

        self.quota_data = dict(metadata_items='1',
                               injected_file_content_bytes='1',
                               volumes='1',
                               gigabytes='1',
                               ram=1,
                               floating_ips='1',
                               instances='1',
                               injected_files='1',
                               cores='1')
        self.quota = FakeQuotaSet(id=self.TEST_TENANT, **self.quota_data)

        self.tenants = [self.tenant]

    def test_index(self):
        self.mox.StubOutWithMock(api, 'tenant_list')
        api.tenant_list(IsA(http.HttpRequest)).AndReturn(self.tenants)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'syspanel/tenants/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants)

    def test_modify_quota(self):
        self.mox.StubOutWithMock(api.keystone, 'tenant_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_update')

        api.keystone.tenant_get(IgnoreArg(), self.TEST_TENANT) \
                    .AndReturn(self.tenant)
        api.nova.tenant_quota_get(IgnoreArg(), self.TEST_TENANT) \
                    .AndReturn(self.quota)
        api.nova.tenant_quota_update(IgnoreArg(),
                                         self.TEST_TENANT,
                                         **self.quota_data)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:tenants:quotas',
                      args=(self.TEST_TENANT,))
        data = {"method": "UpdateQuotas",
                "tenant_id": self.TEST_TENANT,
                "metadata_items": '1',
                "injected_files": '1',
                "injected_file_content_bytes": '1',
                "cores": '1',
                "instances": '1',
                "volumes": '1',
                "gigabytes": '1',
                "ram": 1,
                "floating_ips": '1'}
        res = self.client.post(url, data)
        self.assertRedirectsNoFollow(res, INDEX_URL)
