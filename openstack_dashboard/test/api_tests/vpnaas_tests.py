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
                        'admin_state_up': vpnservice1['admin_state_up']}

        vpnservice = {'vpnservice': self.api_vpnservices.first()}
        neutronclient.create_vpnservice(
            {'vpnservice': form_data}).AndReturn(vpnservice)
        self.mox.ReplayAll()

        ret_val = api.vpn.vpnservice_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.VPNService)

    @test.create_stubs({neutronclient: ('create_ikepolicy',)})
    def test_ikepolicy_create(self):
        ikepolicy1 = self.api_ikepolicies.first()
        form_data = {
                        'name': ikepolicy1['name'],
                        'description': ikepolicy1['description'],
                        'auth_algorithm': ikepolicy1['auth_algorithm'],
                        'encryption_algorithm': ikepolicy1[
                            'encryption_algorithm'],
                        'ike_version': ikepolicy1['ike_version'],
                        'lifetime': ikepolicy1['lifetime'],
                        'phase1_negotiation_mode': ikepolicy1[
                            'phase1_negotiation_mode'],
                        'pfs': ikepolicy1['pfs']}

        ikepolicy = {'ikepolicy': self.api_ikepolicies.first()}
        neutronclient.create_ikepolicy(
            {'ikepolicy': form_data}).AndReturn(ikepolicy)
        self.mox.ReplayAll()

        ret_val = api.vpn.ikepolicy_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.IKEPolicy)

    @test.create_stubs({neutronclient: ('create_ipsecpolicy',)})
    def test_ipsecpolicy_create(self):
        ipsecpolicy1 = self.api_ipsecpolicies.first()
        form_data = {
                        'name': ipsecpolicy1['name'],
                        'description': ipsecpolicy1['description'],
                        'auth_algorithm': ipsecpolicy1['auth_algorithm'],
                        'encryption_algorithm': ipsecpolicy1[
                            'encryption_algorithm'],
                        'encapsulation_mode': ipsecpolicy1[
                            'encapsulation_mode'],
                        'lifetime': ipsecpolicy1['lifetime'],
                        'pfs': ipsecpolicy1['pfs'],
                        'transform_protocol': ipsecpolicy1[
                            'transform_protocol']}

        ipsecpolicy = {'ipsecpolicy': self.api_ipsecpolicies.first()}
        neutronclient.create_ipsecpolicy(
            {'ipsecpolicy': form_data}).AndReturn(ipsecpolicy)
        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecpolicy_create(self.request, **form_data)
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
                        'ipsecpolicy_id': ipsecsiteconnection1[
                            'ipsecpolicy_id'],
                        'mtu': ipsecsiteconnection1['mtu'],
                        'peer_address': ipsecsiteconnection1['peer_address'],
                        'peer_cidrs': ipsecsiteconnection1['peer_cidrs'],
                        'peer_id': ipsecsiteconnection1['peer_id'],
                        'psk': ipsecsiteconnection1['psk'],
                        'vpnservice_id': ipsecsiteconnection1['vpnservice_id'],
                        'admin_state_up': ipsecsiteconnection1[
                            'admin_state_up']}

        ipsecsiteconnection = {'ipsec_site_connection':
                               self.api_ipsecsiteconnections.first()}
        neutronclient.create_ipsec_site_connection(
            {'ipsec_site_connection':
             form_data}).AndReturn(ipsecsiteconnection)
        self.mox.ReplayAll()

        ret_val = api.vpn.ipsecsiteconnection_create(
            self.request, **form_data)
        self.assertIsInstance(ret_val, api.vpn.IPSecSiteConnection)
