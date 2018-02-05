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
import copy
import logging

import netaddr

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from neutronclient.common import exceptions as neutron_exc
from neutronclient.v2_0 import client as neutron_client
import six

from horizon import exceptions
from horizon import messages
from horizon.utils.memoized import memoized
from openstack_dashboard.api import base
from openstack_dashboard.api import nova
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard import policy


LOG = logging.getLogger(__name__)

IP_VERSION_DICT = {4: 'IPv4', 6: 'IPv6'}

OFF_STATE = 'OFF'
ON_STATE = 'ON'

ROUTER_INTERFACE_OWNERS = (
    'network:router_interface',
    'network:router_interface_distributed',
    'network:ha_router_replicated_interface'
)


class NeutronAPIDictWrapper(base.APIDictWrapper):

    def __init__(self, apidict):
        if 'admin_state_up' in apidict:
            if apidict['admin_state_up']:
                apidict['admin_state'] = 'UP'
            else:
                apidict['admin_state'] = 'DOWN'

        # Django cannot handle a key name with ':', so use '__'.
        apidict.update({
            key.replace(':', '__'): value
            for key, value in apidict.items()
            if ':' in key
        })
        super(NeutronAPIDictWrapper, self).__init__(apidict)

    def set_id_as_name_if_empty(self, length=8):
        try:
            if not self._apidict['name'].strip():
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
        return (self._apidict.get('name').strip() or
                '(%s)' % self._apidict['id'][:13])


class Agent(NeutronAPIDictWrapper):
    """Wrapper for neutron agents."""


class Network(NeutronAPIDictWrapper):
    """Wrapper for neutron Networks."""


class Subnet(NeutronAPIDictWrapper):
    """Wrapper for neutron subnets."""

    def __init__(self, apidict):
        apidict['ipver_str'] = get_ipver_str(apidict['ip_version'])
        super(Subnet, self).__init__(apidict)


class Trunk(NeutronAPIDictWrapper):
    """Wrapper for neutron trunks."""

    @property
    def subport_count(self):
        return len(self._apidict.get('sub_ports', []))

    def to_dict(self):
        trunk_dict = super(Trunk, self).to_dict()
        trunk_dict['name_or_id'] = self.name_or_id
        trunk_dict['subport_count'] = self.subport_count
        return trunk_dict


class SubnetPool(NeutronAPIDictWrapper):
    """Wrapper for neutron subnetpools."""


class Port(NeutronAPIDictWrapper):
    """Wrapper for neutron ports."""

    def __init__(self, apidict):
        if 'mac_learning_enabled' in apidict:
            apidict['mac_state'] = \
                ON_STATE if apidict['mac_learning_enabled'] else OFF_STATE
        pairs = apidict.get('allowed_address_pairs')
        if pairs:
            apidict = copy.deepcopy(apidict)
            wrapped_pairs = [PortAllowedAddressPair(pair) for pair in pairs]
            apidict['allowed_address_pairs'] = wrapped_pairs
        super(Port, self).__init__(apidict)


class PortAllowedAddressPair(NeutronAPIDictWrapper):
    """Wrapper for neutron port allowed address pairs."""

    def __init__(self, addr_pair):
        super(PortAllowedAddressPair, self).__init__(addr_pair)
        # Horizon references id property for table operations
        self.id = addr_pair['ip_address']


class Router(NeutronAPIDictWrapper):
    """Wrapper for neutron routers."""


class RouterStaticRoute(NeutronAPIDictWrapper):
    """Wrapper for neutron routes extra route."""

    def __init__(self, route):
        super(RouterStaticRoute, self).__init__(route)
        # Horizon references id property for table operations
        self.id = route['nexthop'] + ":" + route['destination']


class SecurityGroup(NeutronAPIDictWrapper):
    # Required attributes: id, name, description, tenant_id, rules

    def __init__(self, sg, sg_dict=None):
        if sg_dict is None:
            sg_dict = {sg['id']: sg['name']}
        sg['rules'] = [SecurityGroupRule(rule, sg_dict)
                       for rule in sg['security_group_rules']]
        super(SecurityGroup, self).__init__(sg)

    def to_dict(self):
        return {k: self._apidict[k] for k in self._apidict if k != 'rules'}


@six.python_2_unicode_compatible
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

    def __str__(self):
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


