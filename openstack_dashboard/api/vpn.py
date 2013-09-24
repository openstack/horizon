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

from __future__ import absolute_import

from openstack_dashboard.api import neutron

neutronclient = neutron.neutronclient


class IKEPolicy(neutron.NeutronAPIDictWrapper):

    """Wrapper for neutron VPN IKEPolicy."""

    def __init__(self, apiresource):
        super(IKEPolicy, self).__init__(apiresource)


class IPSecPolicy(neutron.NeutronAPIDictWrapper):

    """Wrapper for neutron VPN IPSecPolicy."""

    def __init__(self, apiresource):
        super(IPSecPolicy, self).__init__(apiresource)


class IPSecSiteConnection(neutron.NeutronAPIDictWrapper):

    """Wrapper for neutron IPSecSiteConnection."""

    def __init__(self, apiresource):
        super(IPSecSiteConnection, self).__init__(apiresource)

    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    def readable(self, request):
        cFormatted = {'id': self.id,
                      'name': self.name,
                      'description': self.description,
                      'status': self.status,
                      }
        try:
            cFormatted['ikepolicy_id'] = self.ikepolicy_id
            cFormatted['ikepolicy_name'] = ikepolicy_get(
                request, self.ikepolicy_id).name
        except Exception:
            cFormatted['ikepolicy_id'] = self.ikepolicy_id
            cFormatted['ikepolicy_name'] = self.ikepolicy_id

        try:
            cFormatted['ipsecpolicy_id'] = self.ipsecpolicy_id
            cFormatted['ipsecpolicy_name'] = ipsecpolicy_get(
                request, self.ipsecpolicy_id).name
        except Exception:
            cFormatted['ipsecpolicy_id'] = self.ipsecpolicy_id
            cFormatted['ipsecpolicy_name'] = self.ipsecpolicy_id

        try:
            cFormatted['vpnservice_id'] = self.vpnservice_id
            cFormatted['vpnservice_name'] = vpnservice_get(
                request, self.vpnservice_id).name
        except Exception:
            cFormatted['vpnservice_id'] = self.vpnservice_id
            cFormatted['vpnservice_name'] = self.vpnservice_id

        return self.AttributeDict(cFormatted)


class VPNService(neutron.NeutronAPIDictWrapper):

    """Wrapper for neutron VPNService."""

    def __init__(self, apiresource):
        super(VPNService, self).__init__(apiresource)

    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    def readable(self, request):
        sFormatted = {'id': self.id,
                      'name': self.name,
                      'description': self.description,
                      'admin_state_up': self.admin_state_up,
                      'status': self.status,
                      }
        try:
            sFormatted['subnet_id'] = self.subnet_id
            sFormatted['subnet_name'] = neutron.subnet_get(
                request, self.subnet_id).cidr
        except Exception:
            sFormatted['subnet_id'] = self.subnet_id
            sFormatted['subnet_name'] = self.subnet_id

        try:
            sFormatted['router_id'] = self.router_id
            sFormatted['router_name'] = neutron.router_get(
                request, self.router_id).name
        except Exception:
            sFormatted['router_id'] = self.router_id
            sFormatted['router_name'] = self.router_id

        return self.AttributeDict(sFormatted)


def vpnservice_create(request, **kwargs):
    """Create VPNService

    :param request: request context
    :param admin_state_up: admin state (default on)
    :param name: name for VPNService
    :param description: description for VPNService
    :param router_id: router id for router of VPNService
    :param subnet_id: subnet id for subnet of VPNService
    """
    body = {'vpnservice':
                {'admin_state_up': kwargs['admin_state_up'],
                 'name': kwargs['name'],
                 'description': kwargs['description'],
                 'router_id': kwargs['router_id'],
                 'subnet_id': kwargs['subnet_id']}
            }
    vpnservice = neutronclient(request).create_vpnservice(body).get(
        'vpnservice')
    return VPNService(vpnservice)


def vpnservices_get(request, **kwargs):
    vpnservices = neutronclient(request).list_vpnservices().get('vpnservices')
    return [VPNService(v) for v in vpnservices]


def vpnservice_get(request, vpnservice_id):
    vpnservice = neutronclient(request).show_vpnservice(vpnservice_id).get(
        'vpnservice')
    return VPNService(vpnservice)


def vpnservice_update(request, vpnservice_id, **kwargs):
    vpnservice = neutronclient(request).update_vpnservice(
        vpnservice_id, kwargs).get('vpnservice')
    return VPNService(vpnservice)


def vpnservice_delete(request, vpnservice_id):
    neutronclient(request).delete_vpnservice(vpnservice_id)


def ikepolicy_create(request, **kwargs):
    """Create IKEPolicy

    :param request: request context
    :param name: name for IKEPolicy
    :param description: description for IKEPolicy
    :param auth_algorithm: authorization algorithm for IKEPolicy
    :param encryption_algorithm: encryption algorithm for IKEPolicy
    :param ike_version: IKE version for IKEPolicy
    :param lifetime: Lifetime Units and Value for IKEPolicy
    :param pfs: Perfect Forward Secrecy for IKEPolicy
    :param phase1_negotiation_mode: IKE Phase1 negotiation mode for IKEPolicy
    """
    body = {'ikepolicy':
                {'name': kwargs['name'],
                 'description': kwargs['description'],
                 'auth_algorithm': kwargs['auth_algorithm'],
                 'encryption_algorithm': kwargs['encryption_algorithm'],
                 'ike_version': kwargs['ike_version'],
                 'lifetime': kwargs['lifetime'],
                 'pfs': kwargs['pfs'],
                 'phase1_negotiation_mode': kwargs['phase1_negotiation_mode']}
            }
    ikepolicy = neutronclient(request).create_ikepolicy(body).get(
        'ikepolicy')
    return IKEPolicy(ikepolicy)


