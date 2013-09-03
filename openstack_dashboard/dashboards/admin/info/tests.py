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

    @test.create_stubs({api.nova: ('service_list',
                                   'availability_zone_list',
                                   'aggregate_list'),
                        api.neutron: ('agent_list',)})
    def test_index(self):
        services = self.services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)
        api.nova.availability_zone_list(IsA(http.HttpRequest), detailed=True) \
            .AndReturn(self.availability_zones.list())
        api.nova.aggregate_list(IsA(http.HttpRequest)) \
            .AndReturn(self.aggregates.list())
        agents = self.agents.list()
        api.neutron.agent_list(IsA(http.HttpRequest)).AndReturn(agents)

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
                                  '<Service: orchestration>',
                                  '<Service: database>'])

        zones_tab = res.context['tab_group'].get_tab('zones')
        self.assertQuerysetEqual(zones_tab._tables['zones'].data,
                                 ['<AvailabilityZone: nova>'])

        aggregates_tab = res.context['tab_group'].get_tab('aggregates')
        self.assertQuerysetEqual(aggregates_tab._tables['aggregates'].data,
                                 ['<Aggregate: 1>', '<Aggregate: 2>'])

        network_agents_tab = res.context['tab_group'].get_tab('network_agents')
        self.assertQuerysetEqual(
            network_agents_tab._tables['network_agents'].data,
            [agent.__repr__() for agent in self.agents.list()]
        )
