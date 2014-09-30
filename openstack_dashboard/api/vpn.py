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

from __future__ import absolute_import

from django.utils.datastructures import SortedDict

from horizon.utils.memoized import memoized  # noqa

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


class VPNService(neutron.NeutronAPIDictWrapper):

    """Wrapper for neutron VPNService."""

    def __init__(self, apiresource):
        super(VPNService, self).__init__(apiresource)


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


def vpnservice_list(request, **kwargs):
    return _vpnservice_list(request, expand_subnet=True, expand_router=True,
                            expand_conns=True, **kwargs)


def _vpnservice_list(request, expand_subnet=False, expand_router=False,
                     expand_conns=False, **kwargs):
    vpnservices = neutronclient(request).list_vpnservices(
        **kwargs).get('vpnservices')
    if expand_subnet:
        subnets = neutron.subnet_list(request)
        subnet_dict = SortedDict((s.id, s) for s in subnets)
        for s in vpnservices:
            s['subnet_name'] = subnet_dict.get(s['subnet_id']).cidr
    if expand_router:
        routers = neutron.router_list(request)
        router_dict = SortedDict((r.id, r) for r in routers)
        for s in vpnservices:
            s['router_name'] = router_dict.get(s['router_id']).name_or_id
    if expand_conns:
        ipsecsiteconns = _ipsecsiteconnection_list(request, **kwargs)
        for s in vpnservices:
            s['ipsecsiteconns'] = [c.id for c in ipsecsiteconns
                                   if c.vpnservice_id == s['id']]
    return [VPNService(v) for v in vpnservices]


def vpnservice_get(request, vpnservice_id):
    return _vpnservice_get(request, vpnservice_id, expand_subnet=True,
                           expand_router=True, expand_conns=True)


def _vpnservice_get(request, vpnservice_id, expand_subnet=False,
                    expand_router=False, expand_conns=False):
    vpnservice = neutronclient(request).show_vpnservice(vpnservice_id).get(
        'vpnservice')
    if expand_subnet:
        vpnservice['subnet'] = neutron.subnet_get(
            request, vpnservice['subnet_id'])
    if expand_router:
        vpnservice['router'] = neutron.router_get(
            request, vpnservice['router_id'])
    if expand_conns:
        ipsecsiteconns = _ipsecsiteconnection_list(request)
        vpnservice['ipsecsiteconns'] = [c for c in ipsecsiteconns
                                        if c.vpnservice_id == vpnservice['id']]
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


def ikepolicy_list(request, **kwargs):
    return _ikepolicy_list(request, expand_conns=True, **kwargs)


def _ikepolicy_list(request, expand_conns=False, **kwargs):
    ikepolicies = neutronclient(request).list_ikepolicies(
        **kwargs).get('ikepolicies')
    if expand_conns:
        ipsecsiteconns = _ipsecsiteconnection_list(request, **kwargs)
        for p in ikepolicies:
            p['ipsecsiteconns'] = [c.id for c in ipsecsiteconns
                                   if c.ikepolicy_id == p['id']]
    return [IKEPolicy(v) for v in ikepolicies]


def ikepolicy_get(request, ikepolicy_id):
    return _ikepolicy_get(request, ikepolicy_id, expand_conns=True)


def _ikepolicy_get(request, ikepolicy_id, expand_conns=False):
    ikepolicy = neutronclient(request).show_ikepolicy(
        ikepolicy_id).get('ikepolicy')
    if expand_conns:
        ipsecsiteconns = _ipsecsiteconnection_list(request)
        ikepolicy['ipsecsiteconns'] = [c for c in ipsecsiteconns
                                       if c.ikepolicy_id == ikepolicy['id']]
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


def ipsecpolicy_list(request, **kwargs):
    return _ipsecpolicy_list(request, expand_conns=True, **kwargs)


def _ipsecpolicy_list(request, expand_conns=False, **kwargs):
    ipsecpolicies = neutronclient(request).list_ipsecpolicies(
        **kwargs).get('ipsecpolicies')
    if expand_conns:
        ipsecsiteconns = _ipsecsiteconnection_list(request, **kwargs)
        for p in ipsecpolicies:
            p['ipsecsiteconns'] = [c.id for c in ipsecsiteconns
                                   if c.ipsecpolicy_id == p['id']]
    return [IPSecPolicy(v) for v in ipsecpolicies]


