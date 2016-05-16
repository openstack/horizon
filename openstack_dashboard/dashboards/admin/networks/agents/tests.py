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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

NETWORKS_DETAIL_URL = 'horizon:admin:networks:detail'


class NetworkAgentTests(test.BaseAdminViewTests):

    @test.create_stubs({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_agent_add_get(self):
        network = self.networks.first()
        api.neutron.agent_list(IsA(http.HttpRequest), agent_type='DHCP agent')\
            .AndReturn(self.agents.list())
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id)\
            .AndReturn(self.agents.list())
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/agents/add.html')

    @test.create_stubs({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',
                                      'add_network_to_dhcp_agent',)})
    def test_agent_add_post(self):
        network = self.networks.first()
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id)\
            .AndReturn([self.agents.list()[1]])
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.agent_list(IsA(http.HttpRequest), agent_type='DHCP agent')\
            .AndReturn(self.agents.list())
        api.neutron.add_network_to_dhcp_agent(IsA(http.HttpRequest),
                                              agent_id, network.id)\
            .AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'network_name': network.name,
                     'agent': agent_id}
        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[network.id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('agent_list',
                                      'network_get',
                                      'list_dhcp_agent_hosting_networks',
                                      'add_network_to_dhcp_agent',)})
    def test_agent_add_post_exception(self):
        network = self.networks.first()
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network.id)\
            .AndReturn([self.agents.list()[1]])
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.agent_list(IsA(http.HttpRequest), agent_type='DHCP agent')\
            .AndReturn(self.agents.list())
        api.neutron.add_network_to_dhcp_agent(IsA(http.HttpRequest),
                                              agent_id, network.id)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'network_name': network.name,
                     'agent': agent_id}
        url = reverse('horizon:admin:networks:adddhcpagent',
                      args=[network.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[network.id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported',
                                      'remove_network_from_dhcp_agent',)})
    def test_agent_delete(self):
        network_id = self.networks.first().id
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.remove_network_from_dhcp_agent(IsA(http.HttpRequest),
                                                   agent_id, network_id)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(False)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'action': 'agents__delete__%s' % agent_id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('subnet_list',
                                      'port_list',
                                      'list_dhcp_agent_hosting_networks',
                                      'is_extension_supported',
                                      'remove_network_from_dhcp_agent',)})
    def test_agent_delete_exception(self):
        network_id = self.networks.first().id
        agent_id = self.agents.first().id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.remove_network_from_dhcp_agent(IsA(http.HttpRequest),
                                                   agent_id, network_id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(False)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'action': 'agents__delete__%s' % agent_id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)
