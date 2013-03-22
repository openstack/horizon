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
from mox import IsA

from openstack_dashboard.test import helpers as test
from openstack_dashboard import api

INDEX_URL = reverse('horizon:admin:info:index')


class ServicessViewTests(test.BaseAdminViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(api.nova, 'default_quota_get')
        self.mox.StubOutWithMock(api.cinder, 'default_quota_get')
        api.nova.default_quota_get(IsA(http.HttpRequest),
                                   self.tenant.id).AndReturn(self.quotas.nova)
        api.cinder.default_quota_get(IsA(http.HttpRequest), self.tenant.id) \
                .AndReturn(self.quotas.nova)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'admin/info/index.html')

        services_tab = res.context['tab_group'].get_tab('services')
        self.assertQuerysetEqual(services_tab._tables['services'].data,
                                 ['<Service: compute>',
                                  '<Service: volume>',
                                  '<Service: image>',
                                  '<Service: identity (native backend)>',
                                  '<Service: object-store>',
                                  '<Service: network>',
                                  '<Service: ec2>'])

        quotas_tab = res.context['tab_group'].get_tab('quotas')
        self.assertQuerysetEqual(quotas_tab._tables['quotas'].data,
                                 ['<Quota: (injected_file_content_bytes, 1)>',
                                 '<Quota: (metadata_items, 1)>',
                                 '<Quota: (injected_files, 1)>',
                                 '<Quota: (gigabytes, 1000)>',
                                 '<Quota: (ram, 10000)>',
                                 '<Quota: (floating_ips, 1)>',
                                 '<Quota: (fixed_ips, 10)>',
                                 '<Quota: (instances, 10)>',
                                 '<Quota: (volumes, 1)>',
                                 '<Quota: (cores, 10)>',
                                 '<Quota: (security_groups, 10)>',
                                 '<Quota: (security_group_rules, 20)>'],
                                 ordered=False)
