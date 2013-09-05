# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
#
# @author: Tatiana Mazur

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

    @test.create_stubs({neutronclient: ('list_vpnservices',)})
    def test_vpnservices_get(self):
        vpnservices = {'vpnservices': self.vpnservices.list()}
        vpnservices_dict = {'vpnservices': self.api_vpnservices.list()}

        neutronclient.list_vpnservices().AndReturn(vpnservices_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.vpnservices_get(self.request)
        for (v, d) in zip(ret_val, vpnservices['vpnservices']):
            self.assertIsInstance(v, api.vpn.VPNService)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_vpnservice',)})
    def test_vpnservice_get(self):
        vpnservice1 = self.api_vpnservices.first()
        vpnservice = {'vpnservice': vpnservice1}

        neutronclient.show_vpnservice(
            vpnservice['vpnservice']['id']).AndReturn(vpnservice)

        self.mox.ReplayAll()

        ret_val = api.vpn.vpnservice_get(self.request,
                                         vpnservice['vpnservice']['id'])
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

    @test.create_stubs({neutronclient: ('list_ikepolicies',)})
    def test_ikepolicies_get(self):
        ikepolicies = {'ikepolicies': self.ikepolicies.list()}
        ikepolicies_dict = {'ikepolicies': self.api_ikepolicies.list()}

        neutronclient.list_ikepolicies().AndReturn(ikepolicies_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ikepolicies_get(self.request)
        for (v, d) in zip(ret_val, ikepolicies['ikepolicies']):
            self.assertIsInstance(v, api.vpn.IKEPolicy)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_ikepolicy',)})
    def test_ikepolicy_get(self):
        ikepolicy1 = self.api_ikepolicies.first()
        ikepolicy = {'ikepolicy': ikepolicy1}

        neutronclient.show_ikepolicy(
            ikepolicy['ikepolicy']['id']).AndReturn(ikepolicy)

        self.mox.ReplayAll()

        ret_val = api.vpn.ikepolicy_get(self.request,
                                        ikepolicy['ikepolicy']['id'])
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

    @test.create_stubs({neutronclient: ('list_ipsecpolicies',)})
    def test_ipsecpolicies_get(self):
        ipsecpolicies = {'ipsecpolicies': self.ipsecpolicies.list()}
        ipsecpolicies_dict = {'ipsecpolicies': self.api_ipsecpolicies.list()}

        neutronclient.list_ipsecpolicies().AndReturn(ipsecpolicies_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecpolicies_get(self.request)
        for (v, d) in zip(ret_val, ipsecpolicies['ipsecpolicies']):
            self.assertIsInstance(v, api.vpn.IPSecPolicy)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_ipsecpolicy',)})
    def test_ipsecpolicy_get(self):
        ipsecpolicy1 = self.api_ipsecpolicies.first()
        ipsecpolicy = {'ipsecpolicy': ipsecpolicy1}

        neutronclient.show_ipsecpolicy(
            ipsecpolicy['ipsecpolicy']['id']).AndReturn(ipsecpolicy)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecpolicy_get(self.request,
                                          ipsecpolicy['ipsecpolicy']['id'])
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

    @test.create_stubs({neutronclient: ('list_ipsec_site_connections',)})
    def test_ipsecsiteconnections_get(self):
        ipsecsiteconnections = {
            'ipsec_site_connections': self.ipsecsiteconnections.list()}
        ipsecsiteconnections_dict = {
            'ipsec_site_connections': self.api_ipsecsiteconnections.list()}

        neutronclient.list_ipsec_site_connections().AndReturn(
            ipsecsiteconnections_dict)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecsiteconnections_get(self.request)
        for (v, d) in zip(ret_val,
                          ipsecsiteconnections['ipsec_site_connections']):
            self.assertIsInstance(v, api.vpn.IPSecSiteConnection)
            self.assertTrue(v.name, d.name)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_ipsec_site_connection',)})
    def test_ipsecsiteconnection_get(self):
        ipsecsiteconnection1 = self.api_ipsecsiteconnections.first()
        ipsecsiteconnection = {'ipsec_site_connection': ipsecsiteconnection1}

        neutronclient.show_ipsec_site_connection(
            ipsecsiteconnection['ipsec_site_connection']['id']).AndReturn(
                ipsecsiteconnection)

        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecsiteconnection_get(self.request,
            ipsecsiteconnection['ipsec_site_connection']['id'])
        self.assertIsInstance(ret_val, api.vpn.IPSecSiteConnection)