def ikepolicies_get(request, **kwargs):
    ikepolicies = neutronclient(request).list_ikepolicies().get('ikepolicies')
    return [IKEPolicy(v) for v in ikepolicies]


def ikepolicy_get(request, ikepolicy_id):
    ikepolicy = neutronclient(request).show_ikepolicy(
        ikepolicy_id).get('ikepolicy')
    return IKEPolicy(ikepolicy)


def ikepolicy_update(request, ikepolicy_id, **kwargs):
    ikepolicy = neutronclient(request).update_ikepolicy(
        ikepolicy_id, kwargs).get('ikepolicy')
    return IKEPolicy(ikepolicy)


def ikepolicy_delete(request, ikepolicy_id):
    neutronclient(request).delete_ikepolicy(ikepolicy_id)


def ipsecpolicy_create(request, **kwargs):
    """Create IPSecPolicy

    :param request: request context
    :param name: name for IPSecPolicy
    :param description: description for IPSecPolicy
    :param auth_algorithm: authorization algorithm for IPSecPolicy
    :param encapsulation_mode: encapsulation mode for IPSecPolicy
    :param encryption_algorithm: encryption algorithm for IPSecPolicy
    :param lifetime: Lifetime Units and Value for IPSecPolicy
    :param pfs: Perfect Forward Secrecy for IPSecPolicy
    :param transform_protocol: Transform Protocol for IPSecPolicy
    """
    body = {'ipsecpolicy':
                {'name': kwargs['name'],
                 'description': kwargs['description'],
                 'auth_algorithm': kwargs['auth_algorithm'],
                 'encapsulation_mode': kwargs['encapsulation_mode'],
                 'encryption_algorithm': kwargs['encryption_algorithm'],
                 'lifetime': kwargs['lifetime'],
                 'pfs': kwargs['pfs'],
                 'transform_protocol': kwargs['transform_protocol']}
            }
    ipsecpolicy = neutronclient(request).create_ipsecpolicy(body).get(
        'ipsecpolicy')
    return IPSecPolicy(ipsecpolicy)


def ipsecpolicies_get(request, **kwargs):
    ipsecpolicies = neutronclient(request).list_ipsecpolicies().get(
        'ipsecpolicies')
    return [IPSecPolicy(v) for v in ipsecpolicies]


def ipsecpolicy_get(request, ipsecpolicy_id):
    ipsecpolicy = neutronclient(request).show_ipsecpolicy(
        ipsecpolicy_id).get('ipsecpolicy')
    return IPSecPolicy(ipsecpolicy)


def ipsecpolicy_update(request, ipsecpolicy_id, **kwargs):
    ipsecpolicy = neutronclient(request).update_ipsecpolicy(
        ipsecpolicy_id, kwargs).get('ipsecpolicy')
    return IPSecPolicy(ipsecpolicy)


def ipsecpolicy_delete(request, ipsecpolicy_id):
    neutronclient(request).delete_ipsecpolicy(ipsecpolicy_id)


def ipsecsiteconnection_create(request, **kwargs):
    """Create IPSecSiteConnection

    :param request: request context
    :param name: name for IPSecSiteConnection
    :param description: description for IPSecSiteConnection
    :param dpd: dead peer detection action, interval and timeout
    :param ikepolicy_id: IKEPolicy associated with this connection
    :param initiator: initiator state
    :param ipsecpolicy_id: IPsecPolicy associated with this connection
    :param mtu: MTU size for the connection
    :param peer_address: Peer gateway public address
    :param peer_cidrs: remote subnet(s) in CIDR format
    :param peer_id:  Peer router identity for authentication"
    :param psk: Pre-Shared Key string
    :param vpnservice_id: VPNService associated with this connection
    :param admin_state_up: admin state (default on)
    """
    body = {'ipsec_site_connection':
                {'name': kwargs['name'],
                 'description': kwargs['description'],
                 'dpd': kwargs['dpd'],
                 'ikepolicy_id': kwargs['ikepolicy_id'],
                 'initiator': kwargs['initiator'],
                 'ipsecpolicy_id': kwargs['ipsecpolicy_id'],
                 'mtu': kwargs['mtu'],
                 'peer_address': kwargs['peer_address'],
                 'peer_cidrs': kwargs['peer_cidrs'],
                 'peer_id': kwargs['peer_id'],
                 'psk': kwargs['psk'],
                 'vpnservice_id': kwargs['vpnservice_id'],
                 'admin_state_up': kwargs['admin_state_up']}
            }
    ipsecsiteconnection = neutronclient(request).create_ipsec_site_connection(
        body).get('ipsec_site_connection')
    return IPSecSiteConnection(ipsecsiteconnection)


def ipsecsiteconnections_get(request, **kwargs):
    ipsecsiteconnections = neutronclient(
        request).list_ipsec_site_connections().get('ipsec_site_connections')
    return [IPSecSiteConnection(v) for v in ipsecsiteconnections]


def ipsecsiteconnection_get(request, ipsecsiteconnection_id):
    ipsecsiteconnection = neutronclient(request).show_ipsec_site_connection(
        ipsecsiteconnection_id).get('ipsec_site_connection')
    return IPSecSiteConnection(ipsecsiteconnection)


def ipsecsiteconnection_update(request, ipsecsiteconnection_id, **kwargs):
    ipsecsiteconnection = neutronclient(request).update_ipsec_site_connection(
        ipsecsiteconnection_id, kwargs).get('ipsec_site_connection')
    return IPSecSiteConnection(ipsecsiteconnection)


def ipsecsiteconnection_delete(request, ipsecsiteconnection_id):
    neutronclient(request).delete_ipsec_site_connection(ipsecsiteconnection_id)