class SecurityGroupManager(object):
    """Manager class to implement Security Group methods

    SecurityGroup object returned from methods in this class
    must contains the following attributes:

    * id: ID of Security Group (int for Nova, uuid for Neutron)
    * name
    * description
    * tenant_id
    * rules: A list of SecurityGroupRule objects

    SecurityGroupRule object should have the following attributes
    (The attribute names and their formats are borrowed from nova
    security group implementation):

    * id
    * direction
    * ethertype
    * parent_group_id: security group the rule belongs to
    * ip_protocol
    * from_port: lower limit of allowed port range (inclusive)
    * to_port: upper limit of allowed port range (inclusive)
    * ip_range: remote IP CIDR (source for ingress, dest for egress).
      The value should be a format of "{'cidr': <cidr>}"
    * group: remote security group. The value should be a format of
      "{'name': <secgroup_name>}"
    """
    backend = 'neutron'

    def __init__(self, request):
        self.request = request
        self.client = neutronclient(request)

    def _list(self, **filters):
        secgroups = self.client.list_security_groups(**filters)
        return [SecurityGroup(sg) for sg in secgroups.get('security_groups')]

    @profiler.trace
    def list(self, **params):
        """Fetches a list all security groups.

        :returns: List of SecurityGroup objects
        """
        tenant_id = params.pop('tenant_id', self.request.user.tenant_id)
        return self._list(tenant_id=tenant_id, **params)

    def _sg_name_dict(self, sg_id, rules):
        """Create a mapping dict from secgroup id to its name."""
        related_ids = set([sg_id])
        related_ids |= set(filter(None, [r['remote_group_id'] for r in rules]))
        related_sgs = self.client.list_security_groups(id=related_ids,
                                                       fields=['id', 'name'])
        related_sgs = related_sgs.get('security_groups')
        return dict((sg['id'], sg['name']) for sg in related_sgs)

    @profiler.trace
    def get(self, sg_id):
        """Fetches the security group.

        :returns: SecurityGroup object corresponding to sg_id
        """
        secgroup = self.client.show_security_group(sg_id).get('security_group')
        sg_dict = self._sg_name_dict(sg_id, secgroup['security_group_rules'])
        return SecurityGroup(secgroup, sg_dict)

    @profiler.trace
    def create(self, name, desc):
        """Create a new security group.

        :returns: SecurityGroup object created
        """
        body = {'security_group': {'name': name,
                                   'description': desc,
                                   'tenant_id': self.request.user.project_id}}
        secgroup = self.client.create_security_group(body)
        return SecurityGroup(secgroup.get('security_group'))

    @profiler.trace
    def update(self, sg_id, name, desc):
        body = {'security_group': {'name': name,
                                   'description': desc}}
        secgroup = self.client.update_security_group(sg_id, body)
        return SecurityGroup(secgroup.get('security_group'))

    @profiler.trace
    def delete(self, sg_id):
        """Delete the specified security group."""
        self.client.delete_security_group(sg_id)

    @profiler.trace
    def rule_create(self, parent_group_id,
                    direction=None, ethertype=None,
                    ip_protocol=None, from_port=None, to_port=None,
                    cidr=None, group_id=None):
        """Create a new security group rule.

        :param parent_group_id: security group id a rule is created to
        :param direction: ``ingress`` or ``egress``
        :param ethertype: ``IPv4`` or ``IPv6``
        :param ip_protocol: tcp, udp, icmp
        :param from_port: L4 port range min
        :param to_port: L4 port range max
        :param cidr: Remote IP CIDR
        :param group_id: ID of Source Security Group
        :returns: SecurityGroupRule object
        """
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
        try:
            rule = self.client.create_security_group_rule(body)
        except neutron_exc.OverQuotaClient:
            raise exceptions.Conflict(
                _('Security group rule quotas exceed.'))
        except neutron_exc.Conflict:
            raise exceptions.Conflict(
                _('Security group rule already exists.'))
        rule = rule.get('security_group_rule')
        sg_dict = self._sg_name_dict(parent_group_id, [rule])
        return SecurityGroupRule(rule, sg_dict)

    @profiler.trace
    def rule_delete(self, sgr_id):
        """Delete the specified security group rule."""
        self.client.delete_security_group_rule(sgr_id)

    @profiler.trace
    def list_by_instance(self, instance_id):
        """Gets security groups of an instance.

        :returns: List of SecurityGroup objects associated with the instance
        """
        ports = port_list(self.request, device_id=instance_id)
        sg_ids = []
        for p in ports:
            sg_ids += p.security_groups
        return self._list(id=set(sg_ids)) if sg_ids else []

    @profiler.trace
    def update_instance_security_group(self, instance_id,
                                       new_security_group_ids):
        """Update security groups of a specified instance."""
        ports = port_list(self.request, device_id=instance_id)
        for p in ports:
            params = {'security_groups': new_security_group_ids}
            port_update(self.request, p.id, **params)


class FloatingIp(base.APIDictWrapper):
    _attrs = ['id', 'ip', 'fixed_ip', 'port_id', 'instance_id',
              'instance_type', 'pool']

    def __init__(self, fip):
        fip['ip'] = fip['floating_ip_address']
        fip['fixed_ip'] = fip['fixed_ip_address']
        fip['pool'] = fip['floating_network_id']
        super(FloatingIp, self).__init__(fip)


class FloatingIpPool(base.APIDictWrapper):
    pass


class FloatingIpTarget(base.APIDictWrapper):
    """Representation of floating IP association target.

    The following parameter needs to be passed when instantiating the class:

    :param port: ``Port`` object which represents a neutron port.
    :param ip_address: IP address of the ``port``. It must be one of
        IP address of a given port.
    :param label: String displayed in the floating IP association form.
        IP address will be appended to a specified label.
    """

    def __init__(self, port, ip_address, label):
        target = {'name': '%s: %s' % (label, ip_address),
                  'id': '%s_%s' % (port.id, ip_address),
                  'port_id': port.id,
                  'instance_id': port.device_id}
        super(FloatingIpTarget, self).__init__(target)


