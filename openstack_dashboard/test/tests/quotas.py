# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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

from __future__ import absolute_import

from django import http
from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


class QuotaTests(test.APITestCase):
    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',),
                        quotas: ('is_service_enabled',),
                        cinder: ('volume_list', 'tenant_quota_get',)})
    def test_tenant_quota_usages(self):
        quotas.is_service_enabled(IsA(http.HttpRequest),
                                  'volume').AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
                .AndReturn(self.quotas.first())
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = {
            'injected_file_content_bytes': {'quota': 1},
            'metadata_items': {'quota': 1},
            'injected_files': {'quota': 1},
            'security_groups': {'quota': 10},
            'security_group_rules': {'quota': 20},
            'fixed_ips': {'quota': 10},
            'gigabytes': {'available': 920, 'used': 80, 'quota': 1000},
            'ram': {'available': 8976, 'used': 1024, 'quota': 10000},
            'floating_ips': {'available': 0, 'used': 2, 'quota': 1},
            'instances': {'available': 8, 'used': 2, 'quota': 10},
            'volumes': {'available': 0, 'used': 3, 'quota': 1},
            'cores': {'available': 8, 'used': 2, 'quota': 10}
        }

        # Compare internal structure of usages to expected.
        self.assertEquals(quota_usages.usages, expected_output)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',),
                        quotas: ('is_service_enabled',)})
    def test_tenant_quota_usages_without_volume(self):
        quotas.is_service_enabled(IsA(http.HttpRequest),
                                  'volume').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
                .AndReturn(self.quotas.first())
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = {
            'injected_file_content_bytes': {'quota': 1},
            'metadata_items': {'quota': 1},
            'injected_files': {'quota': 1},
            'security_groups': {'quota': 10},
            'security_group_rules': {'quota': 20},
            'fixed_ips': {'quota': 10},
            'ram': {'available': 8976, 'used': 1024, 'quota': 10000},
            'floating_ips': {'available': 0, 'used': 2, 'quota': 1},
            'instances': {'available': 8, 'used': 2, 'quota': 10},
            'cores': {'available': 8, 'used': 2, 'quota': 10}
        }

        # Compare internal structure of usages to expected.
        self.assertEquals(quota_usages.usages, expected_output)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',),
                        quotas: ('is_service_enabled',)})
    def test_tenant_quota_usages_no_instances_running(self):
        quotas.is_service_enabled(IsA(http.HttpRequest),
                                  'volume').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
                .AndReturn(self.quotas.first())
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn([])
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn([])

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = {
            'injected_file_content_bytes': {'quota': 1},
            'metadata_items': {'quota': 1},
            'injected_files': {'quota': 1},
            'security_groups': {'quota': 10},
            'security_group_rules': {'quota': 20},
            'fixed_ips': {'quota': 10},
            'ram': {'available': 10000, 'used': 0, 'quota': 10000},
            'floating_ips': {'available': 1, 'used': 0, 'quota': 1},
            'instances': {'available': 10, 'used': 0, 'quota': 10},
            'cores': {'available': 10, 'used': 0, 'quota': 10}
        }

        # Compare internal structure of usages to expected.
        self.assertEquals(quota_usages.usages, expected_output)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',),
                        quotas: ('is_service_enabled',),
                        cinder: ('volume_list', 'tenant_quota_get',)})
    def test_tenant_quota_usages_unlimited_quota(self):
        inf_quota = self.quotas.first()
        inf_quota['ram'] = -1

        quotas.is_service_enabled(IsA(http.HttpRequest),
                                  'volume').AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
                .AndReturn(inf_quota)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(inf_quota)

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = {
            'injected_file_content_bytes': {'quota': 1},
            'metadata_items': {'quota': 1},
            'injected_files': {'quota': 1},
            'security_groups': {'quota': 10},
            'security_group_rules': {'quota': 20},
            'fixed_ips': {'quota': 10},
            'gigabytes': {'available': 920, 'used': 80, 'quota': 1000},
            'ram': {'available': float("inf"), 'used': 1024,
                    'quota': float("inf")},
            'floating_ips': {'available': 0, 'used': 2, 'quota': 1},
            'instances': {'available': 8, 'used': 2, 'quota': 10},
            'volumes': {'available': 0, 'used': 3, 'quota': 1},
            'cores': {'available': 8, 'used': 2, 'quota': 10}
        }

        # Compare internal structure of usages to expected.
        self.assertEquals(quota_usages.usages, expected_output)
