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

from django.urls import reverse

import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class HypervisorViewTest(test.BaseAdminViewTests):
    @test.create_mocks({api.nova: ['extension_supported',
                                   'hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list']})
    def test_index(self):
        hypervisors = self.hypervisors.list()
        compute_services = [service for service in self.services.list()
                            if service.binary == 'nova-compute']
        self.mock_extension_supported.return_value = True
        self.mock_hypervisor_list.return_value = hypervisors
        self.mock_hypervisor_stats.return_value = self.hypervisors.stats
        self.mock_service_list.return_value = compute_services

        res = self.client.get(reverse('horizon:admin:hypervisors:index'))
        self.assertTemplateUsed(res, 'admin/hypervisors/index.html')

        hypervisors_tab = res.context['tab_group'].get_tab('hypervisor')
        self.assertItemsEqual(hypervisors_tab._tables['hypervisors'].data,
                              hypervisors)

        host_tab = res.context['tab_group'].get_tab('compute_host')
        host_table = host_tab._tables['compute_host']
        self.assertItemsEqual(host_table.data, compute_services)
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

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_extension_supported, 28,
            mock.call('AdminActions', test.IsHttpRequest()))
        self.mock_hypervisor_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_hypervisor_stats.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')

    @test.create_mocks({api.nova: ['hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list']})
    def test_service_list_unavailable(self):
        # test that error message should be returned when
        # nova.service_list isn't available.

        self.mock_hypervisor_list.return_value = self.hypervisors.list()
        self.mock_hypervisor_stats.return_value = self.hypervisors.stats
        self.mock_service_list.side_effect = self.exceptions.nova

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
        self.assertItemsEqual(res.context['table'].data, hypervisor.servers)

        self.mock_hypervisor_search.assert_called_once_with(
            test.IsHttpRequest(), hypervisor.hypervisor_hostname)
