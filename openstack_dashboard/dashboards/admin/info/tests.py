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

from django.core.urlresolvers import reverse  # noqa
from django import http
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:info:index')


class SystemInfoViewTests(test.BaseAdminViewTests):

    @test.create_stubs({api.nova: ('default_quota_get',
                                   'service_list',
                                   'availability_zone_list',
                                   'aggregate_list'),
                        api.cinder: ('default_quota_get',)})
    def test_index(self):
        api.nova.default_quota_get(IsA(http.HttpRequest),
                                   self.tenant.id).AndReturn(self.quotas.nova)
        api.cinder.default_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.cinder_quotas.first())
        services = self.services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)
        api.nova.availability_zone_list(IsA(http.HttpRequest), detailed=True) \
            .AndReturn(self.availability_zones.list())
        api.nova.aggregate_list(IsA(http.HttpRequest)) \
            .AndReturn(self.aggregates.list())

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
                                  '<Service: ec2>',
                                  '<Service: metering>',
                                  '<Service: orchestration>'])

        quotas_tab = res.context['tab_group'].get_tab('quotas')
        self.assertQuerysetEqual(quotas_tab._tables['quotas'].data,
                                 ['<Quota: (injected_file_content_bytes, 1)>',
                                 '<Quota: (metadata_items, 1)>',
                                 '<Quota: (injected_files, 1)>',
                                 '<Quota: (gigabytes, 1000)>',
                                 '<Quota: (ram, 10000)>',
                                 '<Quota: (instances, 10)>',
                                 '<Quota: (snapshots, 1)>',
                                 '<Quota: (volumes, 1)>',
                                 '<Quota: (cores, 10)>',
                                 '<Quota: (security_groups, 10)>',
                                 '<Quota: (security_group_rules, 20)>'],
                                 ordered=False)

        zones_tab = res.context['tab_group'].get_tab('zones')
        self.assertQuerysetEqual(zones_tab._tables['zones'].data,
                                 ['<AvailabilityZone: nova>'])

        aggregates_tab = res.context['tab_group'].get_tab('aggregates')
        self.assertQuerysetEqual(aggregates_tab._tables['aggregates'].data,
                                 ['<Aggregate: 1>', '<Aggregate: 2>'])

    @test.create_stubs({api.base: ('is_service_enabled',),
                        api.nova: ('default_quota_get',
                                   'service_list',
                                   'availability_zone_list',
                                   'aggregate_list'),
                        api.cinder: ('default_quota_get',)})
    def test_index_with_neutron_disabled(self):
        # Neutron does not have an API for getting default system
        # quotas. When not using Neutron, the floating ips quotas
        # should be in the list.
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
                .AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
                .MultipleTimes().AndReturn(False)

        api.nova.default_quota_get(IsA(http.HttpRequest),
                                   self.tenant.id).AndReturn(self.quotas.nova)

        api.cinder.default_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.cinder_quotas.first())
        services = self.services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)
        api.nova.availability_zone_list(IsA(http.HttpRequest), detailed=True) \
            .AndReturn(self.availability_zones.list())
        api.nova.aggregate_list(IsA(http.HttpRequest)) \
            .AndReturn(self.aggregates.list())

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
                                  '<Service: ec2>',
                                  '<Service: metering>',
                                  '<Service: orchestration>'])

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
                                 '<Quota: (snapshots, 1)>',
                                 '<Quota: (volumes, 1)>',
                                 '<Quota: (cores, 10)>',
                                 '<Quota: (security_groups, 10)>',
                                 '<Quota: (security_group_rules, 20)>'],
                                 ordered=False)

        zones_tab = res.context['tab_group'].get_tab('zones')
        self.assertQuerysetEqual(zones_tab._tables['zones'].data,
                                 ['<AvailabilityZone: nova>'])

        aggregates_tab = res.context['tab_group'].get_tab('aggregates')
        self.assertQuerysetEqual(aggregates_tab._tables['aggregates'].data,
                                 ['<Aggregate: 1>', '<Aggregate: 2>'])