class FloatingIpManager(object):
    """Manager class to implement Floating IP methods

    The FloatingIP object returned from methods in this class
    must contains the following attributes:

    * id: ID of Floating IP
    * ip: Floating IP address
    * pool: ID of Floating IP pool from which the address is allocated
    * fixed_ip: Fixed IP address of a VIF associated with the address
    * port_id: ID of a VIF associated with the address
                (instance_id when Nova floating IP is used)
    * instance_id: Instance ID of an associated with the Floating IP
    """

    device_owner_map = {
        'compute:': 'compute',
        'neutron:LOADBALANCER': 'loadbalancer',
    }

    def __init__(self, request):
        self.request = request
        self.client = neutronclient(request)

    @profiler.trace
    def list_pools(self):
        """Fetches a list of all floating IP pools.

        :returns: List of FloatingIpPool objects
        """
        search_opts = {'router:external': True}
        return [FloatingIpPool(pool) for pool
                in self.client.list_networks(**search_opts).get('networks')]

    def _get_instance_type_from_device_owner(self, device_owner):
        for key, value in self.device_owner_map.items():
            if device_owner.startswith(key):
                return value
        return device_owner

    def _set_instance_info(self, fip, port=None):
        if fip['port_id']:
            if not port:
                port = port_get(self.request, fip['port_id'])
            fip['instance_id'] = port.device_id
            fip['instance_type'] = self._get_instance_type_from_device_owner(
                port.device_owner)
        else:
            fip['instance_id'] = None
            fip['instance_type'] = None

    @profiler.trace
    def list(self, all_tenants=False, **search_opts):
        """Fetches a list of all floating IPs.

        :returns: List of FloatingIp object
        """
        if not all_tenants:
            tenant_id = self.request.user.tenant_id
            # In Neutron, list_floatingips returns Floating IPs from
            # all tenants when the API is called with admin role, so
            # we need to filter them with tenant_id.
            search_opts['tenant_id'] = tenant_id
            port_search_opts = {'tenant_id': tenant_id}
        else:
            port_search_opts = {}
        fips = self.client.list_floatingips(**search_opts)
        fips = fips.get('floatingips')
        # Get port list to add instance_id to floating IP list
        # instance_id is stored in device_id attribute
        ports = port_list(self.request, **port_search_opts)
        port_dict = collections.OrderedDict([(p['id'], p) for p in ports])
        for fip in fips:
            self._set_instance_info(fip, port_dict.get(fip['port_id']))
        return [FloatingIp(fip) for fip in fips]

    @profiler.trace
    def get(self, floating_ip_id):
        """Fetches the floating IP.

        :returns: FloatingIp object corresponding to floating_ip_id
        """
        fip = self.client.show_floatingip(floating_ip_id).get('floatingip')
        self._set_instance_info(fip)
        return FloatingIp(fip)

    @profiler.trace
    def allocate(self, pool, tenant_id=None, **params):
        """Allocates a floating IP to the tenant.

        You must provide a pool name or id for which you would like to
        allocate a floating IP.

        :returns: FloatingIp object corresponding to an allocated floating IP
        """
        if not tenant_id:
            tenant_id = self.request.user.project_id
        create_dict = {'floating_network_id': pool,
                       'tenant_id': tenant_id}
        if 'subnet_id' in params:
            create_dict['subnet_id'] = params['subnet_id']
        if 'floating_ip_address' in params:
            create_dict['floating_ip_address'] = params['floating_ip_address']
        fip = self.client.create_floatingip(
            {'floatingip': create_dict}).get('floatingip')
        self._set_instance_info(fip)
        return FloatingIp(fip)

    @profiler.trace
    def release(self, floating_ip_id):
        """Releases a floating IP specified."""
        self.client.delete_floatingip(floating_ip_id)

    @profiler.trace
    def associate(self, floating_ip_id, port_id):
        """Associates the floating IP to the port.

        ``port_id`` represents a VNIC of an instance.
        ``port_id`` argument is different from a normal neutron port ID.
        A value passed as ``port_id`` must be one of target_id returned by
        ``list_targets``, ``get_target_id_by_instance`` or
        ``list_target_id_by_instance`` method.
        """
        # NOTE: In Neutron Horizon floating IP support, port_id is
        # "<port_id>_<ip_address>" format to identify multiple ports.
        pid, ip_address = port_id.split('_', 1)
        update_dict = {'port_id': pid,
                       'fixed_ip_address': ip_address}
        self.client.update_floatingip(floating_ip_id,
                                      {'floatingip': update_dict})

    @profiler.trace
    def disassociate(self, floating_ip_id):
        """Disassociates the floating IP specified."""
        update_dict = {'port_id': None}
        self.client.update_floatingip(floating_ip_id,
                                      {'floatingip': update_dict})

    def _get_reachable_subnets(self, ports):
        if not is_enabled_by_config('enable_fip_topology_check', True):
            # All subnets are reachable from external network
            return set(
                p.fixed_ips[0]['subnet_id'] for p in ports if p.fixed_ips
            )
        # Retrieve subnet list reachable from external network
        ext_net_ids = [ext_net.id for ext_net in self.list_pools()]
        gw_routers = [r.id for r in router_list(self.request)
                      if (r.external_gateway_info and
                          r.external_gateway_info.get('network_id')
                          in ext_net_ids)]
        reachable_subnets = set([p.fixed_ips[0]['subnet_id'] for p in ports
                                if ((p.device_owner in
                                     ROUTER_INTERFACE_OWNERS)
                                    and (p.device_id in gw_routers))])
        # we have to include any shared subnets as well because we may not
        # have permission to see the router interface to infer connectivity
        shared = set([s.id for n in network_list(self.request, shared=True)
                      for s in n.subnets])
        return reachable_subnets | shared

    @profiler.trace
    def list_targets(self):
        """Returns a list of association targets of instance VIFs.

        Each association target is represented as FloatingIpTarget object.
        FloatingIpTarget is a APIResourceWrapper/APIDictWrapper and
        'id' and 'name' attributes must be defined in each object.
        FloatingIpTarget.id can be passed as port_id in associate().
        FloatingIpTarget.name is displayed in Floating Ip Association Form.
        """
        tenant_id = self.request.user.tenant_id
        ports = port_list(self.request, tenant_id=tenant_id)
        servers, has_more = nova.server_list(self.request, detailed=False)
        server_dict = collections.OrderedDict(
            [(s.id, s.name) for s in servers])
        reachable_subnets = self._get_reachable_subnets(ports)

        targets = []
        for p in ports:
            # Remove network ports from Floating IP targets
            if p.device_owner.startswith('network:'):
                continue
            server_name = server_dict.get(p.device_id)

            for ip in p.fixed_ips:
                if ip['subnet_id'] not in reachable_subnets:
                    continue
                targets.append(FloatingIpTarget(p, ip['ip_address'],
                                                server_name))
        return targets

    def _target_ports_by_instance(self, instance_id):
        if not instance_id:
            return None
        search_opts = {'device_id': instance_id}
        return port_list(self.request, **search_opts)

    @profiler.trace
    def get_target_id_by_instance(self, instance_id, target_list=None):
        """Returns a target ID of floating IP association.

        :param instance_id: ID of target VM instance
        :param target_list: (optional) a list returned by list_targets().
            If specified, looking up is done against the specified list
            to save extra API calls to a back-end. Otherwise a target
            information is retrieved from a back-end inside the method.
        """
        if target_list is not None:
            targets = [target for target in target_list
                       if target['instance_id'] == instance_id]
            if not targets:
                return None
            return targets[0]['id']
        else:
            # In Neutron one port can have multiple ip addresses, so this
            # method picks up the first one and generate target id.
            ports = self._target_ports_by_instance(instance_id)
            if not ports:
                return None
            return '{0}_{1}'.format(ports[0].id,
                                    ports[0].fixed_ips[0]['ip_address'])

    @profiler.trace
    def list_target_id_by_instance(self, instance_id, target_list=None):
        """Returns a list of instance's target IDs of floating IP association.

        :param instance_id: ID of target VM instance
        :param target_list: (optional) a list returned by list_targets().
            If specified, looking up is done against the specified list
            to save extra API calls to a back-end. Otherwise target list
            is retrieved from a back-end inside the method.
        """
        if target_list is not None:
            return [target['id'] for target in target_list
                    if target['instance_id'] == instance_id]
        else:
            ports = self._target_ports_by_instance(instance_id)
            return ['{0}_{1}'.format(p.id, p.fixed_ips[0]['ip_address'])
                    for p in ports]

    def is_simple_associate_supported(self):
        """Returns True if the default floating IP pool is enabled."""
        # NOTE: There are two reason that simple association support
        # needs more considerations. (1) Neutron does not support the
        # default floating IP pool at the moment. It can be avoided
        # in case where only one floating IP pool exists.
        # (2) Neutron floating IP is associated with each VIF and
        # we need to check whether such VIF is only one for an instance
        # to enable simple association support.
        return False

    def is_supported(self):
        """Returns True if floating IP feature is supported."""
        network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
        return network_config.get('enable_router', True)


