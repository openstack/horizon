# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Cisco Systems, Inc.
# Copyright 2012 NEC Corporation
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

import collections
import logging
import netaddr

from django.conf import settings
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base
from openstack_dashboard.api import network_base
from openstack_dashboard.api import nova

from neutronclient.v2_0 import client as neutron_client

LOG = logging.getLogger(__name__)

IP_VERSION_DICT = {4: 'IPv4', 6: 'IPv6'}


class NeutronAPIDictWrapper(base.APIDictWrapper):

    def set_id_as_name_if_empty(self, length=8):
        try:
            if not self._apidict['name']:
                id = self._apidict['id']
                if length:
                    id = id[:length]
                self._apidict['name'] = '(%s)' % id
        except KeyError:
            pass

    def items(self):
        return self._apidict.items()

    @property
    def name_or_id(self):
        return (self._apidict.get('name') or
                '(%s)' % self._apidict['id'][:13])


class Agent(NeutronAPIDictWrapper):
    """Wrapper for neutron agents."""

    def __init__(self, apiresource):
        apiresource['admin_state'] = \
            'UP' if apiresource['admin_state_up'] else 'DOWN'
        super(Agent, self).__init__(apiresource)


class Network(NeutronAPIDictWrapper):
    """Wrapper for neutron Networks."""

    def __init__(self, apiresource):
        apiresource['admin_state'] = \
            'UP' if apiresource['admin_state_up'] else 'DOWN'
        # Django cannot handle a key name with a colon, so remap another key
        for key in apiresource.keys():
            if key.find(':'):
                apiresource['__'.join(key.split(':'))] = apiresource[key]
        super(Network, self).__init__(apiresource)


class Subnet(NeutronAPIDictWrapper):
    """Wrapper for neutron subnets."""

    def __init__(self, apiresource):
        apiresource['ipver_str'] = get_ipver_str(apiresource['ip_version'])
        super(Subnet, self).__init__(apiresource)


class Port(NeutronAPIDictWrapper):
    """Wrapper for neutron ports."""

    def __init__(self, apiresource):
        apiresource['admin_state'] = \
            'UP' if apiresource['admin_state_up'] else 'DOWN'
        super(Port, self).__init__(apiresource)


class Profile(NeutronAPIDictWrapper):
    """Wrapper for neutron profiles."""
    _attrs = ['profile_id', 'name', 'segment_type', 'segment_range',
              'sub_type', 'multicast_ip_index', 'multicast_ip_range']

    def __init__(self, apiresource):
        super(Profile, self).__init__(apiresource)


class Router(NeutronAPIDictWrapper):
    """Wrapper for neutron routers."""

    def __init__(self, apiresource):
        #apiresource['admin_state'] = \
        #    'UP' if apiresource['admin_state_up'] else 'DOWN'
        super(Router, self).__init__(apiresource)


class SecurityGroup(NeutronAPIDictWrapper):
    # Required attributes: id, name, description, tenant_id, rules

    def __init__(self, sg, sg_dict=None):
        if sg_dict is None:
            sg_dict = {sg['id']: sg['name']}
        sg['rules'] = [SecurityGroupRule(rule, sg_dict)
                       for rule in sg['security_group_rules']]
        super(SecurityGroup, self).__init__(sg)


