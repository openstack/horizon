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

from django.core.urlresolvers import reverse
from django import http
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class HypervisorViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('extension_supported',
                                   'hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list')})
    def test_index(self):
        hypervisors = self.hypervisors.list()
        services = self.services.list()
        stats = self.hypervisors.stats
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.hypervisor_list(IsA(http.HttpRequest)).AndReturn(hypervisors)
        api.nova.hypervisor_stats(IsA(http.HttpRequest)).AndReturn(stats)
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:hypervisors:index'))
        self.assertTemplateUsed(res, 'admin/hypervisors/index.html')

        hypervisors_tab = res.context['tab_group'].get_tab('hypervisor')
        self.assertItemsEqual(hypervisors_tab._tables['hypervisors'].data,
                              hypervisors)

        host_tab = res.context['tab_group'].get_tab('compute_host')
        host_table = host_tab._tables['compute_host']
        compute_services = [service for service in services
                            if service.binary == 'nova-compute']
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

    @test.create_stubs({api.nova: ('hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list')})
    def test_service_list_unavailable(self):
        """test that error message should be returned when
        nova.service_list isn't available
        """
        hypervisors = self.hypervisors.list()
        stats = self.hypervisors.stats
        api.nova.hypervisor_list(IsA(http.HttpRequest)).AndReturn(hypervisors)
        api.nova.hypervisor_stats(IsA(http.HttpRequest)).AndReturn(stats)
        api.nova.service_list(IsA(http.HttpRequest)).AndRaise(
            self.exceptions.nova)
        self.mox.ReplayAll()

        resp = self.client.get(reverse('horizon:admin:hypervisors:index'))
        self.assertMessageCount(resp, error=1, warning=0)


class HypervisorDetailViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('hypervisor_search',)})
    def test_index(self):
        hypervisor = self.hypervisors.first()
        api.nova.hypervisor_search(
            IsA(http.HttpRequest),
            hypervisor.hypervisor_hostname).AndReturn([
                hypervisor,
                self.hypervisors.list()[1]])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:hypervisors:detail',
                      args=["%s_%s" % (hypervisor.id,
                                       hypervisor.hypervisor_hostname)])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'admin/hypervisors/detail.html')
        self.assertItemsEqual(res.context['table'].data, hypervisor.servers)
