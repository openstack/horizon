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

import mock

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:info:index')


class SystemInfoViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.base: ['is_service_enabled'],
                        api.nova: [('service_list', 'nova_service_list')],
                        api.neutron: ['agent_list', 'is_extension_supported'],
                        api.cinder: [('service_list', 'cinder_service_list')],
                        })
    def _test_base_index(self):
        self.mock_is_service_enabled.return_value = True
        self.mock_nova_service_list.return_value = self.services.list()

        extensions = {
            'agent': True,
            'availability_zone': False
        }

        def _is_extension_supported(request, ext):
            return extensions[ext]

        self.mock_is_extension_supported.side_effect = _is_extension_supported
        self.mock_agent_list.return_value = self.agents.list()
        self.mock_cinder_service_list.return_value = \
            self.cinder_services.list()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/info/index.html')

        self.mock_is_service_enabled.assert_called_once_with(
            test.IsHttpRequest(), 'network')
        self.mock_nova_service_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_is_extension_supported.assert_has_calls([
            mock.call(test.IsHttpRequest(), 'agent'),
            mock.call(test.IsHttpRequest(), 'availability_zone')])
        self.assertEqual(2, self.mock_is_extension_supported.call_count)
        self.mock_agent_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_cinder_service_list.assert_called_once_with(
            test.IsHttpRequest())

        return res

    def test_index(self):
        res = self._test_base_index()
        services_tab = res.context['tab_group'].get_tab('services')
        self.assertIn("region", services_tab._tables['services'].data[0])
        self.assertIn("endpoints",
                      services_tab._tables['services'].data[0])

    def test_neutron_index(self):
        res = self._test_base_index()
        network_agents_tab = res.context['tab_group'].get_tab('network_agents')
        self.assertQuerysetEqual(
            network_agents_tab._tables['network_agents'].data,
            [agent.__repr__() for agent in self.agents.list()]
        )

    def test_cinder_index(self):
        res = self._test_base_index()
        cinder_services_tab = res.context['tab_group'].\
            get_tab('cinder_services')
        self.assertQuerysetEqual(
            cinder_services_tab._tables['cinder_services'].data,
            [service.__repr__() for service in self.cinder_services.list()]
        )