class SecurityGroupRule(NeutronAPIDictWrapper):
    # Required attributes:
    #   id, parent_group_id
    #   ip_protocol, from_port, to_port, ip_range, group
    #   ethertype, direction (Neutron specific)

    def _get_secgroup_name(self, sg_id, sg_dict):
        if sg_id:
            if sg_dict is None:
                sg_dict = {}
            # If sg name not found in sg_dict,
            # first two parts of UUID is used as sg name.
            return sg_dict.get(sg_id, sg_id[:13])
        else:
            return u''

    def __init__(self, sgr, sg_dict=None):
        # In Neutron, if both remote_ip_prefix and remote_group_id are None,
        # it means all remote IP range is allowed, i.e., 0.0.0.0/0 or ::/0.
        if not sgr['remote_ip_prefix'] and not sgr['remote_group_id']:
            if sgr['ethertype'] == 'IPv6':
                sgr['remote_ip_prefix'] = '::/0'
            else:
                sgr['remote_ip_prefix'] = '0.0.0.0/0'

        rule = {
            'id': sgr['id'],
            'parent_group_id': sgr['security_group_id'],
            'direction': sgr['direction'],
            'ethertype': sgr['ethertype'],
            'ip_protocol': sgr['protocol'],
            'from_port': sgr['port_range_min'],
            'to_port': sgr['port_range_max'],
        }
        cidr = sgr['remote_ip_prefix']
        rule['ip_range'] = {'cidr': cidr} if cidr else {}
        group = self._get_secgroup_name(sgr['remote_group_id'], sg_dict)
        rule['group'] = {'name': group} if group else {}
        super(SecurityGroupRule, self).__init__(rule)

    def __unicode__(self):
        if 'name' in self.group:
            remote = self.group['name']
        elif 'cidr' in self.ip_range:
            remote = self.ip_range['cidr']
        else:
            remote = 'ANY'
        direction = 'to' if self.direction == 'egress' else 'from'
        if self.from_port:
            if self.from_port == self.to_port:
                proto_port = ("%s/%s" %
                              (self.from_port, self.ip_protocol.lower()))
            else:
                proto_port = ("%s-%s/%s" %
                              (self.from_port, self.to_port,
                               self.ip_protocol.lower()))
        elif self.ip_protocol:
            try:
                ip_proto = int(self.ip_protocol)
                proto_port = "ip_proto=%d" % ip_proto
            except Exception:
                # well-defined IP protocol name like TCP, UDP, ICMP.
                proto_port = self.ip_protocol
        else:
            proto_port = ''

        return (_('ALLOW %(ethertype)s %(proto_port)s '
                  '%(direction)s %(remote)s') %
                {'ethertype': self.ethertype,
                 'proto_port': proto_port,
                 'remote': remote,
                 'direction': direction})


class SecurityGroupManager(network_base.SecurityGroupManager):
    backend = 'neutron'

    def __init__(self, request):
        self.request = request
        self.client = neutronclient(request)

    def _list(self, **filters):
        secgroups = self.client.list_security_groups(**filters)
        return [SecurityGroup(sg) for sg in secgroups.get('security_groups')]

    def list(self):
        tenant_id = self.request.user.tenant_id
        return self._list(tenant_id=tenant_id)

    def _sg_name_dict(self, sg_id, rules):
        """Create a mapping dict from secgroup id to its name."""
        related_ids = set([sg_id])
        related_ids |= set(filter(None, [r['remote_group_id'] for r in rules]))
        related_sgs = self.client.list_security_groups(id=related_ids,
                                                       fields=['id', 'name'])
        related_sgs = related_sgs.get('security_groups')
        return dict((sg['id'], sg['name']) for sg in related_sgs)

    def get(self, sg_id):
        secgroup = self.client.show_security_group(sg_id).get('security_group')
        sg_dict = self._sg_name_dict(sg_id, secgroup['security_group_rules'])
        return SecurityGroup(secgroup, sg_dict)

    def create(self, name, desc):
        body = {'security_group': {'name': name,
                                   'description': desc}}
        secgroup = self.client.create_security_group(body)
        return SecurityGroup(secgroup.get('security_group'))

    def update(self, sg_id, name, desc):
        body = {'security_group': {'name': name,
                                   'description': desc}}
        secgroup = self.client.update_security_group(sg_id, body)
        return SecurityGroup(secgroup.get('security_group'))

    def delete(self, sg_id):
        self.client.delete_security_group(sg_id)

    def rule_create(self, parent_group_id,
                    direction=None, ethertype=None,
                    ip_protocol=None, from_port=None, to_port=None,
                    cidr=None, group_id=None):
        if not cidr:
            cidr = None
        if from_port < 0:
            from_port = None
        if to_port < 0:
            to_port = None
        if isinstance(ip_protocol, int) and ip_protocol < 0:
            ip_protocol = None

        body = {'security_group_rule':
                    {'security_group_id': parent_group_id,
                     'direction': direction,
                     'ethertype': ethertype,
                     'protocol': ip_protocol,
                     'port_range_min': from_port,
                     'port_range_max': to_port,
                     'remote_ip_prefix': cidr,
                     'remote_group_id': group_id}}
        rule = self.client.create_security_group_rule(body)
        rule = rule.get('security_group_rule')
        sg_dict = self._sg_name_dict(parent_group_id, [rule])
        return SecurityGroupRule(rule, sg_dict)

    def rule_delete(self, sgr_id):
        self.client.delete_security_group_rule(sgr_id)

    def list_by_instance(self, instance_id):
        """Gets security groups of an instance."""
        ports = port_list(self.request, device_id=instance_id)
        sg_ids = []
        for p in ports:
            sg_ids += p.security_groups
        return self._list(id=set(sg_ids)) if sg_ids else []

    def update_instance_security_group(self, instance_id,
                                       new_security_group_ids):
        ports = port_list(self.request, device_id=instance_id)
        for p in ports:
            params = {'security_groups': new_security_group_ids}
            port_update(self.request, p.id, **params)


