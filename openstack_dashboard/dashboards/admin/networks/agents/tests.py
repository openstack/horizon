# Copyright 2012 NEC Corporation
# Copyright 2015 Cisco Systems, Inc.
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

NETWORKS_DETAIL_URL = 'horizon:admin:networks:detail'


class NetworkAgentTests(test.BaseAdminViewTests):

    @test.create_mocks({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_agent_add_get(self):
        network = self.networks.first()
        self.mock_agent_list.return_value = self.agents.list()
        self.mock_network_get.return_value = network
        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()

        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/agents/add.html')

        self.mock_agent_list.assert_called_once_with(test.IsHttpRequest(),
                                                     agent_type='DHCP agent')
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network.id)

    @test.create_mocks({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',
                                      'add_network_to_dhcp_agent',)})
    def test_agent_add_post(self):
        network = self.networks.first()
        agent_id = self.agents.first().id

        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            [self.agents.list()[1]]
        self.mock_network_get.return_value = network
        self.mock_agent_list.return_value = self.agents.list()
        self.mock_add_network_to_dhcp_agent.return_value = True

        form_data = {'network_id': network.id,
                     'network_name': network.name,
                     'agent': agent_id}
        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[network.id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self.mock_agent_list.assert_called_once_with(test.IsHttpRequest(),
                                                     agent_type='DHCP agent')
        self.mock_add_network_to_dhcp_agent.assert_called_once_with(
            test.IsHttpRequest(), agent_id, network.id)

    @test.create_mocks({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',
                                      'add_network_to_dhcp_agent',)})
    def test_agent_add_post_exception(self):
        network = self.networks.first()
        agent_id = self.agents.first().id
        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            [self.agents.list()[1]]
        self.mock_network_get.return_value = network
        self.mock_agent_list.return_value = self.agents.list()
        self.mock_add_network_to_dhcp_agent.side_effect = \
            self.exceptions.neutron

        form_data = {'network_id': network.id,
                     'network_name': network.name,
                     'agent': agent_id}
        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[network.id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network.id)
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network.id)
        self.mock_agent_list.assert_called_once_with(test.IsHttpRequest(),
                                                     agent_type='DHCP agent')
        self.mock_add_network_to_dhcp_agent.assert_called_once_with(
            test.IsHttpRequest(), agent_id, network.id)

    @test.create_mocks({api.neutron: ('list_dhcp_agent_hosting_networks',
                                      'is_extension_supported',
                                      'remove_network_from_dhcp_agent',)})
    def test_agent_delete(self):
        network_id = self.networks.first().id
        agent_id = self.agents.first().id

        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()
        self.mock_remove_network_from_dhcp_agent.return_value = None
        self.mock_is_extension_supported.side_effect = [
            True,   # network-ip-availability
            False,  # mac-learning
            True,   # dhcp_agent_scheduler
        ]

        url = NETWORKS_DETAIL_URL
        form_data = {'action': 'agents__delete__%s' % agent_id}
        url = reverse(url, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network_id)
        self.mock_remove_network_from_dhcp_agent.assert_called_once_with(
            test.IsHttpRequest(), agent_id, network_id)
        self.mock_is_extension_supported.assert_has_calls([
            mock.call(test.IsHttpRequest(), 'network-ip-availability'),
            mock.call(test.IsHttpRequest(), 'mac-learning'),
            mock.call(test.IsHttpRequest(), 'dhcp_agent_scheduler'),
        ])
        self.assertEqual(3, self.mock_is_extension_supported.call_count)

    @test.create_mocks({api.neutron: ('list_dhcp_agent_hosting_networks',
                                      'is_extension_supported',
                                      'remove_network_from_dhcp_agent',)})
    def test_agent_delete_exception(self):
        network_id = self.networks.first().id
        agent_id = self.agents.first().id

        self.mock_list_dhcp_agent_hosting_networks.return_value = \
            self.agents.list()
        self.mock_remove_network_from_dhcp_agent.side_effect = \
            self.exceptions.neutron
        self.mock_is_extension_supported.side_effect = [
            True,   # network-ip-availability
            False,  # mac-learning
            True,   # dhcp_agent_scheduler
        ]

        form_data = {'action': 'agents__delete__%s' % agent_id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_list_dhcp_agent_hosting_networks.assert_called_once_with(
            test.IsHttpRequest(), network_id)
        self.mock_remove_network_from_dhcp_agent.assert_called_once_with(
            test.IsHttpRequest(), agent_id, network_id)
        self.mock_is_extension_supported.assert_has_calls([
            mock.call(test.IsHttpRequest(), 'network-ip-availability'),
            mock.call(test.IsHttpRequest(), 'mac-learning'),
            mock.call(test.IsHttpRequest(), 'dhcp_agent_scheduler'),
        ])
        self.assertEqual(3, self.mock_is_extension_supported.call_count)