def ipsecpolicy_get(request, ipsecpolicy_id):
    return _ipsecpolicy_get(request, ipsecpolicy_id, expand_conns=True)


def _ipsecpolicy_get(request, ipsecpolicy_id, expand_conns=False):
    ipsecpolicy = neutronclient(request).show_ipsecpolicy(
        ipsecpolicy_id).get('ipsecpolicy')
    if expand_conns:
        ipsecsiteconns = _ipsecsiteconnection_list(request)
        ipsecpolicy['ipsecsiteconns'] = [c for c in ipsecsiteconns
                                         if (c.ipsecpolicy_id ==
                                             ipsecpolicy['id'])]
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


@memoized
def ipsecsiteconnection_list(request, **kwargs):
    return _ipsecsiteconnection_list(request, expand_ikepolicies=True,
                                     expand_ipsecpolicies=True,
                                     expand_vpnservices=True, **kwargs)


@memoized
def _ipsecsiteconnection_list(request, expand_ikepolicies=False,
                              expand_ipsecpolicies=False,
                              expand_vpnservices=False, **kwargs):
    ipsecsiteconnections = neutronclient(request).list_ipsec_site_connections(
        **kwargs).get('ipsec_site_connections')
    if expand_ikepolicies:
        ikepolicies = _ikepolicy_list(request, **kwargs)
        policy_dict = SortedDict((p.id, p) for p in ikepolicies)
        for c in ipsecsiteconnections:
            c['ikepolicy_name'] = policy_dict.get(c['ikepolicy_id']).name_or_id
    if expand_ipsecpolicies:
        ipsecpolicies = _ipsecpolicy_list(request, **kwargs)
        policy_dict = SortedDict((p.id, p) for p in ipsecpolicies)
        for c in ipsecsiteconnections:
            c['ipsecpolicy_name'] = policy_dict.get(c['ipsecpolicy_id']
                                                    ).name_or_id
    if expand_vpnservices:
        vpnservices = _vpnservice_list(request, **kwargs)
        service_dict = SortedDict((s.id, s) for s in vpnservices)
        for c in ipsecsiteconnections:
            c['vpnservice_name'] = service_dict.get(c['vpnservice_id']
                                                    ).name_or_id
    return [IPSecSiteConnection(v) for v in ipsecsiteconnections]


def ipsecsiteconnection_get(request, ipsecsiteconnection_id):
    return _ipsecsiteconnection_get(request, ipsecsiteconnection_id,
                                    expand_ikepolicies=True,
                                    expand_ipsecpolicies=True,
                                    expand_vpnservices=True)


def _ipsecsiteconnection_get(request, ipsecsiteconnection_id,
                             expand_ikepolicies, expand_ipsecpolicies,
                             expand_vpnservices):
    ipsecsiteconnection = neutronclient(request).show_ipsec_site_connection(
        ipsecsiteconnection_id).get('ipsec_site_connection')
    if expand_ikepolicies:
        ipsecsiteconnection['ikepolicy'] = _ikepolicy_get(
            request, ipsecsiteconnection['ikepolicy_id'])
    if expand_ipsecpolicies:
        ipsecsiteconnection['ipsecpolicy'] = _ipsecpolicy_get(
            request, ipsecsiteconnection['ipsecpolicy_id'])
    if expand_vpnservices:
        ipsecsiteconnection['vpnservice'] = _vpnservice_get(
            request, ipsecsiteconnection['vpnservice_id'])
    return IPSecSiteConnection(ipsecsiteconnection)


def ipsecsiteconnection_update(request, ipsecsiteconnection_id, **kwargs):
    ipsecsiteconnection = neutronclient(request).update_ipsec_site_connection(
        ipsecsiteconnection_id, kwargs).get('ipsec_site_connection')
    return IPSecSiteConnection(ipsecsiteconnection)


def ipsecsiteconnection_delete(request, ipsecsiteconnection_id):
    neutronclient(request).delete_ipsec_site_connection(ipsecsiteconnection_id)