class FloatingIp(base.APIDictWrapper):
    _attrs = ['id', 'ip', 'fixed_ip', 'port_id', 'instance_id', 'pool']

    def __init__(self, fip):
        fip['ip'] = fip['floating_ip_address']
        fip['fixed_ip'] = fip['fixed_ip_address']
        fip['pool'] = fip['floating_network_id']
        super(FloatingIp, self).__init__(fip)


class FloatingIpPool(base.APIDictWrapper):
    pass


class FloatingIpTarget(base.APIDictWrapper):
    pass


class FloatingIpManager(network_base.FloatingIpManager):
    def __init__(self, request):
        self.request = request
        self.client = neutronclient(request)

    def list_pools(self):
        search_opts = {'router:external': True}
        return [FloatingIpPool(pool) for pool
                in self.client.list_networks(**search_opts).get('networks')]

    def list(self, **search_opts):
        tenant_id = self.request.user.tenant_id
        # In Neutron, list_floatingips returns Floating IPs from all tenants
        # when the API is called with admin role, so we need to filter them
        # with tenant_id.
        fips = self.client.list_floatingips(tenant_id=tenant_id, **search_opts)
        fips = fips.get('floatingips')
        # Get port list to add instance_id to floating IP list
        # instance_id is stored in device_id attribute
        ports = port_list(self.request, tenant_id=tenant_id)
        device_id_dict = SortedDict([(p['id'], p['device_id']) for p in ports])
        for fip in fips:
            if fip['port_id']:
                fip['instance_id'] = device_id_dict[fip['port_id']]
            else:
                fip['instance_id'] = None
        return [FloatingIp(fip) for fip in fips]

    def get(self, floating_ip_id):
        fip = self.client.show_floatingip(floating_ip_id).get('floatingip')
        if fip['port_id']:
            fip['instance_id'] = port_get(self.request,
                                          fip['port_id']).device_id
        else:
            fip['instance_id'] = None
        return FloatingIp(fip)

    def allocate(self, pool):
        body = {'floatingip': {'floating_network_id': pool}}
        fip = self.client.create_floatingip(body).get('floatingip')
        fip['instance_id'] = None
        return FloatingIp(fip)

    def release(self, floating_ip_id):
        self.client.delete_floatingip(floating_ip_id)

    def associate(self, floating_ip_id, port_id):
        # NOTE: In Neutron Horizon floating IP support, port_id is
        # "<port_id>_<ip_address>" format to identify multiple ports.
        pid, ip_address = port_id.split('_', 1)
        update_dict = {'port_id': pid,
                       'fixed_ip_address': ip_address}
        self.client.update_floatingip(floating_ip_id,
                                      {'floatingip': update_dict})

    def disassociate(self, floating_ip_id, port_id):
        update_dict = {'port_id': None}
        self.client.update_floatingip(floating_ip_id,
                                      {'floatingip': update_dict})

    def list_targets(self):
        tenant_id = self.request.user.tenant_id
        ports = port_list(self.request, tenant_id=tenant_id)
        servers, has_more = nova.server_list(self.request)
        server_dict = SortedDict([(s.id, s.name) for s in servers])

        nc = neutronclient(self.request)
        pool_dict = {p['id']: p['name'] for p in nc.list_pools()['pools']}
        vip_dict = {v['port_id']: pool_dict[v['pool_id']] for v in nc.list_vips()['vips']}

        targets = []
        for p in ports:
            # Remove network ports from Floating IP targets
            if p.device_owner.startswith('network:'):
                continue
            port_id = p.id
            server_name = server_dict.get(p.device_id)

            if server_name is None:
                server_name = vip_dict.get(port_id, None)

            for ip in p.fixed_ips:
                target = {'name': '%s: %s' % (server_name, ip['ip_address']),
                          'id': '%s_%s' % (port_id, ip['ip_address'])}
                targets.append(FloatingIpTarget(target))
        return targets

    def _target_ports_by_instance(self, instance_id):
        if not instance_id:
            return None
        search_opts = {'device_id': instance_id}
        return port_list(self.request, **search_opts)

    def get_target_id_by_instance(self, instance_id):
        # In Neutron one port can have multiple ip addresses, so this method
        # picks up the first one and generate target id.
        ports = self._target_ports_by_instance(instance_id)
        if not ports:
            return None
        return '{0}_{1}'.format(ports[0].id,
                                ports[0].fixed_ips[0]['ip_address'])

    def list_target_id_by_instance(self, instance_id):
        ports = self._target_ports_by_instance(instance_id)
        return ['{0}_{1}'.format(p.id, p.fixed_ips[0]['ip_address'])
                for p in ports]

    def is_simple_associate_supported(self):
        # NOTE: There are two reason that simple association support
        # needs more considerations. (1) Neutron does not support the
        # default floating IP pool at the moment. It can be avoided
        # in case where only one floating IP pool exists.
        # (2) Neutron floating IP is associated with each VIF and
        # we need to check whether such VIF is only one for an instance
        # to enable simple association support.
        return False


