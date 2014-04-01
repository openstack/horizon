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

from django.core.urlresolvers import reverse
from django import http
from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:info:index')


class SystemInfoViewTests(test.BaseAdminViewTests):

    @test.create_stubs({api.base: ('is_service_enabled',),
                        api.nova: ('default_quota_get', 'service_list'),
                        api.neutron: ('agent_list', 'is_extension_supported'),
                        api.cinder: ('default_quota_get',)})
    def test_index(self):
        services = self.services.list()
        api.nova.service_list(IsA(http.HttpRequest)).AndReturn(services)
        agents = self.agents.list()
        api.neutron.agent_list(IsA(http.HttpRequest)).AndReturn(agents)

        api.base.is_service_enabled(IsA(http.HttpRequest), IgnoreArg()) \
                .MultipleTimes().AndReturn(True)
        api.nova.default_quota_get(IsA(http.HttpRequest),
                                   IgnoreArg()).AndReturn({})
        api.cinder.default_quota_get(IsA(http.HttpRequest), self.tenant.id)\
            .AndReturn(self.cinder_quotas.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'security-group').AndReturn(True)

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

        network_agents_tab = res.context['tab_group'].get_tab('network_agents')
        self.assertQuerysetEqual(
            network_agents_tab._tables['network_agents'].data,
            [agent.__repr__() for agent in self.agents.list()]
        )

    def test_default_quotas_index(self):
        self._test_default_quotas_index(neutron_enabled=True)

    def test_default_quotas_index_with_neutron_disabled(self):
        self._test_default_quotas_index(neutron_enabled=False)

    def test_default_quotas_index_with_neutron_sg_disabled(self):
        self._test_default_quotas_index(neutron_enabled=True,
                                        neutron_sg_enabled=False)

    @test.create_stubs({api.base: ('is_service_enabled',),
                        api.nova: ('default_quota_get', 'service_list'),
                        api.cinder: ('default_quota_get',)})
    def _test_default_quotas_index(self, neutron_enabled=True,
                                   neutron_sg_enabled=True):
        # Neutron does not have an API for getting default system
        # quotas. When not using Neutron, the floating ips quotas
        # should be in the list.
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
                .MultipleTimes().AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
                .MultipleTimes().AndReturn(neutron_enabled)

        api.nova.service_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.default_quota_get(IsA(http.HttpRequest),
                                   self.tenant.id).AndReturn(self.quotas.nova)
        api.cinder.default_quota_get(IsA(http.HttpRequest), self.tenant.id)\
            .AndReturn(self.cinder_quotas.first())

        if neutron_enabled:
            self.mox.StubOutWithMock(api.neutron, 'agent_list')
            api.neutron.agent_list(IsA(http.HttpRequest)).AndReturn([])

            self.mox.StubOutWithMock(api.neutron, 'is_extension_supported')
            api.neutron.is_extension_supported(IsA(http.HttpRequest),
                            'security-group').AndReturn(neutron_sg_enabled)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        quotas_tab = res.context['tab_group'].get_tab('quotas')
        expected_tabs = ['<Quota: (injected_file_content_bytes, 1)>',
                         '<Quota: (metadata_items, 1)>',
                         '<Quota: (injected_files, 1)>',
                         '<Quota: (gigabytes, 1000)>',
                         '<Quota: (ram, 10000)>',
                         '<Quota: (instances, 10)>',
                         '<Quota: (snapshots, 1)>',
                         '<Quota: (volumes, 1)>',
                         '<Quota: (cores, 10)>',
                         '<Quota: (floating_ips, 1)>',
                         '<Quota: (fixed_ips, 10)>',
                         '<Quota: (security_groups, 10)>',
                         '<Quota: (security_group_rules, 20)>']
        if neutron_enabled:
            expected_tabs.remove('<Quota: (floating_ips, 1)>')
            expected_tabs.remove('<Quota: (fixed_ips, 10)>')
            if neutron_sg_enabled:
                expected_tabs.remove('<Quota: (security_groups, 10)>')
                expected_tabs.remove('<Quota: (security_group_rules, 20)>')

        self.assertQuerysetEqual(quotas_tab._tables['quotas'].data,
                                 expected_tabs,
                                 ordered=False)