def get_ipver_str(ip_version):
    """Convert an ip version number to a human-friendly string."""
    return IP_VERSION_DICT.get(ip_version, '')


@memoized
def neutronclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    c = neutron_client.Client(token=request.user.token.id,
                              auth_url=base.url_for(request, 'identity'),
                              endpoint_url=base.url_for(request, 'network'),
                              insecure=insecure, ca_cert=cacert)
    return c


@profiler.trace
def list_resources_with_long_filters(list_method,
                                     filter_attr, filter_values, **params):
    """List neutron resources with handling RequestURITooLong exception.

    If filter parameters are long, list resources API request leads to
    414 error (URL is too long). For such case, this method split
    list parameters specified by a list_field argument into chunks
    and call the specified list_method repeatedly.

    :param list_method: Method used to retrieve resource list.
    :param filter_attr: attribute name to be filtered. The value corresponding
        to this attribute is specified by "filter_values".
        If you want to specify more attributes for a filter condition,
        pass them as keyword arguments like "attr2=values2".
    :param filter_values: values of "filter_attr" to be filtered.
        If filter_values are too long and the total URI length exceed the
        maximum length supported by the neutron server, filter_values will
        be split into sub lists if filter_values is a list.
    :param params: parameters to pass a specified listing API call
        without any changes. You can specify more filter conditions
        in addition to a pair of filter_attr and filter_values.
    """
    try:
        params[filter_attr] = filter_values
        return list_method(**params)
    except neutron_exc.RequestURITooLong as uri_len_exc:
        # The URI is too long because of too many filter values.
        # Use the excess attribute of the exception to know how many
        # filter values can be inserted into a single request.

        # We consider only the filter condition from (filter_attr,
        # filter_values) and do not consider other filter conditions
        # which may be specified in **params.
        if not isinstance(filter_values, (list, tuple, set, frozenset)):
            filter_values = [filter_values]

        # Length of each query filter is:
        # <key>=<value>& (e.g., id=<uuid>)
        # The length will be key_len + value_maxlen + 2
        all_filter_len = sum(len(filter_attr) + len(val) + 2
                             for val in filter_values)
        allowed_filter_len = all_filter_len - uri_len_exc.excess

        val_maxlen = max(len(val) for val in filter_values)
        filter_maxlen = len(filter_attr) + val_maxlen + 2
        chunk_size = allowed_filter_len // filter_maxlen

        resources = []
        for i in range(0, len(filter_values), chunk_size):
            params[filter_attr] = filter_values[i:i + chunk_size]
            resources.extend(list_method(**params))
        return resources


@profiler.trace
def trunk_list(request, **params):
    LOG.debug("trunk_list(): params=%s", params)
    trunks = neutronclient(request).list_trunks(**params).get('trunks')
    return [Trunk(t) for t in trunks]


@profiler.trace
def trunk_delete(request, trunk_id):
    LOG.debug("trunk_delete(): trunk_id=%s", trunk_id)
    neutronclient(request).delete_trunk(trunk_id)


@profiler.trace
def trunk_show(request, trunk_id):
    LOG.debug("trunk_show(): trunk_id=%s", trunk_id)
    trunk = neutronclient(request).show_trunk(trunk_id).get('trunk')
    return Trunk(trunk)


@profiler.trace
def network_list(request, **params):
    LOG.debug("network_list(): params=%s", params)
    networks = neutronclient(request).list_networks(**params).get('networks')
    # Get subnet list to expand subnet info in network list.
    subnets = subnet_list(request)
    subnet_dict = dict([(s['id'], s) for s in subnets])
    # Expand subnet list from subnet_id to values.
    for n in networks:
        # Due to potential timing issues, we can't assume the subnet_dict data
        # is in sync with the network data.
        n['subnets'] = [subnet_dict[s] for s in n.get('subnets', []) if
                        s in subnet_dict]
    return [Network(n) for n in networks]