def get_ipver_str(ip_version):
    """Convert an ip version number to a human-friendly string."""
    return IP_VERSION_DICT.get(ip_version, '')


def neutronclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    LOG.debug('neutronclient connection created using token "%s" and url "%s"'
              % (request.user.token.id, base.url_for(request, 'network')))
    LOG.debug('user_id=%(user)s, tenant_id=%(tenant)s' %
              {'user': request.user.id, 'tenant': request.user.tenant_id})
    c = neutron_client.Client(token=request.user.token.id,
                              auth_url=base.url_for(request, 'identity'),
                              endpoint_url=base.url_for(request, 'network'),
                              insecure=insecure, ca_cert=cacert)
    return c


def network_list(request, **params):
    LOG.debug("network_list(): params=%s" % (params))
    networks = neutronclient(request).list_networks(**params).get('networks')
    # Get subnet list to expand subnet info in network list.
    subnets = subnet_list(request)
    subnet_dict = SortedDict([(s['id'], s) for s in subnets])
    # Expand subnet list from subnet_id to values.
    for n in networks:
        n['subnets'] = [subnet_dict.get(s) for s in n.get('subnets', [])]
    return [Network(n) for n in networks]


def network_list_for_tenant(request, tenant_id, **params):
    """Return a network list available for the tenant.
    The list contains networks owned by the tenant and public networks.
    If requested_networks specified, it searches requested_networks only.
    """
    LOG.debug("network_list_for_tenant(): tenant_id=%s, params=%s"
              % (tenant_id, params))

    # If a user has admin role, network list returned by Neutron API
    # contains networks that do not belong to that tenant.
    # So we need to specify tenant_id when calling network_list().
    networks = network_list(request, tenant_id=tenant_id,
                            shared=False, **params)

    # In the current Neutron API, there is no way to retrieve
    # both owner networks and public networks in a single API call.
    networks += network_list(request, shared=True, **params)

    return networks


def network_get(request, network_id, expand_subnet=True, **params):
    LOG.debug("network_get(): netid=%s, params=%s" % (network_id, params))
    network = neutronclient(request).show_network(network_id,
                                                  **params).get('network')
    # Since the number of subnets per network must be small,
    # call subnet_get() for each subnet instead of calling
    # subnet_list() once.
    if expand_subnet:
        network['subnets'] = [subnet_get(request, sid)
                              for sid in network['subnets']]
    return Network(network)


