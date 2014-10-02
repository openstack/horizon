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

from django.core.urlresolvers import reverse
from django import http
from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:info:index')


class SystemInfoViewTests(test.BaseAdminViewTests):

    @test.create_stubs({api.base: ('is_service_enabled',),
                        api.nova: ('service_list',),
                        api.neutron: ('agent_list', 'is_extension_supported'),
                        api.cinder: ('service_list',)})
    def test_index(self):
        services = self.services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)
        api.base.is_service_enabled(IsA(http.HttpRequest), IgnoreArg()) \
                .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'agent').AndReturn(True)
        agents = self.agents.list()
        api.neutron.agent_list(IsA(http.HttpRequest)).AndReturn(agents)

        cinder_services = self.cinder_services.list()
        api.cinder.service_list(IsA(http.HttpRequest)).\
            AndReturn(cinder_services)

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
                                  '<Service: database>',
                                  '<Service: data_processing>', ])

        network_agents_tab = res.context['tab_group'].get_tab('network_agents')
        self.assertQuerysetEqual(
            network_agents_tab._tables['network_agents'].data,
            [agent.__repr__() for agent in self.agents.list()]
        )
        self.mox.VerifyAll()

    @test.create_stubs({api.base: ('is_service_enabled',),
                        api.cinder: ('service_list',),
                        api.nova: ('service_list',),
                        api.neutron: ('agent_list', 'is_extension_supported')})
    def test_cinder_services_index(self):
        cinder_services = self.cinder_services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn([])
        api.cinder.service_list(IsA(http.HttpRequest)).\
            AndReturn(cinder_services)
        api.neutron.agent_list(IsA(http.HttpRequest)).AndReturn([])
        api.base.is_service_enabled(IsA(http.HttpRequest), IgnoreArg()) \
                .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'agent').AndReturn(True)

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        cinder_services_tab = res.context['tab_group'].\
            get_tab('cinder_services')

        self.assertTemplateUsed(res, 'admin/info/index.html')
        self.assertQuerysetEqual(cinder_services_tab._tables
                                 ['cinder_services'].data,
                                 ['<Service: cinder-scheduler>',
                                  '<Service: cinder-volume>'])