@profiler.trace
def network_list_for_tenant(request, tenant_id, include_external=False,
                            **params):
    """Return a network list available for the tenant.

    The list contains networks owned by the tenant and public networks.
    If requested_networks specified, it searches requested_networks only.
    """
    LOG.debug("network_list_for_tenant(): tenant_id=%(tenant_id)s, "
              "params=%(params)s", {'tenant_id': tenant_id, 'params': params})

    networks = []
    shared = params.get('shared')
    if shared is not None:
        del params['shared']

    if shared in (None, False):
        # If a user has admin role, network list returned by Neutron API
        # contains networks that do not belong to that tenant.
        # So we need to specify tenant_id when calling network_list().
        networks += network_list(request, tenant_id=tenant_id,
                                 shared=False, **params)

    if shared in (None, True):
        # In the current Neutron API, there is no way to retrieve
        # both owner networks and public networks in a single API call.
        networks += network_list(request, shared=True, **params)
    params['router:external'] = params.get('router:external', True)
    if params['router:external'] and include_external:
        if shared is not None:
            params['shared'] = shared
        fetched_net_ids = [n.id for n in networks]
        # Retrieves external networks when router:external is not specified
        # in (filtering) params or router:external=True filter is specified.
        # When router:external=False is specified there is no need to query
        # networking API because apparently nothing will match the filter.
        ext_nets = network_list(request, **params)
        networks += [n for n in ext_nets if
                     n.id not in fetched_net_ids]

    return networks


@profiler.trace
def network_get(request, network_id, expand_subnet=True, **params):
    LOG.debug("network_get(): netid=%(network_id)s, params=%(params)s",
              {'network_id': network_id, 'params': params})
    network = neutronclient(request).show_network(network_id,
                                                  **params).get('network')
    if expand_subnet:
        # NOTE(amotoki): There are some cases where a user has no permission
        # to get subnet details, but the condition is complicated. We first
        # try to fetch subnet details. If successful, the subnet details are
        # set to network['subnets'] as a list of "Subent" object.
        # If NotFound exception is returned by neutron, network['subnets'] is
        # left untouched and a list of subnet IDs are stored.
        # Neutron returns NotFound exception if a request user has enough
        # permission to access a requested resource, so we catch only
        # NotFound exception here.
        try:
            # Since the number of subnets per network must be small,
            # call subnet_get() for each subnet instead of calling
            # subnet_list() once.
            network['subnets'] = [subnet_get(request, sid)
                                  for sid in network['subnets']]
        except neutron_exc.NotFound:
            pass
    return Network(network)


@profiler.trace
def network_create(request, **kwargs):
    """Create a  network object.

    :param request: request context
    :param tenant_id: (optional) tenant id of the network created
    :param name: (optional) name of the network created
    :returns: Network object
    """
    LOG.debug("network_create(): kwargs = %s", kwargs)
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body = {'network': kwargs}
    network = neutronclient(request).create_network(body=body).get('network')
    return Network(network)


@profiler.trace
def network_update(request, network_id, **kwargs):
    LOG.debug("network_update(): netid=%(network_id)s, params=%(params)s",
              {'network_id': network_id, 'params': kwargs})
    body = {'network': kwargs}
    network = neutronclient(request).update_network(network_id,
                                                    body=body).get('network')
    return Network(network)


@profiler.trace
def network_delete(request, network_id):
    LOG.debug("network_delete(): netid=%s", network_id)
    neutronclient(request).delete_network(network_id)


@profiler.trace
@memoized
def subnet_list(request, **params):
    LOG.debug("subnet_list(): params=%s", params)
    subnets = neutronclient(request).list_subnets(**params).get('subnets')
    return [Subnet(s) for s in subnets]


@profiler.trace
def subnet_get(request, subnet_id, **params):
    LOG.debug("subnet_get(): subnetid=%(subnet_id)s, params=%(params)s",
              {'subnet_id': subnet_id, 'params': params})
    subnet = neutronclient(request).show_subnet(subnet_id,
                                                **params).get('subnet')
    return Subnet(subnet)


@profiler.trace
def subnet_create(request, network_id, **kwargs):
    """Create a subnet on a specified network.

    :param request: request context
    :param network_id: network id a subnet is created on
    :param cidr: (optional) subnet IP address range
    :param ip_version: (optional) IP version (4 or 6)
    :param gateway_ip: (optional) IP address of gateway
    :param tenant_id: (optional) tenant id of the subnet created
    :param name: (optional) name of the subnet created
    :param subnetpool_id: (optional) subnetpool to allocate prefix from
    :param prefixlen: (optional) length of prefix to allocate
    :returns: Subnet object

    Although both cidr+ip_version and subnetpool_id+preifxlen is listed as
    optional you MUST pass along one of the combinations to get a successful
    result.
    """
    LOG.debug("subnet_create(): netid=%(network_id)s, kwargs=%(kwargs)s",
              {'network_id': network_id, 'kwargs': kwargs})
    body = {'subnet': {'network_id': network_id}}
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body['subnet'].update(kwargs)
    subnet = neutronclient(request).create_subnet(body=body).get('subnet')
    return Subnet(subnet)


@profiler.trace
def subnet_update(request, subnet_id, **kwargs):
    LOG.debug("subnet_update(): subnetid=%(subnet_id)s, kwargs=%(kwargs)s",
              {'subnet_id': subnet_id, 'kwargs': kwargs})
    body = {'subnet': kwargs}
    subnet = neutronclient(request).update_subnet(subnet_id,
                                                  body=body).get('subnet')
    return Subnet(subnet)


@profiler.trace
def subnet_delete(request, subnet_id):
    LOG.debug("subnet_delete(): subnetid=%s", subnet_id)
    neutronclient(request).delete_subnet(subnet_id)


@profiler.trace
def subnetpool_list(request, **params):
    LOG.debug("subnetpool_list(): params=%s", params)
    subnetpools = \
        neutronclient(request).list_subnetpools(**params).get('subnetpools')
    return [SubnetPool(s) for s in subnetpools]


@profiler.trace
def subnetpool_get(request, subnetpool_id, **params):
    LOG.debug("subnetpool_get(): subnetpoolid=%(subnetpool_id)s, "
              "params=%(params)s", {'subnetpool_id': subnetpool_id,
                                    'params': params})
    subnetpool = \
        neutronclient(request).show_subnetpool(subnetpool_id,
                                               **params).get('subnetpool')
    return SubnetPool(subnetpool)