def network_create(request, **kwargs):
    """Create a subnet on a specified network.
    :param request: request context
    :param tenant_id: (optional) tenant id of the network created
    :param name: (optional) name of the network created
    :returns: Subnet object
    """
    LOG.debug("network_create(): kwargs = %s" % kwargs)
    # In the case network profiles are being used, profile id is needed.
    if 'net_profile_id' in kwargs:
        kwargs['n1kv:profile_id'] = kwargs.pop('net_profile_id')
    body = {'network': kwargs}
    network = neutronclient(request).create_network(body=body).get('network')
    return Network(network)


def network_update(request, network_id, **kwargs):
    LOG.debug("network_update(): netid=%s, params=%s" % (network_id, kwargs))
    body = {'network': kwargs}
    network = neutronclient(request).update_network(network_id,
                                                    body=body).get('network')
    return Network(network)


def network_delete(request, network_id):
    LOG.debug("network_delete(): netid=%s" % network_id)
    neutronclient(request).delete_network(network_id)


def subnet_list(request, **params):
    LOG.debug("subnet_list(): params=%s" % (params))
    subnets = neutronclient(request).list_subnets(**params).get('subnets')
    return [Subnet(s) for s in subnets]


def subnet_get(request, subnet_id, **params):
    LOG.debug("subnet_get(): subnetid=%s, params=%s" % (subnet_id, params))
    subnet = neutronclient(request).show_subnet(subnet_id,
                                                **params).get('subnet')
    return Subnet(subnet)


def subnet_create(request, network_id, cidr, ip_version, **kwargs):
    """Create a subnet on a specified network.
    :param request: request context
    :param network_id: network id a subnet is created on
    :param cidr: subnet IP address range
    :param ip_version: IP version (4 or 6)
    :param gateway_ip: (optional) IP address of gateway
    :param tenant_id: (optional) tenant id of the subnet created
    :param name: (optional) name of the subnet created
    :returns: Subnet object
    """
    LOG.debug("subnet_create(): netid=%s, cidr=%s, ipver=%d, kwargs=%s"
              % (network_id, cidr, ip_version, kwargs))
    body = {'subnet':
                {'network_id': network_id,
                 'ip_version': ip_version,
                 'cidr': cidr}}
    body['subnet'].update(kwargs)
    subnet = neutronclient(request).create_subnet(body=body).get('subnet')
    return Subnet(subnet)


def subnet_update(request, subnet_id, **kwargs):
    LOG.debug("subnet_update(): subnetid=%s, kwargs=%s" % (subnet_id, kwargs))
    body = {'subnet': kwargs}
    subnet = neutronclient(request).update_subnet(subnet_id,
                                                  body=body).get('subnet')
    return Subnet(subnet)


def subnet_delete(request, subnet_id):
    LOG.debug("subnet_delete(): subnetid=%s" % subnet_id)
    neutronclient(request).delete_subnet(subnet_id)


def port_list(request, **params):
    LOG.debug("port_list(): params=%s" % (params))
    ports = neutronclient(request).list_ports(**params).get('ports')
    return [Port(p) for p in ports]


def port_get(request, port_id, **params):
    LOG.debug("port_get(): portid=%s, params=%s" % (port_id, params))
    port = neutronclient(request).show_port(port_id, **params).get('port')
    return Port(port)


def port_create(request, network_id, **kwargs):
    """Create a port on a specified network.
    :param request: request context
    :param network_id: network id a subnet is created on
    :param device_id: (optional) device id attached to the port
    :param tenant_id: (optional) tenant id of the port created
    :param name: (optional) name of the port created
    :returns: Port object
    """
    LOG.debug("port_create(): netid=%s, kwargs=%s" % (network_id, kwargs))
    # In the case policy profiles are being used, profile id is needed.
    if 'policy_profile_id' in kwargs:
        kwargs['n1kv:profile_id'] = kwargs.pop('policy_profile_id')
    body = {'port': {'network_id': network_id}}
    body['port'].update(kwargs)
    port = neutronclient(request).create_port(body=body).get('port')
    return Port(port)


def port_delete(request, port_id):
    LOG.debug("port_delete(): portid=%s" % port_id)
    neutronclient(request).delete_port(port_id)


