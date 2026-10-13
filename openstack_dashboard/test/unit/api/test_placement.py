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

import threading
from unittest import mock

from keystoneauth1 import exceptions as ks_exceptions

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class PlacementApiTests(test.APIMockTestCase):

    INVENTORIES = {
        'host1-uuid': {
            'VCPU': {'total': 16, 'reserved': 4, 'allocation_ratio': 4.0},
            'PCPU': {'total': 4, 'reserved': 2, 'allocation_ratio': 1.0},
            'MEMORY_MB': {'total': 32768, 'reserved': 512,
                          'allocation_ratio': 1.5},
            'DISK_GB': {'total': 500, 'reserved': 10,
                        'allocation_ratio': 1.0},
        },
        'host2-uuid': {
            'VCPU': {'total': 8, 'reserved': 0, 'allocation_ratio': 16.0},
            'MEMORY_MB': {'total': 16384, 'reserved': 0,
                          'allocation_ratio': 1.0},
        },
    }
    USAGES = {
        'host1-uuid': {'VCPU': 2, 'PCPU': 1, 'MEMORY_MB': 8192,
                       'DISK_GB': 100},
        'host2-uuid': {'VCPU': 0, 'MEMORY_MB': 0},
    }

    def _providers(self, *uuids, parent=None):
        return [{'uuid': uuid, 'name': uuid.split('-')[0],
                 'parent_provider_uuid': parent} for uuid in uuids]

    @test.create_mocks({api.placement: ['resource_providers',
                                        'resource_provider_inventories',
                                        'resource_provider_usages']})
    def test_get_providers(self):
        self.mock_resource_providers.return_value = (
            self._providers('host1-uuid', 'host2-uuid') +
            self._providers('vgpu-uuid', parent='host1-uuid'))
        self.mock_resource_provider_inventories.side_effect = \
            lambda request, uuid: self.INVENTORIES[uuid]
        self.mock_resource_provider_usages.side_effect = \
            lambda request, uuid: self.USAGES[uuid]

        providers = api.placement.get_providers(self.request)

        self.assertEqual([
            {
                'uuid': 'host1-uuid', 'name': 'host1',
                'parent_provider_uuid': None,
                'inventories': self.INVENTORIES['host1-uuid'],
                'usages': self.USAGES['host1-uuid'],
                'vcpus_used': 2, 'vcpus_reserved': 4,
                'vcpus': 16, 'vcpus_ar': 4.0, 'vcpus_capacity': 64,
                'pcpus_used': 1, 'pcpus_reserved': 2,
                'pcpus': 4, 'pcpus_ar': 1.0, 'pcpus_capacity': 4,
                'memory_mb_used': 8192, 'memory_mb_reserved': 512,
                'memory_mb': 32768, 'memory_mb_ar': 1.5,
                'memory_mb_capacity': 49152.0,
                'disk_gb_used': 100, 'disk_gb_reserved': 10,
                'disk_gb': 500, 'disk_gb_ar': 1.0, 'disk_gb_capacity': 500.0,
            },
            {
                'uuid': 'host2-uuid', 'name': 'host2',
                'parent_provider_uuid': None,
                'inventories': self.INVENTORIES['host2-uuid'],
                'usages': self.USAGES['host2-uuid'],
                'vcpus_used': 0, 'vcpus_reserved': 0,
                'vcpus': 8, 'vcpus_ar': 16.0, 'vcpus_capacity': 128,
                'pcpus_used': None, 'pcpus_reserved': None,
                'pcpus': None, 'pcpus_ar': None, 'pcpus_capacity': None,
                'memory_mb_used': 0, 'memory_mb_reserved': 0,
                'memory_mb': 16384, 'memory_mb_ar': 1.0,
                'memory_mb_capacity': 16384.0,
                'disk_gb_used': None, 'disk_gb_reserved': None,
                'disk_gb': None, 'disk_gb_ar': None, 'disk_gb_capacity': None,
            },
        ], providers)

        self.mock_resource_providers.assert_called_once_with(self.request)
        expected_calls = [mock.call(self.request, 'host1-uuid'),
                          mock.call(self.request, 'host2-uuid')]
        self.mock_resource_provider_inventories.assert_has_calls(
            expected_calls, any_order=True)
        self.assertEqual(
            2, self.mock_resource_provider_inventories.call_count)
        self.mock_resource_provider_usages.assert_has_calls(
            expected_calls, any_order=True)
        self.assertEqual(2, self.mock_resource_provider_usages.call_count)

    @test.create_mocks({api.placement: ['resource_providers',
                                        'resource_provider_inventories',
                                        'resource_provider_usages']})
    def test_get_providers_parallel_keeps_order(self):
        uuids = ['host%d-uuid' % i for i in range(5)]
        self.mock_resource_providers.return_value = self._providers(*uuids)
        last_done = threading.Event()

        def inventories(request, uuid):
            # Serial execution would never get to the last provider here.
            if uuid == uuids[0] and not last_done.wait(timeout=10):
                raise AssertionError('provider details fetched serially')
            return {}

        def usages(request, uuid):
            if uuid == uuids[-1]:
                last_done.set()
            return {}

        self.mock_resource_provider_inventories.side_effect = inventories
        self.mock_resource_provider_usages.side_effect = usages

        providers = api.placement.get_providers(self.request)

        self.assertEqual(uuids, [p['uuid'] for p in providers])

    @test.create_mocks({api.placement: ['resource_providers',
                                        'resource_provider_inventories',
                                        'resource_provider_usages']})
    def test_get_providers_error(self):
        self.mock_resource_providers.return_value = self._providers(
            'host1-uuid', 'host2-uuid')
        self.mock_resource_provider_inventories.return_value = {}
        self.mock_resource_provider_usages.side_effect = [
            {}, ks_exceptions.ServiceUnavailable()]

        self.assertRaises(ks_exceptions.ServiceUnavailable,
                          api.placement.get_providers, self.request)

    @test.create_mocks({api.placement: ['resource_providers',
                                        'resource_provider_inventories',
                                        'resource_provider_usages']})
    def test_get_providers_no_providers(self):
        self.mock_resource_providers.return_value = []

        self.assertEqual([], api.placement.get_providers(self.request))

        self.mock_resource_provider_inventories.assert_not_called()
        self.mock_resource_provider_usages.assert_not_called()
