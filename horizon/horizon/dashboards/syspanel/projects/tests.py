# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import http
from django.core.urlresolvers import reverse
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:syspanel:projects:index')


class TenantsViewTests(test.BaseAdminViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(api, 'tenant_list')
        api.tenant_list(IsA(http.HttpRequest)).AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'syspanel/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants.list())

    def test_modify_quota(self):
        tenant = self.tenants.first()
        quota = self.quotas.first()
        quota_data = {"metadata_items": '1',
                      "injected_files": '1',
                      "injected_file_content_bytes": '1',
                      "cores": '1',
                      "instances": '1',
                      "volumes": '1',
                      "gigabytes": '1',
                      "ram": 1,
                      "floating_ips": '1'}
        self.mox.StubOutWithMock(api.keystone, 'tenant_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_update')
        api.keystone.tenant_get(IgnoreArg(), tenant.id).AndReturn(tenant)
        api.nova.tenant_quota_get(IgnoreArg(), tenant.id).AndReturn(quota)
        api.nova.tenant_quota_update(IgnoreArg(), tenant.id, **quota_data)
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:projects:quotas',
                      args=[self.tenant.id])
        quota_data.update({"method": "UpdateQuotas",
                           "tenant_id": self.tenant.id})
        res = self.client.post(url, quota_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)