def port_update(request, port_id, **kwargs):
    LOG.debug("port_update(): portid=%s, kwargs=%s" % (port_id, kwargs))
    body = {'port': kwargs}
    port = neutronclient(request).update_port(port_id, body=body).get('port')
    return Port(port)


def profile_list(request, type_p, **params):
    LOG.debug("profile_list(): "
              "profile_type=%(profile_type)s, params=%(params)s",
              {'profile_type': type_p, 'params': params})
    if type_p == 'network':
        profiles = neutronclient(request).list_network_profiles(
            **params).get('network_profiles')
    elif type_p == 'policy':
        profiles = neutronclient(request).list_policy_profiles(
            **params).get('policy_profiles')
    return [Profile(n) for n in profiles]


def profile_get(request, profile_id, **params):
    LOG.debug("profile_get(): "
              "profileid=%(profileid)s, params=%(params)s",
              {'profileid': profile_id, 'params': params})
    profile = neutronclient(request).show_network_profile(
        profile_id, **params).get('network_profile')
    return Profile(profile)


def profile_create(request, **kwargs):
    LOG.debug("profile_create(): kwargs=%s", kwargs)
    body = {'network_profile': {}}
    body['network_profile'].update(kwargs)
    profile = neutronclient(request).create_network_profile(
        body=body).get('network_profile')
    return Profile(profile)


def profile_delete(request, profile_id):
    LOG.debug("profile_delete(): profile_id=%s", profile_id)
    neutronclient(request).delete_network_profile(profile_id)


def profile_update(request, profile_id, **kwargs):
    LOG.debug("profile_update(): "
              "profileid=%(profileid)s, kwargs=%(kwargs)s",
              {'profileid': profile_id, 'kwargs': kwargs})
    body = {'network_profile': kwargs}
    profile = neutronclient(request).update_network_profile(
        profile_id, body=body).get('network_profile')
    return Profile(profile)


def profile_bindings_list(request, type_p, **params):
    LOG.debug("profile_bindings_list(): "
              "profile_type=%(profile_type)s params=%(params)s",
              {'profile_type': type_p, 'params': params})
    if type_p == 'network':
        bindings = neutronclient(request).list_network_profile_bindings(
            **params).get('network_profile_bindings')
    elif type_p == 'policy':
        bindings = neutronclient(request).list_policy_profile_bindings(
            **params).get('policy_profile_bindings')
    return [Profile(n) for n in bindings]


def router_create(request, **kwargs):
    LOG.debug("router_create():, kwargs=%s" % kwargs)
    body = {'router': {}}
    body['router'].update(kwargs)
    router = neutronclient(request).create_router(body=body).get('router')
    return Router(router)


def router_update(request, r_id, **kwargs):
    LOG.debug("router_update(): router_id=%s, kwargs=%s" % (r_id, kwargs))
    body = {'router': {}}
    body['router'].update(kwargs)
    router = neutronclient(request).update_router(r_id, body=body)
    return Router(router['router'])


def router_get(request, router_id, **params):
    router = neutronclient(request).show_router(router_id,
                                                **params).get('router')
    return Router(router)


def router_list(request, **params):
    routers = neutronclient(request).list_routers(**params).get('routers')
    return [Router(r) for r in routers]


def router_delete(request, router_id):
    neutronclient(request).delete_router(router_id)


def router_add_interface(request, router_id, subnet_id=None, port_id=None):
    body = {}
    if subnet_id:
        body['subnet_id'] = subnet_id
    if port_id:
        body['port_id'] = port_id
    client = neutronclient(request)
    return client.add_interface_router(router_id, body)


def router_remove_interface(request, router_id, subnet_id=None, port_id=None):
    body = {}
    if subnet_id:
        body['subnet_id'] = subnet_id
    if port_id:
        body['port_id'] = port_id
    neutronclient(request).remove_interface_router(router_id, body)


def router_add_gateway(request, router_id, network_id):
    body = {'network_id': network_id}
    neutronclient(request).add_gateway_router(router_id, body)


def router_remove_gateway(request, router_id):
    neutronclient(request).remove_gateway_router(router_id)