@profiler.trace
def subnetpool_create(request, name, prefixes, **kwargs):
    """Create a subnetpool.

    ip_version is auto-detected in back-end.

    Parameters:
    request           -- Request context
    name              -- Name for subnetpool
    prefixes          -- List of prefixes for pool

    Keyword Arguments (optional):
    min_prefixlen     -- Minimum prefix length for allocations from pool
    max_prefixlen     -- Maximum prefix length for allocations from pool
    default_prefixlen -- Default prefix length for allocations from pool
    default_quota     -- Default quota for allocations from pool
    shared            -- Subnetpool should be shared (Admin-only)
    tenant_id         -- Owner of subnetpool

    Returns:
    SubnetPool object
    """
    LOG.debug("subnetpool_create(): name=%(name)s, prefixes=%(prefixes)s, "
              "kwargs=%(kwargs)s", {'name': name, 'prefixes': prefixes,
                                    'kwargs': kwargs})
    body = {'subnetpool':
            {'name': name,
             'prefixes': prefixes,
             }
            }
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body['subnetpool'].update(kwargs)
    subnetpool = \
        neutronclient(request).create_subnetpool(body=body).get('subnetpool')
    return SubnetPool(subnetpool)


@profiler.trace
def subnetpool_update(request, subnetpool_id, **kwargs):
    LOG.debug("subnetpool_update(): subnetpoolid=%(subnetpool_id)s, "
              "kwargs=%(kwargs)s", {'subnetpool_id': subnetpool_id,
                                    'kwargs': kwargs})
    body = {'subnetpool': kwargs}
    subnetpool = \
        neutronclient(request).update_subnetpool(subnetpool_id,
                                                 body=body).get('subnetpool')
    return SubnetPool(subnetpool)


@profiler.trace
def subnetpool_delete(request, subnetpool_id):
    LOG.debug("subnetpool_delete(): subnetpoolid=%s", subnetpool_id)
    return neutronclient(request).delete_subnetpool(subnetpool_id)


@profiler.trace
@memoized
def port_list(request, **params):
    LOG.debug("port_list(): params=%s", params)
    ports = neutronclient(request).list_ports(**params).get('ports')
    return [Port(p) for p in ports]


@profiler.trace
def port_get(request, port_id, **params):
    LOG.debug("port_get(): portid=%(port_id)s, params=%(params)s",
              {'port_id': port_id, 'params': params})
    port = neutronclient(request).show_port(port_id, **params).get('port')
    return Port(port)


def unescape_port_kwargs(**kwargs):
    for key in kwargs:
        if '__' in key:
            kwargs[':'.join(key.split('__'))] = kwargs.pop(key)
    return kwargs


@profiler.trace
def port_create(request, network_id, **kwargs):
    """Create a port on a specified network.

    :param request: request context
    :param network_id: network id a subnet is created on
    :param device_id: (optional) device id attached to the port
    :param tenant_id: (optional) tenant id of the port created
    :param name: (optional) name of the port created
    :returns: Port object
    """
    LOG.debug("port_create(): netid=%(network_id)s, kwargs=%(kwargs)s",
              {'network_id': network_id, 'kwargs': kwargs})
    kwargs = unescape_port_kwargs(**kwargs)
    body = {'port': {'network_id': network_id}}
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body['port'].update(kwargs)
    port = neutronclient(request).create_port(body=body).get('port')
    return Port(port)


@profiler.trace
def port_delete(request, port_id):
    LOG.debug("port_delete(): portid=%s", port_id)
    neutronclient(request).delete_port(port_id)


@profiler.trace
def port_update(request, port_id, **kwargs):
    LOG.debug("port_update(): portid=%(port_id)s, kwargs=%(kwargs)s",
              {'port_id': port_id, 'kwargs': kwargs})
    kwargs = unescape_port_kwargs(**kwargs)
    body = {'port': kwargs}
    port = neutronclient(request).update_port(port_id, body=body).get('port')
    return Port(port)


@profiler.trace
def router_create(request, **kwargs):
    LOG.debug("router_create():, kwargs=%s", kwargs)
    body = {'router': {}}
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body['router'].update(kwargs)
    router = neutronclient(request).create_router(body=body).get('router')
    return Router(router)


@profiler.trace
def router_update(request, r_id, **kwargs):
    LOG.debug("router_update(): router_id=%(r_id)s, kwargs=%(kwargs)s",
              {'r_id': r_id, 'kwargs': kwargs})
    body = {'router': {}}
    body['router'].update(kwargs)
    router = neutronclient(request).update_router(r_id, body=body)
    return Router(router['router'])


@profiler.trace
def router_get(request, router_id, **params):
    router = neutronclient(request).show_router(router_id,
                                                **params).get('router')
    return Router(router)


@profiler.trace
def router_list(request, **params):
    routers = neutronclient(request).list_routers(**params).get('routers')
    return [Router(r) for r in routers]


@profiler.trace
def router_list_on_l3_agent(request, l3_agent_id, **params):
    routers = neutronclient(request).\
        list_routers_on_l3_agent(l3_agent_id,
                                 **params).get('routers')
    return [Router(r) for r in routers]


@profiler.trace
def router_delete(request, router_id):
    neutronclient(request).delete_router(router_id)


@profiler.trace
def router_add_interface(request, router_id, subnet_id=None, port_id=None):
    body = {}
    if subnet_id:
        body['subnet_id'] = subnet_id
    if port_id:
        body['port_id'] = port_id
    client = neutronclient(request)
    return client.add_interface_router(router_id, body)


@profiler.trace
def router_remove_interface(request, router_id, subnet_id=None, port_id=None):
    body = {}
    if subnet_id:
        body['subnet_id'] = subnet_id
    if port_id:
        body['port_id'] = port_id
    neutronclient(request).remove_interface_router(router_id, body)


@profiler.trace
def router_add_gateway(request, router_id, network_id):
    body = {'network_id': network_id}
    neutronclient(request).add_gateway_router(router_id, body)


