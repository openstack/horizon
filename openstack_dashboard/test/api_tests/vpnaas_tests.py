# Copyright 2013, Mirantis Inc
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

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from neutronclient.v2_0 import client

neutronclient = client.Client


class VPNaasApiTests(test.APITestCase):
    @test.create_stubs({neutronclient: ('create_vpnservice',)})
    def test_vpnservice_create(self):
        vpnservice1 = self.api_vpnservices.first()
        form_data = {
            'name': vpnservice1['name'],
            'description': vpnservice1['description'],
            'subnet_id': vpnservice1['subnet_id'],
            'router_id': vpnservice1['router_id'],
            'admin_state_up': vpnservice1['admin_state_up']
        }

        vpnservice = {'vpnservice': self.api_vpnservices.first()}
        neutronclient.create_vpnservice(
            {'vpnservice': form_data}).AndReturn(vpnservice)
        self.mox.ReplayAll()

        ret_val = api.vpn.vpnservice_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.VPNService)

    @test.create_stubs({neutronclient: ('list_vpnservices',
                                        'list_ipsec_site_connections'),
                        api.neutron: ('subnet_list', 'router_list')})
    def test_vpnservice_list(self):
        vpnservices = {'vpnservices': self.vpnservices.list()}
        vpnservices_dict = {'vpnservices': self.api_vpnservices.list()}
        subnets = self.subnets.list()
        routers = self.routers.list()
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.list_vpnservices().AndReturn(vpnservices_dict)
        api.neutron.subnet_list(self.request).AndReturn(subnets)
        api.neutron.router_list(self.request).AndReturn(routers)
        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.vpnservice_list(self.request)
        for (v, d) in zip(ret_val, vpnservices['vpnservices']):
            self.assertIsInstance(v, api.vpn.VPNService)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_vpnservice',
                                        'list_ipsec_site_connections'),
                        api.neutron: ('subnet_get', 'router_get')})
    def test_vpnservice_get(self):
        vpnservice = self.vpnservices.first()
        vpnservice_dict = {'vpnservice': self.api_vpnservices.first()}
        subnet = self.subnets.first()
        router = self.routers.first()
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.show_vpnservice(
            vpnservice.id).AndReturn(vpnservice_dict)
        api.neutron.subnet_get(self.request, subnet.id).AndReturn(subnet)
        api.neutron.router_get(self.request, router.id).AndReturn(router)
        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.vpnservice_get(self.request, vpnservice.id)
        self.assertIsInstance(ret_val, api.vpn.VPNService)

    @test.create_stubs({neutronclient: ('create_ikepolicy',)})
    def test_ikepolicy_create(self):
        ikepolicy1 = self.api_ikepolicies.first()
        form_data = {
            'name': ikepolicy1['name'],
            'description': ikepolicy1['description'],
            'auth_algorithm': ikepolicy1['auth_algorithm'],
            'encryption_algorithm': ikepolicy1['encryption_algorithm'],
            'ike_version': ikepolicy1['ike_version'],
            'lifetime': ikepolicy1['lifetime'],
            'phase1_negotiation_mode': ikepolicy1['phase1_negotiation_mode'],
            'pfs': ikepolicy1['pfs']
        }

        ikepolicy = {'ikepolicy': self.api_ikepolicies.first()}
        neutronclient.create_ikepolicy(
            {'ikepolicy': form_data}).AndReturn(ikepolicy)
        self.mox.ReplayAll()

        ret_val = api.vpn.ikepolicy_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.IKEPolicy)

    @test.create_stubs({neutronclient: ('list_ikepolicies',
                                        'list_ipsec_site_connections')})
    def test_ikepolicy_list(self):
        ikepolicies = {'ikepolicies': self.ikepolicies.list()}
        ikepolicies_dict = {'ikepolicies': self.api_ikepolicies.list()}
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.list_ikepolicies().AndReturn(ikepolicies_dict)
        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ikepolicy_list(self.request)
        for (v, d) in zip(ret_val, ikepolicies['ikepolicies']):
            self.assertIsInstance(v, api.vpn.IKEPolicy)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_ikepolicy',
                                        'list_ipsec_site_connections')})
    def test_ikepolicy_get(self):
        ikepolicy = self.ikepolicies.first()
        ikepolicy_dict = {'ikepolicy': self.api_ikepolicies.first()}
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.show_ikepolicy(
            ikepolicy.id).AndReturn(ikepolicy_dict)
        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ikepolicy_get(self.request, ikepolicy.id)
        self.assertIsInstance(ret_val, api.vpn.IKEPolicy)

    @test.create_stubs({neutronclient: ('create_ipsecpolicy',)})
    def test_ipsecpolicy_create(self):
        ipsecpolicy1 = self.api_ipsecpolicies.first()
        form_data = {
            'name': ipsecpolicy1['name'],
            'description': ipsecpolicy1['description'],
            'auth_algorithm': ipsecpolicy1['auth_algorithm'],
            'encryption_algorithm': ipsecpolicy1['encryption_algorithm'],
            'encapsulation_mode': ipsecpolicy1['encapsulation_mode'],
            'lifetime': ipsecpolicy1['lifetime'],
            'pfs': ipsecpolicy1['pfs'],
            'transform_protocol': ipsecpolicy1['transform_protocol']
        }

        ipsecpolicy = {'ipsecpolicy': self.api_ipsecpolicies.first()}
        neutronclient.create_ipsecpolicy(
            {'ipsecpolicy': form_data}).AndReturn(ipsecpolicy)
        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecpolicy_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.IPSecPolicy)

    @test.create_stubs({neutronclient: ('list_ipsecpolicies',
                                        'list_ipsec_site_connections')})
    def test_ipsecpolicy_list(self):
        ipsecpolicies = {'ipsecpolicies': self.ipsecpolicies.list()}
        ipsecpolicies_dict = {'ipsecpolicies': self.api_ipsecpolicies.list()}
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.list_ipsecpolicies().AndReturn(ipsecpolicies_dict)
        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecpolicy_list(self.request)
        for (v, d) in zip(ret_val, ipsecpolicies['ipsecpolicies']):
            self.assertIsInstance(v, api.vpn.IPSecPolicy)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_ipsecpolicy',
                                        'list_ipsec_site_connections')})
    def test_ipsecpolicy_get(self):
        ipsecpolicy = self.ipsecpolicies.first()
        ipsecpolicy_dict = {'ipsecpolicy': self.api_ipsecpolicies.first()}
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.show_ipsecpolicy(
            ipsecpolicy.id).AndReturn(ipsecpolicy_dict)
        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecpolicy_get(self.request, ipsecpolicy.id)
        self.assertIsInstance(ret_val, api.vpn.IPSecPolicy)

    @test.create_stubs({neutronclient: ('create_ipsec_site_connection',)})
    def test_ipsecsiteconnection_create(self):
        ipsecsiteconnection1 = self.api_ipsecsiteconnections.first()
        form_data = {
            'name': ipsecsiteconnection1['name'],
            'description': ipsecsiteconnection1['description'],
            'dpd': ipsecsiteconnection1['dpd'],
            'ikepolicy_id': ipsecsiteconnection1['ikepolicy_id'],
            'initiator': ipsecsiteconnection1['initiator'],
            'ipsecpolicy_id': ipsecsiteconnection1['ipsecpolicy_id'],
            'mtu': ipsecsiteconnection1['mtu'],
            'peer_address': ipsecsiteconnection1['peer_address'],
            'peer_cidrs': ipsecsiteconnection1['peer_cidrs'],
            'peer_id': ipsecsiteconnection1['peer_id'],
            'psk': ipsecsiteconnection1['psk'],
            'vpnservice_id': ipsecsiteconnection1['vpnservice_id'],
            'admin_state_up': ipsecsiteconnection1['admin_state_up']
        }

        ipsecsiteconnection = {'ipsec_site_connection':
                               self.api_ipsecsiteconnections.first()}
        neutronclient.create_ipsec_site_connection(
            {'ipsec_site_connection':
             form_data}).AndReturn(ipsecsiteconnection)
        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecsiteconnection_create(
            self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.IPSecSiteConnection)

    @test.create_stubs({neutronclient: ('list_ipsec_site_connections',
                                        'list_ikepolicies',
                                        'list_ipsecpolicies',
                                        'list_vpnservices')})
    def test_ipsecsiteconnection_list(self):
        ipsecsiteconnections = {
            'ipsec_site_connections': self.ipsecsiteconnections.list()}
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}
        ikepolicies_dict = {'ikepolicies': self.api_ikepolicies.list()}
        ipsecpolicies_dict = {'ipsecpolicies': self.api_ipsecpolicies.list()}
        vpnservices_dict = {'vpnservices': self.api_vpnservices.list()}

        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)
        neutronclient.list_ikepolicies().AndReturn(ikepolicies_dict)
        neutronclient.list_ipsecpolicies().AndReturn(ipsecpolicies_dict)
        neutronclient.list_vpnservices().AndReturn(vpnservices_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecsiteconnection_list(self.request)
        for (v, d) in zip(ret_val,
                          ipsecsiteconnections['ipsec_site_connections']):
            self.assertIsInstance(v, api.vpn.IPSecSiteConnection)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_ipsec_site_connection',
                                        'show_ikepolicy', 'show_ipsecpolicy',
                                        'show_vpnservice')})
    def test_ipsecsiteconnection_get(self):
        ipsecsiteconnection = self.ipsecsiteconnections.first()
        connection_dict = {'ipsec_site_connection':
                           self.api_ipsecsiteconnections.first()}
        ikepolicy_dict = {'ikepolicy': self.api_ikepolicies.first()}
        ipsecpolicy_dict = {'ipsecpolicy': self.api_ipsecpolicies.first()}
        vpnservice_dict = {'vpnservice': self.api_vpnservices.first()}

        neutronclient.show_ipsec_site_connection(
            ipsecsiteconnection.id).AndReturn(connection_dict)
        neutronclient.show_ikepolicy(
            ipsecsiteconnection.ikepolicy_id).AndReturn(ikepolicy_dict)
        neutronclient.show_ipsecpolicy(
            ipsecsiteconnection.ipsecpolicy_id).AndReturn(ipsecpolicy_dict)
        neutronclient.show_vpnservice(
            ipsecsiteconnection.vpnservice_id).AndReturn(vpnservice_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecsiteconnection_get(self.request,
                                                  ipsecsiteconnection.id)
        self.assertIsInstance(ret_val, api.vpn.IPSecSiteConnection)
