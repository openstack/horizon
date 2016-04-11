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
from django.utils.translation import ugettext_lazy as _
from mox3.mox import IsA  # noqa

from horizon import exceptions
from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


class QuotaTests(test.APITestCase):

    def get_usages(self, with_volume=True):
        usages = {'injected_file_content_bytes': {'quota': 1},
                  'metadata_items': {'quota': 1},
                  'injected_files': {'quota': 1},
                  'security_groups': {'quota': 10},
                  'security_group_rules': {'quota': 20},
                  'fixed_ips': {'quota': 10},
                  'ram': {'available': 8976, 'used': 1024, 'quota': 10000},
                  'floating_ips': {'available': 0, 'used': 2, 'quota': 1},
                  'instances': {'available': 8, 'used': 2, 'quota': 10},
                  'cores': {'available': 8, 'used': 2, 'quota': 10}}
        if with_volume:
            usages.update({'volumes': {'available': 0, 'used': 4, 'quota': 1},
                           'snapshots': {'available': 0, 'used': 3,
                                         'quota': 1},
                           'gigabytes': {'available': 880, 'used': 120,
                                         'quota': 1000}})
        return usages

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',
                                      'floating_ip_supported'),
                        api.base: ('is_service_enabled',),
                        cinder: ('volume_list', 'volume_snapshot_list',
                                 'tenant_quota_get',
                                 'is_volume_service_enabled')})
    def test_tenant_quota_usages(self):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest),
                                    'network').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        search_opts = {'tenant_id': self.request.user.tenant_id}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts,
                             all_tenants=True) \
            .AndReturn([servers, False])
        opts = {'all_tenants': 1, 'project_id': self.request.user.tenant_id}
        cinder.volume_list(IsA(http.HttpRequest), opts) \
            .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest), opts) \
            .AndReturn(self.cinder_volume_snapshots.list())
        cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.cinder_quotas.first())

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages()

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',
                                      'floating_ip_supported'),
                        api.base: ('is_service_enabled',),
                        api.cinder: ('is_volume_service_enabled',)})
    def test_tenant_quota_usages_without_volume(self):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        api.cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(False)
        api.base.is_service_enabled(IsA(http.HttpRequest),
                                    'network').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        search_opts = {'tenant_id': self.request.user.tenant_id}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts,
                             all_tenants=True) \
            .AndReturn([servers, False])

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages(with_volume=False)

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

        # Make sure that the `in` operator and the `.get()` method
        # behave as expected
        self.assertIn('ram', quota_usages)
        self.assertIsNotNone(quota_usages.get('ram'))

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',
                                      'floating_ip_supported'),
                        api.base: ('is_service_enabled',),
                        api.cinder: ('is_volume_service_enabled',)})
    def test_tenant_quota_usages_no_instances_running(self):
        api.cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(False)
        api.base.is_service_enabled(IsA(http.HttpRequest),
                                    'network').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        search_opts = {'tenant_id': self.request.user.tenant_id}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts,
                             all_tenants=True) \
            .AndReturn([[], False])

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages(with_volume=False)

        expected_output.update({
            'ram': {'available': 10000, 'used': 0, 'quota': 10000},
            'floating_ips': {'available': 1, 'used': 0, 'quota': 1},
            'instances': {'available': 10, 'used': 0, 'quota': 10},
            'cores': {'available': 10, 'used': 0, 'quota': 10}})

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',
                                      'floating_ip_supported'),
                        api.base: ('is_service_enabled',),
                        cinder: ('volume_list', 'volume_snapshot_list',
                                 'tenant_quota_get',
                                 'is_volume_service_enabled')})
    def test_tenant_quota_usages_unlimited_quota(self):
        inf_quota = self.quotas.first()
        inf_quota['ram'] = -1
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest),
                                    'network').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(inf_quota)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        search_opts = {'tenant_id': self.request.user.tenant_id}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts,
                             all_tenants=True) \
            .AndReturn([servers, False])
        opts = {'all_tenants': 1, 'project_id': self.request.user.tenant_id}
        cinder.volume_list(IsA(http.HttpRequest), opts) \
            .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest), opts) \
            .AndReturn(self.cinder_volume_snapshots.list())
        cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.cinder_quotas.first())

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages()
        expected_output.update({'ram': {'available': float("inf"),
                                        'used': 1024,
                                        'quota': float("inf")}})

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'tenant_quota_get',),
                        api.network: ('tenant_floating_ip_list',
                                      'floating_ip_supported'),
                        api.base: ('is_service_enabled',),
                        cinder: ('volume_list', 'volume_snapshot_list',
                                 'tenant_quota_get',
                                 'is_volume_service_enabled')})
    def test_tenant_quota_usages_neutron_fip_disabled(self):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest),
                                    'network').AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(False)
        search_opts = {'tenant_id': self.request.user.tenant_id}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts,
                             all_tenants=True) \
            .AndReturn([servers, False])
        opts = {'all_tenants': 1, 'project_id': self.request.user.tenant_id}
        cinder.volume_list(IsA(http.HttpRequest), opts) \
            .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest), opts) \
            .AndReturn(self.cinder_volume_snapshots.list())
        cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.cinder_quotas.first())

        self.mox.ReplayAll()

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages()
        expected_output['floating_ips']['used'] = 0
        expected_output['floating_ips']['available'] = 1

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

    @test.create_stubs({cinder: ('volume_list',),
                        exceptions: ('handle',)})
    def test_get_tenant_volume_usages_cinder_exception(self):
        cinder.volume_list(IsA(http.HttpRequest)) \
            .AndRaise(cinder.cinder_exception.ClientException('test'))
        exceptions.handle(IsA(http.HttpRequest),
                          _("Unable to retrieve volume limit information."))
        self.mox.ReplayAll()

        quotas._get_tenant_volume_usages(self.request, {}, [], None)

    @test.create_stubs({api.nova: ('tenant_quota_get',),
                        api.base: ('is_service_enabled',),
                        api.cinder: ('tenant_quota_get',
                                     'is_volume_service_enabled'),
                        exceptions: ('handle',)})
    def test_get_quota_data_cinder_exception(self):
        api.cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest),
                                    'network').AndReturn(False)
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndRaise(cinder.cinder_exception.ClientException('test'))
        exceptions.handle(IsA(http.HttpRequest),
                          _("Unable to retrieve volume limit information."))
        self.mox.ReplayAll()

        quotas._get_quota_data(self.request, 'tenant_quota_get')

    @test.create_stubs({api.nova: ('tenant_absolute_limits',),
                        api.base: ('is_service_enabled',),
                        api.cinder: ('tenant_absolute_limits',
                                     'is_volume_service_enabled'),
                        exceptions: ('handle',)})
    def test_tenant_limit_usages_cinder_exception(self):
        api.cinder.is_volume_service_enabled(
            IsA(http.HttpRequest)
        ).AndReturn(True)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)).AndReturn({})
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndRaise(cinder.cinder_exception.ClientException('test'))
        exceptions.handle(IsA(http.HttpRequest),
                          _("Unable to retrieve volume limit information."))
        self.mox.ReplayAll()
        quotas.tenant_limit_usages(self.request)
