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

import collections

from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _
import mock

from horizon import exceptions
from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


class QuotaTests(test.APITestCase):

    def _mock_service_enabled(self, compute_enabled=True,
                              network_enabled=False, volume_enabled=True):
        services = {'network': network_enabled,
                    'compute': compute_enabled}
        self._service_call_count = collections.defaultdict(int)

        def fake_service_enabled(request, service):
            self._service_call_count[service] += 1
            return services[service]

        self.mock_is_service_enabled.side_effect = fake_service_enabled
        self.mock_is_volume_service_enabled.return_value = volume_enabled

    def _check_service_enabled(self, expected_count):
        expected_volume_count = expected_count.pop('volume', 0)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_volume_service_enabled, expected_volume_count,
            mock.call(test.IsHttpRequest()))
        self.assertEqual(expected_count, self._service_call_count)
        total_count = sum(expected_count.values())
        self.assertEqual(total_count, self.mock_is_service_enabled.call_count)

    def get_usages(self, with_volume=True, with_compute=True,
                   nova_quotas_enabled=True, tenant_id=None):
        usages = {}
        if with_compute:
            # These are all nova fields; the neutron ones are named slightly
            # differently and aren't included in here yet
            if nova_quotas_enabled:
                usages.update({
                    'injected_file_content_bytes': {'quota': 1},
                    'metadata_items': {'quota': 1},
                    'injected_files': {'quota': 1},
                    'ram': {'available': 8976, 'used': 1024, 'quota': 10000},
                    'instances': {'available': 8, 'used': 2, 'quota': 10},
                    'cores': {'available': 8, 'used': 2, 'quota': 10},
                    'key_pairs': {'quota': 100},
                    'injected_file_path_bytes': {'quota': 255}
                })
                if tenant_id == 3:
                    usages.update({
                        'ram': {'available': 10000,
                                'used': 0,
                                'quota': 10000},
                        'instances': {'available': 10, 'used': 2, 'quota': 10},
                        'cores': {'available': 10, 'used': 2, 'quota': 10}
                    })

        if with_volume:
            usages.update({'volumes': {'available': 0, 'used': 4, 'quota': 1},
                           'snapshots': {'available': 0, 'used': 3,
                                         'quota': 1},
                           'gigabytes': {'available': 600, 'used': 400,
                                         'quota': 1000}})
        return usages

    def get_usages_from_limits(self, with_volume=True, with_compute=True,
                               nova_quotas_enabled=True,
                               unlimited_items=None):
        usages = {}
        if with_compute and nova_quotas_enabled:
            usages.update({
                'instances': {'available': 8, 'used': 2, 'quota': 10},
                'cores': {'available': 18, 'used': 2, 'quota': 20},
                'ram': {'available': 8976, 'used': 1024, 'quota': 10000},
                'key_pairs': {'quota': 100},
            })
        if with_volume:
            usages.update({
                'volumes': {'available': 16, 'used': 4, 'quota': 20},
                'gigabytes': {'available': 600, 'used': 400, 'quota': 1000},
                'snapshots': {'available': 7, 'used': 3, 'quota': 10},
            })
        if unlimited_items:
            for item in unlimited_items:
                usages[item]['available'] = float('inf')
                usages[item]['quota'] = float('inf')
        return usages

    def assertAvailableQuotasEqual(self, expected_usages, actual_usages,
                                   msg=None):
        expected_available = {key: value['available'] for key, value in
                              expected_usages.items() if 'available' in value}
        actual_available = {key: value['available'] for key, value in
                            actual_usages.items() if 'available' in value}
        self.assertEqual(expected_available, actual_available, msg=msg)

    @test.create_mocks({
        api.nova: (('tenant_absolute_limits', 'nova_tenant_absolute_limits'),),
        api.base: ('is_service_enabled',),
        cinder: (('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
                 'is_volume_service_enabled')})
    def test_tenant_quota_usages_with_id(self):
        tenant_id = 3

        self._mock_service_enabled()
        self.mock_nova_tenant_absolute_limits.return_value = \
            self.limits['absolute']
        self.mock_cinder_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request,
                                                  tenant_id=tenant_id)
        expected_output = self.get_usages_from_limits(
            with_volume=True, with_compute=True)

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)
        # Compare available resources
        self.assertAvailableQuotasEqual(expected_output, quota_usages.usages)

        self._check_service_enabled({'compute': 2, 'network': 1, 'volume': 1})
        self.mock_nova_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), reserved=True, tenant_id=tenant_id)
        self.mock_cinder_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), tenant_id)

    @test.create_mocks({
        api.nova: (('tenant_absolute_limits', 'nova_tenant_absolute_limits'),),
        api.base: ('is_service_enabled',),
        cinder: (('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
                 'is_volume_service_enabled')})
    def _test_tenant_quota_usages(self,
                                  nova_quotas_enabled=True,
                                  with_compute=True, with_volume=True,
                                  unlimited_items=None):
        tenant_id = '1'

        self._mock_service_enabled(compute_enabled=with_compute,
                                   volume_enabled=with_volume)
        if with_compute and nova_quotas_enabled:
            self.mock_nova_tenant_absolute_limits.return_value = \
                self.limits['absolute']
        if with_volume:
            self.mock_cinder_tenant_absolute_limits.return_value = \
                self.cinder_limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages_from_limits(
            nova_quotas_enabled=nova_quotas_enabled,
            with_volume=with_volume,
            with_compute=with_compute,
            unlimited_items=unlimited_items)

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)
        # Compare available resources
        self.assertAvailableQuotasEqual(expected_output, quota_usages.usages)

        if with_compute and nova_quotas_enabled:
            self._check_service_enabled({'compute': 2, 'network': 1,
                                         'volume': 1})
            self.mock_nova_tenant_absolute_limits.assert_called_once_with(
                test.IsHttpRequest(), reserved=True, tenant_id=tenant_id)
        else:
            self._check_service_enabled({'compute': 1, 'network': 1,
                                         'volume': 1})
            self.mock_nova_tenant_absolute_limits.assert_not_called()
        if with_volume:
            self.mock_cinder_tenant_absolute_limits.assert_called_once_with(
                test.IsHttpRequest(), tenant_id)
        else:
            self.mock_cinder_tenant_absolute_limits.assert_not_called()

    def test_tenant_quota_usages(self):
        self._test_tenant_quota_usages()

    @override_settings(OPENSTACK_HYPERVISOR_FEATURES={'enable_quotas': False})
    def test_tenant_quota_usages_wo_nova_quotas(self):
        self._test_tenant_quota_usages(nova_quotas_enabled=False,
                                       with_compute=True,
                                       with_volume=False)

    def test_tenant_quota_usages_with_unlimited(self):
        self.limits['absolute']['maxTotalInstances'] = float('inf')
        self._test_tenant_quota_usages(unlimited_items=['instances'])

    @override_settings(OPENSTACK_HYPERVISOR_FEATURES={'enable_quotas': False})
    @test.create_mocks({api.base: ('is_service_enabled',),
                        cinder: ('is_volume_service_enabled',)})
    def test_get_all_disabled_quotas(self):
        self._mock_service_enabled(volume_enabled=False)

        result_quotas = quotas.get_disabled_quotas(self.request)
        expected_quotas = (quotas.CINDER_QUOTA_FIELDS |
                           quotas.NEUTRON_QUOTA_FIELDS |
                           quotas.NOVA_QUOTA_FIELDS)
        self.assertItemsEqual(result_quotas, expected_quotas)

        self._check_service_enabled({'compute': 1, 'network': 1, 'volume': 1})

    @test.create_mocks({api.nova: ('tenant_absolute_limits',),
                        api.base: ('is_service_enabled',),
                        cinder: ('is_volume_service_enabled',)})
    def test_tenant_quota_usages_without_volume(self):
        tenant_id = self.request.user.tenant_id

        self._mock_service_enabled(volume_enabled=False)
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages_from_limits(with_volume=False)

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

        # Make sure that the `in` operator and the `.get()` method
        # behave as expected
        self.assertIn('ram', quota_usages)
        self.assertIsNotNone(quota_usages.get('ram'))

        self._check_service_enabled({'compute': 2, 'network': 1, 'volume': 1})
        self.mock_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), reserved=True, tenant_id=tenant_id)

    @test.create_mocks({api.nova: ('tenant_absolute_limits',),
                        api.base: ('is_service_enabled',),
                        cinder: ('is_volume_service_enabled',)})
    def test_tenant_quota_usages_no_instances_running(self):
        self._mock_service_enabled(volume_enabled=False)
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages_from_limits(with_volume=False)

        expected_output.update({
            'ram': {'available': 10000, 'used': 0, 'quota': 10000},
            'instances': {'available': 10, 'used': 0, 'quota': 10},
            'cores': {'available': 10, 'used': 0, 'quota': 10}})

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

        self._check_service_enabled({'compute': 2, 'network': 1, 'volume': 1})
        self.mock_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), reserved=True, tenant_id='1')

    @test.create_mocks({
        api.nova: (('tenant_absolute_limits', 'nova_tenant_absolute_limits'),),
        api.base: ('is_service_enabled',),
        cinder: (('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
                 'is_volume_service_enabled')})
    def test_tenant_quota_usages_unlimited_quota(self):
        tenant_id = '1'
        inf_quota = self.quotas.first()
        inf_quota['ram'] = -1

        self._mock_service_enabled()
        self.mock_nova_tenant_absolute_limits.return_value = \
            self.limits['absolute']
        self.mock_cinder_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages_from_limits()
        expected_output.update({'ram': {'available': float("inf"),
                                        'used': 1024,
                                        'quota': float("inf")}})

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

        self._check_service_enabled({'compute': 2, 'network': 1, 'volume': 1})
        self.mock_nova_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), reserved=True, tenant_id=tenant_id)
        self.mock_cinder_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), tenant_id)

    @test.create_mocks({
        api.nova: (('tenant_absolute_limits', 'nova_tenant_absolute_limits'),),
        api.base: ('is_service_enabled',),
        cinder: (('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
                 'is_volume_service_enabled')})
    def test_tenant_quota_usages_neutron_fip_disabled(self):
        tenant_id = '1'

        self._mock_service_enabled()
        self.mock_nova_tenant_absolute_limits.return_value = \
            self.limits['absolute']
        self.mock_cinder_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request)
        expected_output = self.get_usages_from_limits()

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected_output, quota_usages.usages)

        self._check_service_enabled({'compute': 2, 'network': 1, 'volume': 1})
        self.mock_nova_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), reserved=True, tenant_id=tenant_id)
        self.mock_cinder_tenant_absolute_limits.assert_called_once_with(
            test.IsHttpRequest(), tenant_id)

    @test.create_mocks({api.base: ('is_service_enabled',),
                        cinder: ('tenant_quota_get',
                                 'is_volume_service_enabled'),
                        exceptions: ('handle',)})
    def test_get_quota_data_cinder_exception(self):
        self._mock_service_enabled(compute_enabled=False)
        self.mock_tenant_quota_get.side_effect = \
            cinder.cinder_exception.ClientException('test')

        quotas.get_tenant_quota_data(self.request)

        self._check_service_enabled({'compute': 1, 'network': 1, 'volume': 1})
        self.mock_tenant_quota_get.assert_called_once_with(
            test.IsHttpRequest(), '1')
        self.mock_handle.assert_called_once_with(
            test.IsHttpRequest(),
            _("Unable to retrieve volume limit information."))

    @test.create_mocks({api.neutron: ('is_router_enabled',
                                      'is_extension_supported',
                                      'is_quotas_extension_supported',),
                        api.cinder: ('is_volume_service_enabled',),
                        api.base: ('is_service_enabled',)})
    def test_get_disabled_quotas_router_disabled(self):
        self._mock_service_enabled(network_enabled=True)
        self.mock_is_extension_supported.return_value = True
        self.mock_is_router_enabled.return_value = False
        self.mock_is_quotas_extension_supported.return_value = True

        disabled_quotas = quotas.get_disabled_quotas(self.request)
        expected = set(['router', 'floatingip'])
        self.assertEqual(expected, disabled_quotas)

        self._check_service_enabled({'compute': 1, 'network': 1, 'volume': 1})
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'security-group')
        self.mock_is_router_enabled.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_is_quotas_extension_supported.assert_called_once_with(
            test.IsHttpRequest())

    def test_tenant_quota_usages_with_target_instances(self):
        self._test_tenant_quota_usages_with_target(
            targets=('instances',), use_cinder_call=False)

    def test_tenant_quota_usages_with_target_ram(self):
        self._test_tenant_quota_usages_with_target(
            targets=('ram',), use_flavor_list=True, use_cinder_call=False)

    def test_tenant_quota_usages_with_target_volume(self):
        self._test_tenant_quota_usages_with_target(
            targets=('volumes',), use_compute_call=False,
            use_cinder_call=True)

    def test_tenant_quota_usages_with_target_compute_volume(self):
        self._test_tenant_quota_usages_with_target(
            targets=('instances', 'cores', 'ram', 'volumes',),
            use_flavor_list=True, use_cinder_call=True)

    @test.create_mocks({
        api.nova: (('tenant_absolute_limits', 'nova_tenant_absolute_limits'),),
        api.base: ('is_service_enabled',),
        cinder: (('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
                 'is_volume_service_enabled')})
    def _test_tenant_quota_usages_with_target(
            self, targets, use_compute_call=True,
            use_flavor_list=False, use_cinder_call=False):

        tenant_id = self.request.user.tenant_id

        self._mock_service_enabled()
        if use_compute_call:
            self.mock_nova_tenant_absolute_limits.return_value = \
                self.limits['absolute']
        if use_cinder_call:
            self.mock_cinder_tenant_absolute_limits.return_value = \
                self.cinder_limits['absolute']

        quota_usages = quotas.tenant_quota_usages(self.request,
                                                  targets=targets)

        expected = self.get_usages_from_limits()
        expected = dict((k, v) for k, v in expected.items() if k in targets)

        # Compare internal structure of usages to expected.
        self.assertItemsEqual(expected, quota_usages.usages)
        # Compare available resources
        self.assertAvailableQuotasEqual(expected, quota_usages.usages)

        expected_count = {}
        if use_compute_call:
            expected_count['compute'] = 2
        if use_cinder_call:
            expected_count['volume'] = 1
        self._check_service_enabled(expected_count)
        if use_compute_call:
            self.mock_nova_tenant_absolute_limits.assert_called_once_with(
                test.IsHttpRequest(), reserved=True, tenant_id=tenant_id)
        else:
            self.mock_nova_tenant_absolute_limits.assert_not_called()
        if use_cinder_call:
            self.mock_cinder_tenant_absolute_limits.assert_called_once_with(
                test.IsHttpRequest(), tenant_id)
        else:
            self.mock_cinder_tenant_absolute_limits.assert_not_called()

    def test_tenant_quota_usages_neutron_with_target_network_resources(self):
        self._test_tenant_quota_usages_neutron_with_target(
            targets=('network', 'subnet', 'router',))

    def test_tenant_quota_usages_neutron_with_target_security_groups(self):
        self._test_tenant_quota_usages_neutron_with_target(
            targets=('security_group',))

    def test_tenant_quota_usages_neutron_with_target_floating_ips(self):
        self._test_tenant_quota_usages_neutron_with_target(
            targets=('floatingip',))

    def test_tenant_quota_usages_neutron_with_target_security_group_rule(self):
        self._test_tenant_quota_usages_neutron_with_target(
            targets=('security_group_rule',)
        )

    def _list_security_group_rules(self):
        security_groups = self.security_groups.list()
        security_group_rules = []
        for group in security_groups:
            security_group_rules += group.security_group_rules
        return security_group_rules

    # Tests network quota retrieval via neutron.tenant_quota_detail_get
    # rather than quotas._get_tenant_network_usages_legacy (see
    # quotas._get_tenant_network_usages)
    @test.create_mocks({api.base: ('is_service_enabled',),
                        cinder: ('is_volume_service_enabled',),
                        api.neutron: ('floating_ip_supported',
                                      'is_extension_supported',
                                      'is_quotas_extension_supported',
                                      'tenant_quota_detail_get')})
    def test_tenant_quota_usages_non_legacy(self):
        self._mock_service_enabled(network_enabled=True)
        self.mock_is_extension_supported.return_value = True

        test_data = [
            ("network", self.networks.list(), 10),
            ("subnet", self.subnets.list(), 10),
            ("port", self.ports.list(), 100),
            ("router", self.routers.list(), 10),
            ("floatingip", self.floating_ips.list(), 50),
            ("security_group", self.security_groups.list(), 20),
            ("security_group_rule", self._list_security_group_rules(), 100)
        ]

        for datum in test_data:
            target = datum[0]
            used = len(datum[1])
            limit = datum[2]

            expected = {
                target: {
                    'used': used,
                    'quota': limit,
                    'available': limit - used
                }
            }

            self.mock_tenant_quota_detail_get.return_value = {
                target: {
                    'reserved': 0,
                    'used': used,
                    'limit': limit
                }
            }

            quota_usages = quotas.tenant_quota_usages(self.request,
                                                      targets=(target,))

            msg = "Test failure for resource: '{}'".format(target)
            # Compare internal structure of usages to expected.
            self.assertEqual(expected, quota_usages.usages, msg=msg)
            # Compare available resources
            self.assertAvailableQuotasEqual(expected, quota_usages.usages,
                                            msg=msg)

    @test.create_mocks({api.base: ('is_service_enabled',),
                        cinder: ('is_volume_service_enabled',),
                        api.neutron: ('floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list',
                                      'is_extension_supported',
                                      'is_router_enabled',
                                      'is_quotas_extension_supported',
                                      'tenant_quota_get',
                                      'network_list',
                                      'subnet_list',
                                      'router_list')})
    def _test_tenant_quota_usages_neutron_with_target(self, targets):
        self._mock_service_enabled(network_enabled=True)
        if 'security_group' in targets or 'security_group_rule' in targets:
            self.mock_is_extension_supported.side_effect = [True, False]
        else:
            self.mock_is_extension_supported.side_effect = [False]
        self.mock_is_router_enabled.return_value = True
        self.mock_is_quotas_extension_supported.return_value = True
        self.mock_tenant_quota_get.return_value = self.neutron_quotas.first()

        if 'network' in targets:
            self.mock_network_list.return_value = self.networks.list()
        if 'subnet' in targets:
            self.mock_subnet_list.return_value = self.subnets.list()
        if 'router' in targets:
            self.mock_router_list.return_value = self.routers.list()
        if 'floatingip' in targets:
            self.mock_tenant_floating_ip_list.return_value = \
                self.floating_ips.list()
        if 'security_group' in targets or 'security_group_rule' in targets:
            self.mock_security_group_list.return_value = \
                self.security_groups.list()

        quota_usages = quotas.tenant_quota_usages(self.request,
                                                  targets=targets)

        network_used = len(self.networks.list())
        subnet_used = len(self.subnets.list())
        router_used = len(self.routers.list())
        fip_used = len(self.floating_ips.list())

        security_groups = self.security_groups.list()
        sg_used = len(security_groups)
        sgr_used = sum(map(
            lambda group: len(group.security_group_rules),
            security_groups
        ))

        expected = {
            'network': {'used': network_used, 'quota': 10,
                        'available': 10 - network_used},
            'subnet': {'used': subnet_used, 'quota': 10,
                       'available': 10 - subnet_used},
            'router': {'used': router_used, 'quota': 10,
                       'available': 10 - router_used},
            'security_group': {'used': sg_used, 'quota': 20,
                               'available': 20 - sg_used},
            'security_group_rule': {
                'quota': 100, 'used': sgr_used, 'available': 100 - sgr_used
            },
            'floatingip': {'used': fip_used, 'quota': 50,
                           'available': 50 - fip_used},
        }
        expected = dict((k, v) for k, v in expected.items() if k in targets)

        # Compare internal structure of usages to expected.
        self.assertEqual(expected, quota_usages.usages)
        # Compare available resources
        self.assertAvailableQuotasEqual(expected, quota_usages.usages)

        self._check_service_enabled({'network': 1})

        if 'security_group' in targets or 'security_group_rule' in targets:
            self.mock_is_extension_supported.assert_has_calls([
                mock.call(test.IsHttpRequest(), 'security-group'),
                mock.call(test.IsHttpRequest(), 'quota_details'),
            ])
            self.assertEqual(2, self.mock_is_extension_supported.call_count)
        else:
            self.mock_is_extension_supported.assert_called_once_with(
                test.IsHttpRequest(), 'quota_details')
        if 'floatingip' in targets or 'router' in targets:
            self.mock_is_router_enabled.assert_called_once_with(
                test.IsHttpRequest())
        else:
            self.mock_is_router_enabled.assert_not_called()
        self.mock_is_quotas_extension_supported.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_quota_get.assert_called_once_with(
            test.IsHttpRequest(), '1')
        if 'network' in targets:
            self.mock_network_list.assert_called_once_with(
                test.IsHttpRequest(),
                tenant_id=self.request.user.tenant_id)
        else:
            self.mock_network_list.assert_not_called()
        if 'subnet' in targets:
            self.mock_subnet_list.assert_called_once_with(
                test.IsHttpRequest(),
                tenant_id=self.request.user.tenant_id)
        else:
            self.mock_subnet_list.assert_not_called()
        if 'router' in targets:
            self.mock_router_list.assert_called_once_with(
                test.IsHttpRequest(),
                tenant_id=self.request.user.tenant_id)
        else:
            self.mock_router_list.assert_not_called()
        if 'floatingip' in targets:
            self.mock_tenant_floating_ip_list.assert_called_once_with(
                test.IsHttpRequest())
        else:
            self.mock_tenant_floating_ip_list.assert_not_called()
        if 'security_group' in targets or 'security_group_rule' in targets:
            self.mock_security_group_list.assert_called_once_with(
                test.IsHttpRequest())
        else:
            self.mock_security_group_list.assert_not_called()
