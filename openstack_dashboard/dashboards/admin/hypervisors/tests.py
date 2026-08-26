# Copyright 2013 B1 Systems GmbH
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

from django.test import override_settings
from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class HypervisorViewTest(test.BaseAdminViewTests):

    TEST_PROVIDER = {
        'uuid': 'test-provider-uuid',
        'name': 'test-host',
        'parent_provider_uuid': None,
        'root_provider_uuid': 'test-provider-uuid',
        'inventories': {
            'VCPU': {'total': 16, 'reserved': 4, 'allocation_ratio': 4.0},
            'PCPU': {'total': 4, 'reserved': 2, 'allocation_ratio': 1.0},
            'MEMORY_MB': {'total': 32768, 'reserved': 512,
                          'allocation_ratio': 1.5},
            'DISK_GB': {'total': 500, 'reserved': 10,
                        'allocation_ratio': 1.0},
        },
        'usages': {'VCPU': 2, 'PCPU': 1, 'MEMORY_MB': 8192, 'DISK_GB': 100},
        'vcpus_used': 2, 'vcpus_reserved': 4,
        'vcpus': 16, 'vcpus_ar': 4.0, 'vcpus_capacity': 64,
        'pcpus_used': 1, 'pcpus_reserved': 2,
        'pcpus': 4, 'pcpus_ar': 1.0, 'pcpus_capacity': 4,
        'memory_mb_used': 8192, 'memory_mb_reserved': 512,
        'memory_mb': 32768, 'memory_mb_ar': 1.5,
        'memory_mb_capacity': 49152.0,
        'disk_gb_used': 100, 'disk_gb_reserved': 10,
        'disk_gb': 500, 'disk_gb_ar': 1.0, 'disk_gb_capacity': 500.0,
    }

    @test.create_mocks({api.nova: ['hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list'],
                        api.placement: ['get_providers']})
    def test_index(self):
        hypervisors = self.hypervisors.list()
        compute_services = [service for service in self.services.list()
                            if service.binary == 'nova-compute']
        self.mock_hypervisor_list.return_value = hypervisors
        self.mock_hypervisor_stats.return_value = self.hypervisors.stats
        self.mock_service_list.return_value = compute_services
        self.mock_get_providers.return_value = [self.TEST_PROVIDER]

        res = self.client.get(reverse('horizon:admin:hypervisors:index'))
        self.assertTemplateUsed(res, 'admin/hypervisors/index.html')

        hypervisors_tab = res.context['tab_group'].get_tab('hypervisor')
        self.assertCountEqual(hypervisors_tab._tables['hypervisors'].data,
                              hypervisors)

        host_tab = res.context['tab_group'].get_tab('compute_host')
        host_table = host_tab._tables['compute_host']
        self.assertCountEqual(host_table.data, compute_services)
        actions_host_up = host_table.get_row_actions(host_table.data[0])
        self.assertEqual(1, len(actions_host_up))
        actions_host_down = host_table.get_row_actions(host_table.data[1])
        self.assertEqual(2, len(actions_host_down))
        self.assertEqual('evacuate', actions_host_down[0].name)

        actions_service_enabled = host_table.get_row_actions(
            host_table.data[1])
        self.assertEqual('evacuate', actions_service_enabled[0].name)
        self.assertEqual('disable', actions_service_enabled[1].name)

        actions_service_disabled = host_table.get_row_actions(
            host_table.data[2])
        self.assertEqual('enable', actions_service_disabled[0].name)
        self.assertEqual('migrate_maintenance',
                         actions_service_disabled[1].name)

        self.mock_hypervisor_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_hypervisor_stats.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_get_providers.assert_called_once_with(
            test.IsHttpRequest())

        self.assertTrue(res.context['show_provider'])
        self.assertContains(res, 'Resource Providers Summary')

    @test.create_mocks({api.nova: ['hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list'],
                        api.placement: ['get_providers']})
    @override_settings(SHOW_RESOURCE_PROVIDER_SUMMARY=False)
    def test_disable_provider_view_summary(self):
        res = self.client.get(reverse('horizon:admin:hypervisors:index'))
        self.assertTemplateUsed(res, 'admin/hypervisors/index.html')
        self.assertFalse(res.context['show_provider'])
        self.assertNotContains(res, 'Resource Providers Summary')
        self.mock_get_providers.assert_not_called()

    @test.create_mocks({api.nova: ['hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list'],
                        api.placement: ['get_providers']})
    def test_service_list_unavailable(self):
        # test that error message should be returned when
        # nova.service_list isn't available.

        self.mock_hypervisor_list.return_value = self.hypervisors.list()
        self.mock_hypervisor_stats.return_value = self.hypervisors.stats
        self.mock_service_list.side_effect = self.exceptions.nova
        self.mock_get_providers.return_value = [self.TEST_PROVIDER]

        resp = self.client.get(reverse('horizon:admin:hypervisors:index'))
        self.assertMessageCount(resp, error=1, warning=0)

        self.mock_hypervisor_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_hypervisor_stats.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')


class HypervisorDetailViewTest(test.BaseAdminViewTests):
    @test.create_mocks({api.nova: ['hypervisor_search']})
    def test_index(self):
        hypervisor = self.hypervisors.first()
        self.mock_hypervisor_search.return_value = [
            hypervisor, self.hypervisors.list()[1]]

        url = reverse('horizon:admin:hypervisors:detail',
                      args=["%s_%s" % (hypervisor.id,
                                       hypervisor.hypervisor_hostname)])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'admin/hypervisors/detail.html')
        self.assertCountEqual(res.context['table'].data, hypervisor.servers)

        self.mock_hypervisor_search.assert_called_once_with(
            test.IsHttpRequest(), hypervisor.hypervisor_hostname)