def tenant_quota_get(request, tenant_id):
    return base.QuotaSet(neutronclient(request).show_quota(tenant_id)['quota'])


def tenant_quota_update(request, tenant_id, **kwargs):
    quotas = {'quota': kwargs}
    return neutronclient(request).update_quota(tenant_id, quotas)


def agent_list(request):
    agents = neutronclient(request).list_agents()
    return [Agent(a) for a in agents['agents']]


def provider_list(request):
    providers = neutronclient(request).list_service_providers()
    return providers['service_providers']


def servers_update_addresses(request, servers):
    """Retrieve servers networking information from Neutron if enabled.

       Should be used when up to date networking information is required,
       and Nova's networking info caching mechanism is not fast enough.
    """

    # Get all (filtered for relevant servers) information from Neutron
    try:
        ports = port_list(request,
                          device_id=[instance.id for instance in servers])
        floating_ips = FloatingIpManager(request).list(
            port_id=[port.id for port in ports])
        networks = network_list(request,
                                id=[port.network_id for port in ports])
    except Exception:
        error_message = _('Unable to connect to Neutron.')
        LOG.error(error_message)
        messages.error(request, error_message)
        return

    # Map instance to its ports
    instances_ports = collections.defaultdict(list)
    for port in ports:
        instances_ports[port.device_id].append(port)

    # Map port to its floating ips
    ports_floating_ips = collections.defaultdict(list)
    for fip in floating_ips:
        ports_floating_ips[fip.port_id].append(fip)

    # Map network id to its name
    network_names = dict(((network.id, network.name) for network in networks))

    for server in servers:
        try:
            addresses = _server_get_addresses(
                request,
                server,
                instances_ports,
                ports_floating_ips,
                network_names)
        except Exception as e:
            LOG.error(e)
        else:
            server.addresses = addresses


def _server_get_addresses(request, server, ports, floating_ips, network_names):
    def _format_address(mac, ip, type):
        try:
            version = netaddr.IPAddress(ip).version
        except Exception as e:
            error_message = _('Unable to parse IP address %s.') % ip
            LOG.error(error_message)
            messages.error(request, error_message)
            raise e
        return {u'OS-EXT-IPS-MAC:mac_addr': mac,
                u'version': version,
                u'addr': ip,
                u'OS-EXT-IPS:type': type}

    addresses = collections.defaultdict(list)
    instance_ports = ports.get(server.id, [])
    for port in instance_ports:
        network_name = network_names.get(port.network_id)
        if network_name is not None:
            for fixed_ip in port.fixed_ips:
                addresses[network_name].append(
                    _format_address(port.mac_address,
                                    fixed_ip['ip_address'],
                                    u'fixed'))
            port_fips = floating_ips.get(port.id, [])
            for fip in port_fips:
                addresses[network_name].append(
                    _format_address(port.mac_address,
                                    fip.floating_ip_address,
                                    u'floating'))

    return dict(addresses)


@memoized
def list_extensions(request):
    extensions_list = neutronclient(request).list_extensions()
    if 'extensions' in extensions_list:
        return extensions_list['extensions']
    else:
        return {}


@memoized
def is_extension_supported(request, extension_alias):
    extensions = list_extensions(request)

    for extension in extensions:
        if extension['alias'] == extension_alias:
            return True
    else:
        return False


@memoized
def is_quotas_extension_supported(request):
    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
    if (network_config.get('enable_quotas', False) and
            is_extension_supported(request, 'quotas')):
        return True
    else:
        return False


def is_security_group_extension_supported(request):
    return is_extension_supported(request, 'security-group')


# Using this mechanism till a better plugin/sub-plugin detection
# mechanism is available.
# Using local_settings to detect if the "router" dashboard
# should be turned on or not. When using specific plugins the
# profile_support can be turned on if needed.
# Since this is a temporary mechanism used to detect profile_support
# @memorize is not being used. This is mainly used in the run_tests
# environment to detect when to use profile_support neutron APIs.
# TODO(absubram): Change this config variable check with
# subplugin/plugin detection API when it becomes available.
def is_port_profiles_supported():
    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
    # Can be used to check for vendor specific plugin
    profile_support = network_config.get('profile_support', None)
    if str(profile_support).lower() == 'cisco':
        return True
