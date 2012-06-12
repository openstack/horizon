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
        self.mox.StubOutWithMock(api.keystone, 'tenant_list')
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True) \
                    .AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'syspanel/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants.list())

    def test_modify_quota(self):
        tenant = self.tenants.first()
        quota = self.quotas.first()
        quota_data = {"metadata_items": 1,
                      "injected_files": 1,
                      "injected_file_content_bytes": 1,
                      "cores": 1,
                      "instances": 1,
                      "volumes": 1,
                      "gigabytes": 1,
                      "ram": 1,
                      "floating_ips": 1}
        self.mox.StubOutWithMock(api.keystone, 'tenant_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_get')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_update')
        api.keystone.tenant_get(IgnoreArg(), tenant.id, admin=True) \
                    .AndReturn(tenant)
        api.nova.tenant_quota_get(IgnoreArg(), tenant.id).AndReturn(quota)
        api.nova.tenant_quota_update(IgnoreArg(), tenant.id, **quota_data)
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:projects:quotas',
                      args=[self.tenant.id])
        quota_data.update({"method": "UpdateQuotas",
                           "tenant_id": self.tenant.id})
        res = self.client.post(url, quota_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_modify_users(self):
        self.mox.StubOutWithMock(api.keystone, 'tenant_get')
        self.mox.StubOutWithMock(api.keystone, 'user_list')
        self.mox.StubOutWithMock(api.keystone, 'roles_for_user')
        api.keystone.tenant_get(IgnoreArg(), self.tenant.id, admin=True) \
                    .AndReturn(self.tenant)
        api.keystone.user_list(IsA(http.HttpRequest)) \
                    .AndReturn(self.users.list())
        api.keystone.user_list(IsA(http.HttpRequest), self.tenant.id) \
                    .AndReturn([self.user])
        api.keystone.roles_for_user(IsA(http.HttpRequest),
                                    self.user.id,
                                    self.tenant.id) \
                    .AndReturn(self.roles.list())
        self.mox.ReplayAll()
        url = reverse('horizon:syspanel:projects:users',
                      args=(self.tenant.id,))
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'syspanel/projects/users.html')