@profiler.trace
def router_remove_gateway(request, router_id):
    neutronclient(request).remove_gateway_router(router_id)


@profiler.trace
def router_static_route_list(request, router_id=None):
    router = router_get(request, router_id)
    try:
        routes = [RouterStaticRoute(r) for r in router.routes]
    except AttributeError:
        LOG.debug("router_static_route_list(): router_id=%(router_id)s, "
                  "router=%(router)s", {'router_id': router_id,
                                        'router': router})
        return []
    return routes


@profiler.trace
def router_static_route_remove(request, router_id, route_ids):
    currentroutes = router_static_route_list(request, router_id=router_id)
    newroutes = []
    for oldroute in currentroutes:
        if oldroute.id not in route_ids:
            newroutes.append({'nexthop': oldroute.nexthop,
                              'destination': oldroute.destination})
    body = {'routes': newroutes}
    new = router_update(request, router_id, **body)
    return new


@profiler.trace
def router_static_route_add(request, router_id, newroute):
    body = {}
    currentroutes = router_static_route_list(request, router_id=router_id)
    body['routes'] = [newroute] + [{'nexthop': r.nexthop,
                                    'destination': r.destination}
                                   for r in currentroutes]
    new = router_update(request, router_id, **body)
    return new


@profiler.trace
def tenant_quota_get(request, tenant_id):
    return base.QuotaSet(neutronclient(request).show_quota(tenant_id)['quota'])


@profiler.trace
def tenant_quota_update(request, tenant_id, **kwargs):
    quotas = {'quota': kwargs}
    return neutronclient(request).update_quota(tenant_id, quotas)


@profiler.trace
def agent_list(request, **params):
    agents = neutronclient(request).list_agents(**params)
    return [Agent(a) for a in agents['agents']]


@profiler.trace
def list_dhcp_agent_hosting_networks(request, network, **params):
    agents = neutronclient(request).list_dhcp_agent_hosting_networks(network,
                                                                     **params)
    return [Agent(a) for a in agents['agents']]


@profiler.trace
def list_l3_agent_hosting_router(request, router, **params):
    agents = neutronclient(request).list_l3_agent_hosting_routers(router,
                                                                  **params)
    return [Agent(a) for a in agents['agents']]


@profiler.trace
def show_network_ip_availability(request, network_id):
    ip_availability = neutronclient(request).show_network_ip_availability(
        network_id)
    return ip_availability


@profiler.trace
def add_network_to_dhcp_agent(request, dhcp_agent, network_id):
    body = {'network_id': network_id}
    return neutronclient(request).add_network_to_dhcp_agent(dhcp_agent, body)


@profiler.trace
def remove_network_from_dhcp_agent(request, dhcp_agent, network_id):
    return neutronclient(request).remove_network_from_dhcp_agent(dhcp_agent,
                                                                 network_id)


@profiler.trace
def provider_list(request):
    providers = neutronclient(request).list_service_providers()
    return providers['service_providers']


def floating_ip_pools_list(request):
    return FloatingIpManager(request).list_pools()


@memoized
def tenant_floating_ip_list(request, all_tenants=False):
    return FloatingIpManager(request).list(all_tenants=all_tenants)


def tenant_floating_ip_get(request, floating_ip_id):
    return FloatingIpManager(request).get(floating_ip_id)


def tenant_floating_ip_allocate(request, pool=None, tenant_id=None, **params):
    return FloatingIpManager(request).allocate(pool, tenant_id, **params)


def tenant_floating_ip_release(request, floating_ip_id):
    return FloatingIpManager(request).release(floating_ip_id)


def floating_ip_associate(request, floating_ip_id, port_id):
    return FloatingIpManager(request).associate(floating_ip_id, port_id)


def floating_ip_disassociate(request, floating_ip_id):
    return FloatingIpManager(request).disassociate(floating_ip_id)


def floating_ip_target_list(request):
    return FloatingIpManager(request).list_targets()


def floating_ip_target_get_by_instance(request, instance_id, cache=None):
    return FloatingIpManager(request).get_target_id_by_instance(
        instance_id, cache)


def floating_ip_target_list_by_instance(request, instance_id, cache=None):
    return FloatingIpManager(request).list_target_id_by_instance(
        instance_id, cache)


def floating_ip_simple_associate_supported(request):
    return FloatingIpManager(request).is_simple_associate_supported()


def floating_ip_supported(request):
    return FloatingIpManager(request).is_supported()


@memoized
def security_group_list(request, **params):
    return SecurityGroupManager(request).list(**params)


def security_group_get(request, sg_id):
    return SecurityGroupManager(request).get(sg_id)


def security_group_create(request, name, desc):
    return SecurityGroupManager(request).create(name, desc)


def security_group_delete(request, sg_id):
    return SecurityGroupManager(request).delete(sg_id)


def security_group_update(request, sg_id, name, desc):
    return SecurityGroupManager(request).update(sg_id, name, desc)


def security_group_rule_create(request, parent_group_id,
                               direction, ethertype,
                               ip_protocol, from_port, to_port,
                               cidr, group_id):
    return SecurityGroupManager(request).rule_create(
        parent_group_id, direction, ethertype, ip_protocol,
        from_port, to_port, cidr, group_id)


def security_group_rule_delete(request, sgr_id):
    return SecurityGroupManager(request).rule_delete(sgr_id)


def server_security_groups(request, instance_id):
    return SecurityGroupManager(request).list_by_instance(instance_id)


def server_update_security_groups(request, instance_id,
                                  new_security_group_ids):
    return SecurityGroupManager(request).update_instance_security_group(
        instance_id, new_security_group_ids)


