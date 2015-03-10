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
                        api.cinder: ('service_list',),
                        api.heat: ('service_list',)})
    def _test_base_index(self):
        api.base.is_service_enabled(IsA(http.HttpRequest), IgnoreArg()) \
                .MultipleTimes().AndReturn(True)

        services = self.services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)

        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'agent').AndReturn(True)
        agents = self.agents.list()
        api.neutron.agent_list(IsA(http.HttpRequest)).AndReturn(agents)

        cinder_services = self.cinder_services.list()
        api.cinder.service_list(IsA(http.HttpRequest)).\
            AndReturn(cinder_services)

        heat_services = self.heat_services.list()
        api.heat.service_list(IsA(http.HttpRequest)).\
            AndReturn(heat_services)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/info/index.html')

        return res

    def test_index(self):
        res = self._test_base_index()
        services_tab = res.context['tab_group'].get_tab('services')
        self.assertQuerysetEqual(
            services_tab._tables['services'].data,
            ['<Service: compute>',
             '<Service: volume>',
             '<Service: volumev2>',
             '<Service: image>',
             '<Service: identity (native backend)>',
             '<Service: object-store>',
             '<Service: network>',
             '<Service: ec2>',
             '<Service: metering>',
             '<Service: orchestration>',
             '<Service: database>',
             '<Service: data-processing>', ])

        self.mox.VerifyAll()

    def test_neutron_index(self):
        res = self._test_base_index()
        network_agents_tab = res.context['tab_group'].get_tab('network_agents')
        self.assertQuerysetEqual(
            network_agents_tab._tables['network_agents'].data,
            [agent.__repr__() for agent in self.agents.list()]
        )

        self.mox.VerifyAll()

    def test_cinder_index(self):
        res = self._test_base_index()
        cinder_services_tab = res.context['tab_group'].\
            get_tab('cinder_services')
        self.assertQuerysetEqual(
            cinder_services_tab._tables['cinder_services'].data,
            [service.__repr__() for service in self.cinder_services.list()]
        )

        self.mox.VerifyAll()

    def test_heat_index(self):
        res = self._test_base_index()
        heat_services_tab = res.context['tab_group'].\
            get_tab('heat_services')
        self.assertQuerysetEqual(
            heat_services_tab._tables['heat_services'].data,
            [service.__repr__() for service in self.heat_services.list()]
        )

        self.mox.VerifyAll()