# TODO(pkarikh) need to uncomment when osprofiler will have no
# issues with unicode in:
# openstack_dashboard/test/test_data/nova_data.py#L470 data
# @profiler.trace
def servers_update_addresses(request, servers, all_tenants=False):
    """Retrieve servers networking information from Neutron if enabled.

       Should be used when up to date networking information is required,
       and Nova's networking info caching mechanism is not fast enough.
    """

    # Get all (filtered for relevant servers) information from Neutron
    try:
        # NOTE(e0ne): we need tuple here to work with @memoized decorator.
        # @memoized works with hashable arguments only.
        ports = list_resources_with_long_filters(
            port_list, 'device_id',
            tuple([instance.id for instance in servers]),
            request=request)
        fips = FloatingIpManager(request)
        if fips.is_supported():
            floating_ips = list_resources_with_long_filters(
                fips.list, 'port_id', tuple([port.id for port in ports]),
                all_tenants=all_tenants)
        else:
            floating_ips = []
        # NOTE(e0ne): we need frozenset here to work with @memoized decorator.
        # @memoized works with hashable arguments only
        networks = list_resources_with_long_filters(
            network_list, 'id', frozenset([port.network_id for port in ports]),
            request=request)
    except Exception as e:
        LOG.error('Unable to connect to Neutron: %s', e)
        error_message = _('Unable to connect to Neutron.')
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
            LOG.error(six.text_type(e))
        else:
            server.addresses = addresses


def _server_get_addresses(request, server, ports, floating_ips, network_names):
    def _format_address(mac, ip, type):
        try:
            version = netaddr.IPAddress(ip).version
        except Exception as e:
            LOG.error('Unable to parse IP address %(ip)s: %(exc)s',
                      {'ip': ip, 'exc': e})
            error_message = _('Unable to parse IP address %s.') % ip
            messages.error(request, error_message)
            raise
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


@profiler.trace
@memoized
def list_extensions(request):
    try:
        extensions_list = neutronclient(request).list_extensions()
    except exceptions.ServiceCatalogException:
        return {}
    if 'extensions' in extensions_list:
        return tuple(extensions_list['extensions'])
    else:
        return ()


@profiler.trace
@memoized
def is_extension_supported(request, extension_alias):
    extensions = list_extensions(request)

    for extension in extensions:
        if extension['alias'] == extension_alias:
            return True
    else:
        return False


def is_enabled_by_config(name, default=True):
    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
    return network_config.get(name, default)


@memoized
def is_service_enabled(request, config_name, ext_name):
    return (is_enabled_by_config(config_name) and
            is_extension_supported(request, ext_name))


@memoized
def is_quotas_extension_supported(request):
    return (is_enabled_by_config('enable_quotas', False) and
            is_extension_supported(request, 'quotas'))


@memoized
def is_router_enabled(request):
    return (is_enabled_by_config('enable_router') and
            is_extension_supported(request, 'router'))

# FEATURE_MAP is used to define:
# - related neutron extension name (key: "extension")
# - corresponding dashboard config (key: "config")
# - RBAC policies (key: "poclies")
# If a key is not contained, the corresponding permission check is skipped.
FEATURE_MAP = {
    'dvr': {
        'extension': 'dvr',
        'config': {
            'name': 'enable_distributed_router',
            'default': False,
        },
        'policies': {
            'get': 'get_router:distributed',
            'create': 'create_router:distributed',
            'update': 'update_router:distributed',
        }
    },
    'l3-ha': {
        'extension': 'l3-ha',
        'config': {'name': 'enable_ha_router',
                   'default': False},
        'policies': {
            'get': 'get_router:ha',
            'create': 'create_router:ha',
            'update': 'update_router:ha',
        }
    },
}


def get_feature_permission(request, feature, operation=None):
    """Check if a feature-specific field can be displayed.

    This method check a permission for a feature-specific field.
    Such field is usually provided through Neutron extension.

    :param request: Request Object
    :param feature: feature name defined in FEATURE_MAP
    :param operation (optional): Operation type. The valid value should be
        defined in FEATURE_MAP[feature]['policies']
        It must be specified if FEATURE_MAP[feature] has 'policies'.
    """
    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
    feature_info = FEATURE_MAP.get(feature)
    if not feature_info:
        raise ValueError("The requested feature '%(feature)s' is unknown. "
                         "Please make sure to specify a feature defined "
                         "in FEATURE_MAP.")

    # Check dashboard settings
    feature_config = feature_info.get('config')
    if feature_config:
        if not network_config.get(feature_config['name'],
                                  feature_config['default']):
            return False

    # Check policy
    feature_policies = feature_info.get('policies')
    if feature_policies:
        policy_name = feature_policies.get(operation)
        if not policy_name:
            raise ValueError("The 'operation' parameter for "
                             "get_feature_permission '%(feature)s' "
                             "is invalid. It should be one of %(allowed)s"
                             % {'feature': feature,
                                'allowed': ' '.join(feature_policies.keys())})
        role = (('network', policy_name),)
        if not policy.check(role, request):
            return False

    # Check if a required extension is enabled
    feature_extension = feature_info.get('extension')
    if feature_extension:
        try:
            return is_extension_supported(request, feature_extension)
        except Exception:
            LOG.info("Failed to check Neutron '%s' extension is not supported",
                     feature_extension)
            return False

    # If all checks are passed, now a given feature is allowed.
    return True


class QoSPolicy(NeutronAPIDictWrapper):
    """Wrapper for neutron QoS Policy."""

    def to_dict(self):
        return self._apidict


def policy_create(request, **kwargs):
    """Create a QoS Policy.

    :param request: request context
    :param name: name of the policy
    :param description: description of policy
    :param shared: boolean (true or false)
    :return: QoSPolicy object
    """
    body = {'policy': kwargs}
    policy = neutronclient(request).create_qos_policy(body=body).get('policy')
    return QoSPolicy(policy)


def policy_list(request, **kwargs):
    """List of QoS Policies."""
    policies = neutronclient(request).list_qos_policies(
        **kwargs).get('policies')
    return [QoSPolicy(p) for p in policies]


@profiler.trace
def policy_get(request, policy_id, **kwargs):
    """Get QoS policy for a given policy id."""
    policy = neutronclient(request).show_qos_policy(
        policy_id, **kwargs).get('policy')
    return QoSPolicy(policy)
