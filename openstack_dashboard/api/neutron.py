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

import collections
from collections.abc import Sequence
import copy
import itertools
import logging
import types

import netaddr

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from keystoneauth1 import exceptions as ks_exceptions
from keystoneauth1 import session
from keystoneauth1 import token_endpoint
from neutronclient.common import exceptions as neutron_exc
from neutronclient.v2_0 import client as neutron_client
from novaclient import exceptions as nova_exc
import openstack
from openstack import exceptions as sdk_exceptions
import requests

from openstack_auth import utils as auth_utils

from horizon import exceptions
from horizon import messages
from horizon.utils.memoized import memoized
from openstack_dashboard.api import base
from openstack_dashboard.api import nova
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard import policy
from openstack_dashboard.utils import settings as setting_utils


LOG = logging.getLogger(__name__)

IP_VERSION_DICT = {4: 'IPv4', 6: 'IPv6'}

OFF_STATE = 'OFF'
ON_STATE = 'ON'

ROUTER_INTERFACE_OWNERS = (
    'network:router_interface',
    'network:router_interface_distributed',
    'network:ha_router_replicated_interface'
)

VNIC_TYPES = [
    ('normal', _('Normal')),
    ('direct', _('Direct')),
    ('direct-physical', _('Direct Physical')),
    ('macvtap', _('MacVTap')),
    ('baremetal', _('Bare Metal')),
    ('virtio-forwarder', _('Virtio Forwarder')),
    ('smart-nic', _('Smart NIC')),
    ('vdpa', _('vHost vDPA')),
    ('accelerator-direct', _('Accelerator Direct')),
    ('accelerator-direct-physical', _('Accelerator Direct Physical')),
    ('remote-managed', _('Remote Managed')),
]


class NeutronAPIDictWrapper(base.APIDictWrapper):

    def __init__(self, apidict):
        if 'is_admin_state_up' in apidict:
            if apidict['is_admin_state_up']:
                apidict['admin_state'] = 'UP'
            else:
                apidict['admin_state'] = 'DOWN'
        if 'admin_state_up' in apidict:
            if apidict['admin_state_up']:
                apidict['admin_state'] = 'UP'
            else:
                apidict['admin_state'] = 'DOWN'

        # https://bugs.launchpad.net/horizon/+bug/2093367
        if 'is_port_security_enabled' in apidict:
            if apidict['is_port_security_enabled']:
                apidict['port_security_enabled'] = 'UP'

        # Django cannot handle a key name with ':', so use '__'.
        apidict.update({
            key.replace(':', '__'): value
            for key, value in apidict.items()
            if ':' in key
        })
        super().__init__(apidict)

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
        super().__init__(apidict)


AUTO_ALLOCATE_ID = '__auto_allocate__'


class PreAutoAllocateNetwork(Network):
    def __init__(self, request):
        tenant_id = request.user.tenant_id
        auto_allocated_subnet = Subnet({
            'name': 'auto_allocated_subnet',
            'id': AUTO_ALLOCATE_ID,
            'network_id': 'auto',
            'tenant_id': tenant_id,
            # The following two fields are fake so that Subnet class
            # and the network topology view work without errors.
            'ip_version': 4,
            'cidr': '0.0.0.0/0',
        })
        auto_allocated_network = {
            'name': 'auto_allocated_network',
            'description': 'Network to be allocated automatically',
            'id': AUTO_ALLOCATE_ID,
            'status': 'ACTIVE',
            'admin_state_up': True,
            'shared': False,
            'router:external': False,
            'subnets': [auto_allocated_subnet],
            'tenant_id': tenant_id,
        }
        super().__init__(auto_allocated_network)


class Trunk(NeutronAPIDictWrapper):
    """Wrapper for neutron trunks."""

    @property
    def subport_count(self):
        return len(self._apidict.get('sub_ports', []))

    def to_dict(self):
        trunk_dict = super().to_dict()
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
        super().__init__(apidict)


class PortTrunkParent(Port):
    """Neutron ports that are trunk parents.

    There's no need to add extra attributes for a trunk parent, because it
    already has 'trunk_details'. See also class PortTrunkSubport.
    """


class PortTrunkSubport(Port):
    """Neutron ports that are trunk subports.

    The Neutron API expresses port subtyping information in a surprisingly
    complex way. When you see a port with attribute 'trunk_details' you know
    it's a trunk parent. But when you see a port without the 'trunk_details'
    attribute you can't tell if it's a trunk subport or a regular one without
    looking beyond the port's attributes. You must go and check if trunks
    (and/or trunk_details of trunk parent ports) refer to this port.

    Since this behavior is awfully complex we hide this from the rest of
    horizon by introducing types PortTrunkParent and PortTrunkSubport.
    """

    def __init__(self, apidict, trunk_subport_info):
        for field in ['trunk_id', 'segmentation_type', 'segmentation_id']:
            apidict[field] = trunk_subport_info[field]
        super().__init__(apidict)


class PortAllowedAddressPair(NeutronAPIDictWrapper):
    """Wrapper for neutron port allowed address pairs."""

    def __init__(self, addr_pair):
        super().__init__(addr_pair)
        # Horizon references id property for table operations
        mac_addr = addr_pair['mac_address'].replace(':', '-')
        self.id = addr_pair['ip_address'] + ":" + mac_addr


class Router(NeutronAPIDictWrapper):
    """Wrapper for neutron routers."""


class RouterStaticRoute(NeutronAPIDictWrapper):
    """Wrapper for neutron routes extra route."""

    def __init__(self, route):
        super().__init__(route)
        # Horizon references id property for table operations
        self.id = route['nexthop'] + ":" + route['destination']


class SecurityGroup(NeutronAPIDictWrapper):
    # Required attributes: id, name, description, tenant_id, rules

    def __init__(self, sg, sg_dict=None):
        if sg_dict is None:
            sg_dict = {sg['id']: sg['name']}
        if 'security_group_rules' not in sg:
            sg['security_group_rules'] = []
        sg['rules'] = [SecurityGroupRule(rule, sg_dict)
                       for rule in sg['security_group_rules']]
        super().__init__(sg)

    def to_dict(self):
        return {k: self._apidict[k] for k in self._apidict if k != 'rules'}


class SecurityGroupRule(NeutronAPIDictWrapper):
    # Required attributes:
    #   id, parent_group_id
    #   ip_protocol, from_port, to_port, ip_range, group
    #   ethertype, direction (Neutron specific)

    def _get_secgroup_name(self, sg_id, sg_dict):
        if not sg_id:
            return ''

        if sg_dict is None:
            sg_dict = {}
        # If sg name not found in sg_dict,
        # first two parts of UUID is used as sg name.
        return sg_dict.get(sg_id, sg_id[:13])

    def __init__(self, sgr, sg_dict=None):
        # In Neutron, if both remote_ip_prefix and remote_group_id are None,
        # it means all remote IP range is allowed, i.e., 0.0.0.0/0 or ::/0.
        if not sgr['remote_ip_prefix'] and not sgr['remote_group_id']:
            if sgr['ethertype'] == 'IPv6':
                sgr['remote_ip_prefix'] = '::/0'
            else:
                sgr['remote_ip_prefix'] = '0.0.0.0/0'

        ethertype = ''
        if 'ethertype' in sgr:
            ethertype = sgr['ethertype']
        else:
            ethertype = sgr['ether_type']
        rule = {
            'id': sgr['id'],
            'parent_group_id': sgr['security_group_id'],
            'direction': sgr['direction'],
            'ethertype': ethertype,
            'ip_protocol': sgr['protocol'],
            'from_port': sgr['port_range_min'],
            'to_port': sgr['port_range_max'],
            'description': sgr.get('description', '')
        }
        cidr = sgr['remote_ip_prefix']
        rule['ip_range'] = {'cidr': cidr} if cidr else {}
        group = self._get_secgroup_name(sgr['remote_group_id'], sg_dict)
        rule['group'] = {'name': group} if group else {}
        super().__init__(rule)

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

        return (_('ALLOW %(ether_type)s %(proto_port)s '
                  '%(direction)s %(remote)s') %
                {'ether_type': self.ethertype,
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
    * shared: A boolean indicates whether this security group is shared
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
        self.net_client = networkclient(request)

    def _list(self, **filters):
        if (filters.get("tenant_id") and
                is_extension_supported(
                    self.request, 'security-groups-shared-filtering')):
            # NOTE(hangyang): First, we get the SGs owned by but not shared
            # to the requester(tenant_id)
            filters["is_shared"] = False
            secgroups_owned = self.net_client.security_groups(**filters)
            # NOTE(hangyang): Second, we get the SGs shared to the
            # requester. For a requester with an admin role, this second
            # API call also only returns SGs shared to the requester's tenant
            # instead of all the SGs shared to any tenant.
            filters.pop("tenant_id")
            filters["is_shared"] = True
            secgroups_rbac = self.net_client.security_groups(**filters)

            def _filter_sgs(all_sgs):
                already_found = set()
                for sg in all_sgs:
                    if sg.id not in already_found:
                        already_found.add(sg.id)
                        yield sg

            filtered_list = []
            for sg in _filter_sgs(
                    itertools.chain(secgroups_owned, secgroups_rbac)):
                filtered_list.append(sg)
            return [SecurityGroup(sg.to_dict()) for sg in filtered_list]

        secgroups = self.net_client.security_groups(**filters)
        return [SecurityGroup(sg.to_dict()) for sg in secgroups]

    @profiler.trace
    def list(self, **params):
        """Fetches a list all security groups.

        :returns: List of SecurityGroup objects
        """
        # This is to ensure tenant_id key is not populated
        # if tenant_id=None is specified.
        tenant_id = params.pop('tenant_id', self.request.user.tenant_id)
        if tenant_id:
            params['tenant_id'] = tenant_id
        return self._list(**params)

    def _sg_name_dict(self, sg_id, rules):
        """Create a mapping dict from secgroup id to its name."""
        related_ids = set([sg_id])
        related_ids |= set(filter(None, [r['remote_group_id'] for r in rules]))
        related_sgs = self.net_client.security_groups(id=related_ids,
                                                      fields=['id', 'name'])
        return dict((sg.to_dict()['id'], sg.to_dict()['name'])
                    for sg in related_sgs)

    @profiler.trace
    def get(self, sg_id):
        """Fetches the security group.

        :returns: SecurityGroup object corresponding to sg_id
        """
        secgroup = self.net_client.get_security_group(sg_id).to_dict()
        sg_dict = self._sg_name_dict(sg_id, secgroup['security_group_rules'])
        return SecurityGroup(secgroup, sg_dict)

    @profiler.trace
    def create(self, name, desc):
        """Create a new security group.

        :returns: SecurityGroup object created
        """
        body = {'name': name, 'description': desc,
                'tenant_id': self.request.user.project_id}
        secgroup = self.net_client.create_security_group(**body).to_dict()
        return SecurityGroup(secgroup)

    @profiler.trace
    def update(self, sg_id, name, desc):
        body = {'name': name, 'description': desc}
        secgroup = self.net_client.update_security_group(
            sg_id, **body).to_dict()
        return SecurityGroup(secgroup)

    @profiler.trace
    def delete(self, sg_id):
        """Delete the specified security group."""
        self.net_client.delete_security_group(sg_id)

    @profiler.trace
    def rule_create(self, parent_group_id,
                    direction=None, ethertype=None,
                    ip_protocol=None, from_port=None, to_port=None,
                    cidr=None, group_id=None, description=None):
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
        if isinstance(from_port, int) and from_port < 0:
            from_port = None
        if isinstance(to_port, int) and to_port < 0:
            to_port = None
        if isinstance(ip_protocol, int) and ip_protocol < 0:
            ip_protocol = None

        params = {'security_group_id': parent_group_id,
                  'direction': direction,
                  'ethertype': ethertype,
                  'protocol': ip_protocol,
                  'port_range_min': from_port,
                  'port_range_max': to_port,
                  'remote_ip_prefix': cidr,
                  'remote_group_id': group_id}
        if description is not None:
            params['description'] = description
        try:
            rule = self.net_client.create_security_group_rule(
                **params).to_dict()
        except neutron_exc.OverQuotaClient:
            raise exceptions.Conflict(
                _('Security group rule quota exceeded.'))
        except neutron_exc.Conflict:
            raise exceptions.Conflict(
                _('Security group rule already exists.'))
        sg_dict = self._sg_name_dict(parent_group_id, [rule])
        return SecurityGroupRule(rule, sg_dict)

    @profiler.trace
    def rule_delete(self, sgr_id):
        """Delete the specified security group rule."""
        self.net_client.delete_security_group_rule(sgr_id)

    @profiler.trace
    def list_by_instance(self, instance_id):
        """Gets security groups of an instance.

        :returns: List of SecurityGroup objects associated with the instance
        """
        ports = port_list(self.request, device_id=instance_id)
        sg_ids = []
        for p in ports:
            sg_ids += p.security_group_ids
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
              'instance_type', 'pool', 'dns_domain', 'dns_name',
              'port_forwardings']

    def __init__(self, fip):
        fip['ip'] = fip['floating_ip_address']
        fip['fixed_ip'] = fip['fixed_ip_address']
        fip['pool'] = fip['floating_network_id']
        fip['port_forwardings'] = fip.get('portforwardings', {})
        super().__init__(fip)


class PortForwarding(base.APIDictWrapper):
    _attrs = ['id', 'floating_ip_id', 'protocol', 'internal_port_range',
              'external_port_range', 'internal_ip_address',
              'description', 'internal_port_id', 'external_ip_address']

    def __init__(self, pfw, fip):
        pfw['floatingip_id'] = fip
        port_forwarding = pfw
        if 'port_forwarding' in pfw:
            port_forwarding = pfw['port_forwarding']
        port_forwarding['internal_port_range'] = ':'.join(
            map(str, sorted(
                map(int, set(port_forwarding.get(
                    'internal_port_range', '').split(':'))))))
        port_forwarding['external_port_range'] = ':'.join(
            map(str, sorted(
                map(int, set(port_forwarding.get(
                    'external_port_range', '').split(':'))))))
        super().__init__(pfw)


class FloatingIpPool(base.APIDictWrapper):
    pass


class FloatingIpTarget(base.APIDictWrapper):
    """Representation of floating IP association target.

    The following parameter needs to be passed when instantiating the class:

    :param port: ``Port`` object which represents a neutron port.
    :param ip_address: IP address of the ``port``. It must be one of
        IP address of a given port.
    :param label: String displayed in the floating IP association form.
        IP address will be appended to a specified label. (Optional)
    """

    def __init__(self, port, ip_address, label=None):
        name = '%s: %s' % (label, ip_address) if label else ip_address
        target = {'name': name,
                  'id': '%s_%s' % (port.id, ip_address),
                  'port_id': port.id,
                  'instance_id': port.device_id}
        super().__init__(target)


class PortForwardingManager(object):

    def __init__(self, request):
        self.request = request
        self.net_client = networkclient(request)

    @profiler.trace
    def list(self, floating_ip_id, **search_opts):
        port_forwarding_rules = self.net_client.port_forwardings(
            floating_ip_id, **search_opts)
        LOG.debug("Portforwarding rules listed=%s", port_forwarding_rules)
        return [PortForwarding(port_forwarding_rule.to_dict(), floating_ip_id)
                for port_forwarding_rule in port_forwarding_rules]

    @profiler.trace
    def update(self, floating_ip_id, **params):
        portforwarding_dict = self.create_port_forwarding_dict(**params)
        portforwarding_id = params['portforwarding_id']
        LOG.debug("Updating Portforwarding rule with id %s", portforwarding_id)
        pfw = self.net_client.update_port_forwarding(
            floating_ip_id,
            portforwarding_id,
            **portforwarding_dict).to_dict()

        return PortForwarding(pfw, floating_ip_id)

    @profiler.trace
    def create(self, floating_ip_id, **params):
        portforwarding_dict = self.create_port_forwarding_dict(**params)
        portforwarding_rule = self.net_client.create_port_forwarding(
            floating_ip_id, **portforwarding_dict).to_dict()
        LOG.debug("Created a Portforwarding rule to floating IP %s with id %s",
                  floating_ip_id,
                  portforwarding_rule['id'])
        return PortForwarding(portforwarding_rule, floating_ip_id)

    def create_port_forwarding_dict(self, **params):
        portforwarding_dict = {}
        if 'protocol' in params:
            portforwarding_dict['protocol'] = str(params['protocol']).lower()
        if 'internal_port' in params:
            internal_port = str(params['internal_port'])
            if ':' not in internal_port:
                portforwarding_dict['internal_port'] = int(internal_port)
            else:
                portforwarding_dict['internal_port_range'] = internal_port
        if 'external_port' in params:
            external_port = str(params['external_port'])
            if ':' not in external_port:
                portforwarding_dict['external_port'] = int(external_port)
            else:
                portforwarding_dict['external_port_range'] = external_port
        if 'internal_ip_address' in params:
            portforwarding_dict['internal_ip_address'] = params[
                'internal_ip_address']
        if 'description' in params:
            portforwarding_dict['description'] = params['description']
        if 'internal_port_id' in params:
            portforwarding_dict['internal_port_id'] = params['internal_port_id']
        return portforwarding_dict

    def delete(self, floating_ip_id, portforwarding_id):
        self.net_client.delete_port_forwarding(
            floating_ip_id, portforwarding_id)
        LOG.debug(
            "The Portforwarding rule of floating IP %s with id %s was deleted",
            floating_ip_id, portforwarding_id)

    def get(self, floating_ip_id, portforwarding_id):
        pfw = self.net_client.get_port_forwarding(floating_ip_id,
                                                  portforwarding_id).to_dict()
        return PortForwarding(pfw, floating_ip_id)


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
    }

    def __init__(self, request):
        self.request = request
        self.net_client = networkclient(request)

    @profiler.trace
    def list_pools(self):
        """Fetches a list of all floating IP pools.

        :returns: List of FloatingIpPool objects
        """
        search_opts = {'router:external': True}
        return [FloatingIpPool(pool) for pool
                in self.net_client.networks(**search_opts)]

    def _get_instance_type_from_device_owner(self, device_owner):
        for key, value in self.device_owner_map.items():
            if device_owner.startswith(key):
                return value
        return device_owner

    def _set_fip_details(self, fip, port):
        try:
            if not port:
                port = port_get(self.request, fip['port_id'])
            fip['instance_id'] = port.device_id
            fip['instance_type'] = self._get_instance_type_from_device_owner(
                port.device_owner)
        except sdk_exceptions.ResourceNotFound:
            LOG.debug("Failed to get port %s details for floating IP %s",
                      fip['port_id'], fip['ip'])
            fip['instance_id'] = None
            fip['instance_type'] = None

    def _set_instance_info(self, fip, port=None):
        if fip['port_id']:
            self._set_fip_details(fip, port)
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
        fips = list(self.net_client.ips(**search_opts))
        # Get port list to add instance_id to floating IP list
        # instance_id is stored in device_id attribute
        ports = port_list(self.request, **port_search_opts)
        port_dict = collections.OrderedDict([(p['id'], p) for p in ports])
        fips_list = []
        for fip in fips:
            fips_list.append(fip.to_dict())
        for fip in fips_list:
            self._set_instance_info(fip, port_dict.get(fip['port_id']))
        return [FloatingIp(fip) for fip in fips_list]

    @profiler.trace
    def get(self, floating_ip_id):
        """Fetches the floating IP.

        :returns: FloatingIp object corresponding to floating_ip_id
        """
        fip = self.net_client.get_ip(floating_ip_id).to_dict()
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
        if 'description' in params:
            create_dict['description'] = params['description']
        if 'dns_domain' in params:
            create_dict['dns_domain'] = params['dns_domain']
        if 'dns_name' in params:
            create_dict['dns_name'] = params['dns_name']
        fip = self.net_client.create_ip(**create_dict).to_dict()
        self._set_instance_info(fip)
        fip_class = FloatingIp(fip)
        return fip_class

    @profiler.trace
    def release(self, floating_ip_id):
        """Releases a floating IP specified."""
        self.net_client.delete_ip(floating_ip_id)

    @profiler.trace
    def associate(self, floating_ip_id, port_id):
        """Associates the floating IP to the port.

        ``port_id`` represents a VNIC of an instance.
        ``port_id`` argument is different from a normal neutron port ID.
        A value passed as ``port_id`` must be one of target_id returned by
        ``list_targets`` or ``list_targets_by_instance`` method.
        """
        # NOTE: In Neutron Horizon floating IP support, port_id is
        # "<port_id>_<ip_address>" format to identify multiple ports.
        pid, ip_address = port_id.split('_', 1)
        update_dict = {'port_id': pid,
                       'fixed_ip_address': ip_address}
        self.net_client.update_ip(floating_ip_id, **update_dict)

    @profiler.trace
    def disassociate(self, floating_ip_id):
        """Disassociates the floating IP specified."""
        update_dict = {'port_id': None}
        self.net_client.update_ip(floating_ip_id, **update_dict)

    def _get_reachable_subnets(self, ports, fetch_router_ports=False):
        if not is_enabled_by_config('enable_fip_topology_check'):
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
        if fetch_router_ports:
            router_ports = port_list(self.request,
                                     device_owner=ROUTER_INTERFACE_OWNERS)
        else:
            router_ports = [p for p in ports
                            if p.device_owner in ROUTER_INTERFACE_OWNERS]
        reachable_subnets = set(p.fixed_ips[0]['subnet_id']
                                for p in router_ports
                                if p.device_id in gw_routers)
        # we have to include any shared subnets as well because we may not
        # have permission to see the router interface to infer connectivity
        shared = set(s.id for n in network_list(self.request, is_shared=True)
                     for s in n['subnets'])
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
                # Floating IPs can only target IPv4 addresses.
                if netaddr.IPAddress(ip['ip_address']).version != 4:
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
    def list_targets_by_instance(self, instance_id, target_list=None):
        """Returns a list of FloatingIpTarget objects of FIP association.

        :param instance_id: ID of target VM instance
        :param target_list: (optional) a list returned by list_targets().
            If specified, looking up is done against the specified list
            to save extra API calls to a back-end. Otherwise target list
            is retrieved from a back-end inside the method.
        """
        if target_list is not None:
            # We assume that target_list was returned by list_targets()
            # so we can assume checks for subnet reachability and IP version
            # have been done already. We skip all checks here.
            return [target for target in target_list
                    if target['instance_id'] == instance_id]

        ports = self._target_ports_by_instance(instance_id)
        reachable_subnets = self._get_reachable_subnets(
            ports, fetch_router_ports=True)
        name = self._get_server_name(instance_id)
        targets = []
        for p in ports:
            for ip in p.fixed_ips:
                if ip['subnet_id'] not in reachable_subnets:
                    continue
                # Floating IPs can only target IPv4 addresses.
                if netaddr.IPAddress(ip['ip_address']).version != 4:
                    continue
                targets.append(FloatingIpTarget(p, ip['ip_address'], name))
        return targets

    def _get_server_name(self, server_id):
        try:
            server = nova.server_get(self.request, server_id)
            return server.name
        except nova_exc.NotFound:
            return ''

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
        return setting_utils.get_dict_config(
            'OPENSTACK_NEUTRON_NETWORK', 'enable_router')


def get_ipver_str(ip_version):
    """Convert an ip version number to a human-friendly string."""
    return IP_VERSION_DICT.get(ip_version, '')


def get_auth_params_from_request(request):
    return (
        request.user.token.id,
        base.url_for(request, 'network'),
        base.url_for(request, 'identity')
    )


@memoized
def neutronclient(request):
    token_id, neutron_url, auth_url = get_auth_params_from_request(request)
    insecure = settings.OPENSTACK_SSL_NO_VERIFY
    cacert = settings.OPENSTACK_SSL_CACERT
    c = neutron_client.Client(token=token_id,
                              auth_url=auth_url,
                              endpoint_url=neutron_url,
                              insecure=insecure, ca_cert=cacert)
    return c


@memoized
def networkclient(request):
    token_id, neutron_url, auth_url = get_auth_params_from_request(request)

    insecure = settings.OPENSTACK_SSL_NO_VERIFY
    cacert = settings.OPENSTACK_SSL_CACERT
    verify = cacert if not insecure else False

    token_auth = token_endpoint.Token(
        endpoint=neutron_url,
        token=token_id)
    k_session = session.Session(
        auth=token_auth,
        original_ip=auth_utils.get_client_ip(request),
        verify=verify,
        # TODO(lajoskatona): cert should be None of a tuple in the form of
        # (cert, key).
        # In a devstack with enable_service tls-proxy:
        # cert=('/path/to/devstack-cert.crt', '/path/to/devstack-cert.key')
        # For this new horizon cfg option should be added.
    )
    c = openstack.connection.Connection(
        session=k_session,
        region_name=request.user.services_region,
        app_name='horizon', app_version='1.0'
    )
    return c.network


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

        if isinstance(filter_values, str):
            filter_values = [filter_values]
        elif not isinstance(filter_values, Sequence):
            filter_values = list(filter_values)

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
def trunk_show(request, trunk_id):
    LOG.debug("trunk_show(): trunk_id=%s", trunk_id)
    trunk = networkclient(request).get_trunk(trunk_id)
    return Trunk(trunk.to_dict())


@profiler.trace
def trunk_list(request, **params):
    LOG.debug("trunk_list(): params=%s", params)
    trunks = networkclient(request).trunks(**params)
    if not isinstance(trunks, (types.GeneratorType, list)):
        trunks = [trunks]
    return [Trunk(t.to_dict()) for t in trunks]


@profiler.trace
def trunk_create(request, **params):
    LOG.debug("trunk_create(): params=%s", params)
    if 'project_id' not in params:
        params['project_id'] = request.user.project_id
    trunk = networkclient(request).create_trunk(**params).to_dict()
    return Trunk(trunk)


@profiler.trace
def trunk_delete(request, trunk_id):
    LOG.debug("trunk_delete(): trunk_id=%s", trunk_id)
    networkclient(request).delete_trunk(trunk_id)


def _prepare_body_remove_subports(subports):
    """Prepare body for PUT /v2.0/trunks/TRUNK_ID/remove_subports."""
    return [{'port_id': sp['port_id']} for sp in subports]


@profiler.trace
def trunk_update(request, trunk_id, old_trunk, new_trunk):
    """Handle update to a trunk in (at most) three neutron calls.

    The JavaScript side should know only about the old and new state of a
    trunk. However it should not know anything about how the old and new are
    meant to be diffed and sent to neutron. We handle that here.

    This code was adapted from Heat, see: https://review.opendev.org/442496

    Call #1) Update all changed properties but 'sub_ports'.
        PUT /v2.0/trunks/TRUNK_ID
        openstack network trunk set

    Call #2) Delete subports not needed anymore.
        PUT /v2.0/trunks/TRUNK_ID/remove_subports
        openstack network trunk unset --subport

    Call #3) Create new subports.
        PUT /v2.0/trunks/TRUNK_ID/add_subports
        openstack network trunk set --subport

    A single neutron port cannot be two subports at the same time (ie.
    have two segmentation (type, ID)s on the same trunk or to belong to
    two trunks). Therefore we have to delete old subports before creating
    new ones to avoid conflicts.
    """
    LOG.debug("trunk_update(): trunk_id=%s", trunk_id)

    # NOTE(bence romsics): We want to do set operations on the subports,
    # however we receive subports represented as dicts. In Python
    # mutable objects like dicts are not hashable so they cannot be
    # inserted into sets. So we convert subport dicts to (immutable)
    # frozensets in order to do the set operations.
    def dict2frozenset(d):
        """Convert a dict to a frozenset.

        Create an immutable equivalent of a dict, so it's hashable
        therefore can be used as an element of a set or a key of another
        dictionary.
        """
        return frozenset(d.items())

    # cf. neutron_lib/api/definitions/trunk.py
    updatable_props = ('is_admin_state_up', 'description', 'name')
    prop_diff = {
        k: new_trunk[k]
        for k in updatable_props
        if old_trunk[k] != new_trunk[k]}

    subports_old = {dict2frozenset(d): d
                    for d in old_trunk.get('sub_ports', [])}
    subports_new = {dict2frozenset(d): d
                    for d in new_trunk.get('sub_ports', [])}

    old_set = set(subports_old.keys())
    new_set = set(subports_new.keys())

    delete = old_set - new_set
    create = new_set - old_set

    dicts_delete = [subports_old[fs] for fs in delete]
    dicts_create = [subports_new[fs] for fs in create]

    trunk = old_trunk
    if prop_diff:
        LOG.debug('trunk_update(): update properties of trunk %s: %s',
                  trunk_id, prop_diff)
        trunk = networkclient(request).update_trunk(
            trunk_id, **prop_diff)

    if dicts_delete:
        LOG.debug('trunk_update(): delete subports of trunk %s: %s',
                  trunk_id, dicts_delete)
        body = _prepare_body_remove_subports(dicts_delete)
        trunk = networkclient(request).delete_trunk_subports(
            trunk_id, body)

    if dicts_create:
        LOG.debug('trunk_update(): create subports of trunk %s: %s',
                  trunk_id, dicts_create)
        trunk = networkclient(request).add_trunk_subports(
            trunk_id, dicts_create)

    return Trunk(trunk.to_dict())


@profiler.trace
def network_list_paged(request, page_data, **params):
    page_data, marker_net = _configure_pagination(request, params, page_data)
    query_kwargs = {
        'request': request,
        'page_data': page_data,
        'params': params,
    }
    return _perform_query(_network_list_paged, query_kwargs, marker_net)


def _network_list_paged(request, page_data, params):
    nets = network_list(
        request, single_page=page_data['single_page'], **params)
    return update_pagination(nets, page_data)


@profiler.trace
def network_list(request, single_page=False, **params):
    LOG.debug("network_list(): params=%s", params)
    list_values = []
    if 'id' in params and isinstance(params['id'], frozenset):
        list_values = list(params['id'])
    if 'id' in params and isinstance(params['id'], list):
        list_values = params['id']
    if single_page is True:
        params['retrieve_all'] = False

    networks = []
    if 'tenant_id' in params:
        params['project_id'] = params.pop('tenant_id')
    for value in list_values:
        params['id'] = value
        for net in networkclient(request).networks(**params):
            networks.append(net)
    if not list_values:
        networks = networkclient(request).networks(**params)

    # Get subnet list to expand subnet info in network list.
    subnets = subnet_list(request)
    subnet_dict = dict((s['id'], s) for s in subnets)

    if not isinstance(networks, (list, types.GeneratorType)):
        networks = [networks]
    nets_with_subnet = []
    net_ids = set()

    # Expand subnet list from subnet_id to values.
    subnet_l_ready = False
    runs = 0
    max_runs = 3
    while not subnet_l_ready and runs < max_runs:
        networks, cp_nets = itertools.tee(networks, 2)
        try:
            for n in cp_nets:
                # Due to potential timing issues, we can't assume the
                # subnet_dict data is in sync with the network data.
                net_dict = n.to_dict()
                net_dict['subnets'] = [
                    subnet_dict[s] for s in net_dict.get('subnet_ids', [])
                    if s in subnet_dict
                ]
                if net_dict['id'] not in net_ids:
                    nets_with_subnet.append(net_dict)
                    net_ids.add(net_dict['id'])
            subnet_l_ready = True
        except (requests.exceptions.SSLError, ks_exceptions.SSLError):
            LOG.warning('Retry due to SSLError')
            runs += 1
            continue
    return [Network(n) for n in nets_with_subnet]


def _is_auto_allocated_network_supported(request):
    try:
        neutron_auto_supported = is_service_enabled(
            request, 'enable_auto_allocated_network',
            'auto-allocated-topology')
    except Exception:
        exceptions.handle(request, _('Failed to check if neutron supports '
                                     '"auto_allocated_network".'))
        neutron_auto_supported = False
    if not neutron_auto_supported:
        return False

    try:
        # server_create needs to support both features,
        # so we need to pass both features here.
        nova_auto_supported = nova.is_feature_available(
            request, ("instance_description",
                      "auto_allocated_network"))
    except Exception:
        exceptions.handle(request, _('Failed to check if nova supports '
                                     '"auto_allocated_network".'))
        nova_auto_supported = False

    return nova_auto_supported


# TODO(ganso): consolidate this function with cinder's and nova's
@profiler.trace
def update_pagination(entities, page_data):

    has_more_data, has_prev_data = False, False

    # single_page=True is actually to have pagination enabled
    if page_data.get('single_page') is not True:
        return entities, has_more_data, has_prev_data

    if len(entities) > page_data['page_size']:
        has_more_data = True
        entities.pop()
        if page_data.get('marker_id') is not None:
            has_prev_data = True

    # first page condition when reached via prev back
    elif (page_data.get('sort_dir') == 'desc' and
          page_data.get('marker_id') is not None):
        has_more_data = True

    # last page condition
    elif page_data.get('marker_id') is not None:
        has_prev_data = True

    # reverse to maintain same order when going backwards
    if page_data.get('sort_dir') == 'desc':
        entities.reverse()

    return entities, has_more_data, has_prev_data


def _add_to_nets_and_return(
        nets, obtained_nets, page_data, filter_tenant_id=None):
    # remove project non-shared external nets that should
    # be retrieved by project query
    if filter_tenant_id:
        obtained_nets = [net for net in obtained_nets
                         if net['tenant_id'] != filter_tenant_id]

    if (page_data['single_page'] is True and
            len(obtained_nets) + len(nets) > page_data['limit']):
        # we need to trim results if we already surpassed the limit
        # we use limit so we can call update_pagination
        cut = page_data['limit'] - (len(obtained_nets) + len(nets))
        nets += obtained_nets[0:cut]
        return True
    nets += obtained_nets
    # we don't need to perform more queries if we already have enough nets
    if page_data['single_page'] is True and len(nets) == page_data['limit']:
        return True
    return False


def _query_external_nets(request, include_external, page_data, **params):

    # If the external filter is set to False we don't need to perform this
    # query
    # If the shared filter is set to True we don't need to perform this
    # query (already retrieved)
    # We are either paginating external nets or not pending more data
    if (page_data['filter_external'] is not False and include_external and
            page_data['filter_shared'] is not True and
            page_data.get('marker_type') in (None, 'ext')):

        # Grab only all external non-shared networks
        params['router:external'] = True
        params['shared'] = False

        return _perform_net_query(request, {}, page_data, 'ext', **params)

    return []


def _query_shared_nets(request, page_data, **params):

    # If the shared filter is set to False we don't need to perform this query
    # We are either paginating shared nets or not pending more data
    if (page_data['filter_shared'] is not False and
            page_data.get('marker_type') in (None, 'shr')):

        if page_data['filter_external'] is None:
            params.pop('router:external', None)
        else:
            params['router:external'] = page_data['filter_external']

        # Grab only all shared networks
        # May include shared external nets based on external filter
        params['shared'] = True

        return _perform_net_query(request, {}, page_data, 'shr', **params)

    return []


def _query_project_nets(request, tenant_id, page_data, **params):

    # We don't need to run this query if shared filter is True, as the networks
    # will be retrieved by another query
    # We are either paginating project nets or not pending more data
    if (page_data['filter_shared'] is not True and
            page_data.get('marker_type') in (None, 'proj')):

        # Grab only non-shared project networks
        # May include non-shared project external nets based on external filter
        if page_data['filter_external'] is None:
            params.pop('router:external', None)
        else:
            params['router:external'] = page_data['filter_external']
        params['shared'] = False

        return _perform_net_query(
            request, {'tenant_id': tenant_id}, page_data, 'proj', **params)

    return []


def _perform_net_query(
        request, extra_param, page_data, query_marker_type, **params):
    copy_req_params = copy.deepcopy(params)
    copy_req_params.update(extra_param)
    if page_data.get('marker_type') == query_marker_type:
        copy_req_params['marker'] = page_data['marker_id']
        # We clear the marker type to allow for other queries if
        # this one does not fill up the page
        page_data['marker_type'] = None
    return network_list(
        request, single_page=page_data['single_page'], **copy_req_params)


def _query_nets_for_tenant(request, include_external, tenant_id, page_data,
                           **params):

    # Save variables
    page_data['filter_external'] = params.get('router:external')
    page_data['filter_shared'] = params.get('shared')

    nets = []

    # inverted direction (for prev page)
    if (page_data.get('single_page') is True and
            page_data.get('sort_dir') == 'desc'):

        ext_nets = _query_external_nets(
            request, include_external, page_data, **params)
        if _add_to_nets_and_return(
                nets, ext_nets, page_data, filter_tenant_id=tenant_id):
            return update_pagination(nets, page_data)

        proj_nets = _query_project_nets(
            request, tenant_id, page_data, **params)
        if _add_to_nets_and_return(nets, proj_nets, page_data):
            return update_pagination(nets, page_data)

        shr_nets = _query_shared_nets(
            request, page_data, **params)
        if _add_to_nets_and_return(nets, shr_nets, page_data):
            return update_pagination(nets, page_data)

    # normal direction (for next page)
    else:
        shr_nets = _query_shared_nets(
            request, page_data, **params)
        if _add_to_nets_and_return(nets, shr_nets, page_data):
            return update_pagination(nets, page_data)

        proj_nets = _query_project_nets(
            request, tenant_id, page_data, **params)
        if _add_to_nets_and_return(nets, proj_nets, page_data):
            return update_pagination(nets, page_data)

        ext_nets = _query_external_nets(
            request, include_external, page_data, **params)
        if _add_to_nets_and_return(
                nets, ext_nets, page_data, filter_tenant_id=tenant_id):
            return update_pagination(nets, page_data)

    return update_pagination(nets, page_data)


def _configure_marker_type(marker_net, tenant_id=None):
    if marker_net:
        if marker_net['is_shared'] is True:
            return 'shr'
        if (marker_net['is_router_external'] is True and
                marker_net['tenant_id'] != tenant_id):
            return 'ext'
        return 'proj'
    return None


def _reverse_page_order(sort_dir):
    if sort_dir == 'asc':
        return 'desc'
    return 'asc'


def _configure_pagination(request, params, page_data=None, tenant_id=None):

    marker_net = None
    # "single_page" is a neutron API parameter to disable automatic
    # pagination done by the API. If it is False, it returns all the
    # results. If page_data param is not present, the method is being
    # called by someone that does not want/expect pagination.
    if page_data is None:
        page_data = {'single_page': False}
    else:
        page_data['single_page'] = True
        if page_data['marker_id']:
            # this next request is inefficient, but the alternative is for
            # the UI to send the extra parameters in the request,
            # maybe a future optimization
            marker_net = network_get(request, page_data['marker_id'])
            page_data['marker_type'] = _configure_marker_type(
                marker_net, tenant_id=tenant_id)
        else:
            page_data['marker_type'] = None

        # we query one more than we are actually displaying due to
        # consistent pagination hack logic used in other services
        page_data['page_size'] = setting_utils.get_page_size(request)
        page_data['limit'] = page_data['page_size'] + 1
        params['limit'] = page_data['limit']

        # Neutron API sort direction is inverted compared to other services
        page_data['sort_dir'] = page_data.get('sort_dir', "desc")
        page_data['sort_dir'] = _reverse_page_order(page_data['sort_dir'])

        # params are included in the request to the neutron API
        params['sort_dir'] = page_data['sort_dir']
        params['sort_key'] = 'id'

    return page_data, marker_net


def _perform_query(
        query_func, query_kwargs, marker_net, include_pre_auto_allocate=False):
    networks, has_more_data, has_prev_data = query_func(**query_kwargs)

    # Hack for auto allocated network
    if include_pre_auto_allocate and not networks:
        if _is_auto_allocated_network_supported(query_kwargs['request']):
            networks.append(PreAutoAllocateNetwork(query_kwargs['request']))

    # no pagination case, single_page=True means pagination is enabled
    if query_kwargs['page_data'].get('single_page') is not True:
        return networks

    # handle case of full page deletes
    deleted = query_kwargs['request'].session.pop('network_deleted', None)
    if deleted and marker_net:

        # contents of last page deleted, invert order, load previous page
        # based on marker (which ends up not included), remove head and add
        # marker at the end. Since it is the last page, also force
        # has_more_data to False because the marker item would always be
        # the "more_data" of the request.
        # we do this only if there are no elements to be displayed
        if ((networks is None or len(networks) == 0) and
                has_prev_data and not has_more_data and
                query_kwargs['page_data']['sort_dir'] == 'asc'):
            # admin section params
            if 'params' in query_kwargs:
                query_kwargs['params']['sort_dir'] = 'desc'
            else:
                query_kwargs['page_data']['marker_type'] = (
                    _configure_marker_type(marker_net,
                                           query_kwargs.get('tenant_id')))
                query_kwargs['sort_dir'] = 'desc'
            query_kwargs['page_data']['sort_dir'] = 'desc'
            networks, has_more_data, has_prev_data = (
                query_func(**query_kwargs))
            if networks:
                if has_prev_data:
                    # if we are back in the first page, we don't remove head
                    networks.pop(0)
                networks.append(marker_net)
                has_more_data = False

        # contents of first page deleted (loaded by prev), invert order
        # and remove marker as if the section was loaded for the first time
        # we do this regardless of number of elements in the first page
        elif (has_more_data and not has_prev_data and
                query_kwargs['page_data']['sort_dir'] == 'desc'):
            query_kwargs['page_data']['sort_dir'] = 'asc'
            query_kwargs['page_data']['marker_id'] = None
            query_kwargs['page_data']['marker_type'] = None
            # admin section params
            if 'params' in query_kwargs:
                if 'marker' in query_kwargs['params']:
                    del query_kwargs['params']['marker']
                query_kwargs['params']['sort_dir'] = 'asc'
            else:
                query_kwargs['sort_dir'] = 'asc'
            networks, has_more_data, has_prev_data = (
                query_func(**query_kwargs))

    return networks, has_more_data, has_prev_data


@profiler.trace
def network_list_for_tenant(request, tenant_id, include_external=False,
                            include_pre_auto_allocate=False, page_data=None,
                            **params):
    """Return a network list available for the tenant.

    The list contains networks owned by the tenant and public networks.
    If requested_networks specified, it searches requested_networks only.

    page_data parameter format:

    page_data = {
        'marker_id': '<id>',
        'sort_dir': '<desc(next)|asc(prev)>'
    }

    """

    # Pagination is implemented consistently with nova and cinder views,
    # which means it is a bit hacky:
    # - it requests X units but displays X-1 units
    # - it ignores the marker metadata from the API response and uses its own
    # Here we have extra hacks on top of that, because we have to merge the
    # results of 3 different queries, and decide which one of them we are
    # actually paginating.
    # The 3 queries consist of:
    # 1. Shared=True networks
    # 2. Project non-shared networks
    # 3. External non-shared non-project networks
    # The main reason behind that order is to maintain the current behavior
    # for how external networks are retrieved and displayed.
    # The include_external assumption of whether external networks should be
    # displayed is "overridden" whenever the external network is shared or is
    # the tenant's. Therefore it refers to only non-shared non-tenant external
    # networks.
    # To accomplish pagination, we check the type of network the provided
    # marker is, to determine which query we have last run and whether we
    # need to paginate it.

    LOG.debug("network_list_for_tenant(): tenant_id=%(tenant_id)s, "
              "params=%(params)s, page_data=%(page_data)s", {
                  'tenant_id': tenant_id,
                  'params': params,
                  'page_data': page_data,
              })

    page_data, marker_net = _configure_pagination(
        request, params, page_data, tenant_id=tenant_id)

    query_kwargs = {
        'request': request,
        'include_external': include_external,
        'tenant_id': tenant_id,
        'page_data': page_data,
        **params,
    }

    return _perform_query(
        _query_nets_for_tenant, query_kwargs, marker_net,
        include_pre_auto_allocate)


@profiler.trace
def network_get(request, network_id, expand_subnet=True, **params):
    LOG.debug("network_get(): netid=%(network_id)s, params=%(params)s",
              {'network_id': network_id, 'params': params})
    network = networkclient(request).get_network(network_id,
                                                 **params).to_dict()
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
                                  for sid in network['subnet_ids']]
        except sdk_exceptions.ResourceNotFound:
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
    network = networkclient(request).create_network(**kwargs).to_dict()
    return Network(network)


@profiler.trace
def network_update(request, network_id, **kwargs):
    LOG.debug("network_update(): netid=%(network_id)s, params=%(params)s",
              {'network_id': network_id, 'params': kwargs})
    network = networkclient(request).update_network(network_id,
                                                    **kwargs).to_dict()
    return Network(network)


@profiler.trace
def network_delete(request, network_id):
    LOG.debug("network_delete(): netid=%s", network_id)
    networkclient(request).delete_network(network_id)
    request.session['network_deleted'] = network_id


@profiler.trace
@memoized
def subnet_list(request, **params):
    LOG.debug("subnet_list(): params=%s", params)
    subnets = networkclient(request).subnets(**params)
    ret_val = [Subnet(s.to_dict()) for s in subnets]
    return ret_val


@profiler.trace
def subnet_get(request, subnet_id, **params):
    LOG.debug("subnet_get(): subnetid=%(subnet_id)s, params=%(params)s",
              {'subnet_id': subnet_id, 'params': params})
    subnet = networkclient(request).get_subnet(subnet_id,
                                               **params).to_dict()
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
    body = {'network_id': network_id}
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body.update(kwargs)
    subnet = networkclient(request).create_subnet(**body).to_dict()
    return Subnet(subnet)


@profiler.trace
def subnet_update(request, subnet_id, **kwargs):
    LOG.debug("subnet_update(): subnetid=%(subnet_id)s, kwargs=%(kwargs)s",
              {'subnet_id': subnet_id, 'kwargs': kwargs})
    subnet = networkclient(request).update_subnet(subnet_id,
                                                  **kwargs).to_dict()
    return Subnet(subnet)


@profiler.trace
def subnet_delete(request, subnet_id):
    LOG.debug("subnet_delete(): subnetid=%s", subnet_id)
    networkclient(request).delete_subnet(subnet_id)


@profiler.trace
def subnetpool_list(request, **params):
    LOG.debug("subnetpool_list(): params=%s", params)
    subnetpools = networkclient(request).subnet_pools(**params)
    if not isinstance(subnetpools, (types.GeneratorType, list)):
        subnetpools = [subnetpools]
    return [SubnetPool(s.to_dict()) for s in subnetpools]


@profiler.trace
def subnetpool_get(request, subnetpool_id):
    LOG.debug("subnetpool_get(): subnetpoolid=%(subnetpool_id)s",
              {'subnetpool_id': subnetpool_id})
    subnetpool = networkclient(request).get_subnet_pool(subnetpool_id)
    return SubnetPool(subnetpool.to_dict())


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
    body = {'name': name,
            'prefixes': prefixes,
            }
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    body.update(kwargs)
    subnetpool = \
        networkclient(request).create_subnet_pool(**body)
    return SubnetPool(subnetpool.to_dict())


@profiler.trace
def subnetpool_update(request, subnetpool_id, **kwargs):
    LOG.debug("subnetpool_update(): subnetpoolid=%(subnetpool_id)s, "
              "kwargs=%(kwargs)s", {'subnetpool_id': subnetpool_id,
                                    'kwargs': kwargs})
    subnetpool = \
        networkclient(request).update_subnet_pool(subnetpool_id, **kwargs)
    return SubnetPool(subnetpool.to_dict())


@profiler.trace
def subnetpool_delete(request, subnetpool_id):
    LOG.debug("subnetpool_delete(): subnetpoolid=%s", subnetpool_id)
    return networkclient(request).delete_subnet_pool(subnetpool_id)


@profiler.trace
@memoized
def port_list(request, **params):
    LOG.debug("port_list(): params=%s", params)
    ports = networkclient(request).ports(**params)
    if not isinstance(ports, (types.GeneratorType, list)):
        ports = [ports]
    return [Port(p.to_dict()) for p in ports]


@profiler.trace
@memoized
def port_list_with_trunk_types(request, **params):
    """List neutron Ports for this tenant with possible TrunkPort indicated

    :param request: request context

    NOTE Performing two API calls is not atomic, but this is not worse
         than the original idea when we call port_list repeatedly for
         each network to perform identification run-time. We should
         handle the inconsistencies caused by non-atomic API requests
         gracefully.
    """
    LOG.debug("port_list_with_trunk_types(): params=%s", params)

    # When trunk feature is disabled in neutron, we have no need to fetch
    # trunk information and port_list() is enough.
    if not is_extension_supported(request, 'trunk'):
        return port_list(request, **params)

    ports = networkclient(request).ports(**params)
    trunk_filters = {}
    if 'tenant_id' in params:
        trunk_filters['tenant_id'] = params['tenant_id']
    trunks = networkclient(request).trunks(**trunk_filters)
    parent_ports = set(t['port_id'] for t in trunks)
    # Create a dict map for child ports (port ID to trunk info)
    child_ports = dict((s['port_id'],
                        {'trunk_id': t['id'],
                         'segmentation_type': s['segmentation_type'],
                         'segmentation_id': s['segmentation_id']})
                       for t in trunks
                       for s in t['sub_ports'])

    def _get_port_info(port):
        if port['id'] in parent_ports:
            return PortTrunkParent(port)
        if port['id'] in child_ports:
            return PortTrunkSubport(port, child_ports[port['id']])
        return Port(port)

    return [_get_port_info(p) for p in ports]


@profiler.trace
def port_get(request, port_id):
    LOG.debug("port_get(): portid=%(port_id)s", {'port_id': port_id})
    port = networkclient(request).get_port(port_id)
    return Port(port.to_dict())


def unescape_port_kwargs(**kwargs):
    keys = list(kwargs)
    for key in keys:
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
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    kwargs['network_id'] = network_id
    port = networkclient(request).create_port(**kwargs).to_dict()
    return Port(port)


@profiler.trace
def port_delete(request, port_id):
    LOG.debug("port_delete(): portid=%s", port_id)
    networkclient(request).delete_port(port_id)


@profiler.trace
def port_update(request, port_id, **kwargs):
    LOG.debug("port_update(): portid=%(port_id)s, kwargs=%(kwargs)s",
              {'port_id': port_id, 'kwargs': kwargs})
    kwargs = unescape_port_kwargs(**kwargs)
    port = networkclient(request).update_port(port_id, **kwargs).to_dict()
    return Port(port)


@profiler.trace
def router_create(request, **kwargs):
    LOG.debug("router_create():, kwargs=%s", kwargs)
    if 'tenant_id' not in kwargs:
        kwargs['tenant_id'] = request.user.project_id
    router = networkclient(request).create_router(**kwargs)
    return Router(router)


@profiler.trace
def router_update(request, r_id, **kwargs):
    LOG.debug("router_update(): router_id=%(r_id)s, kwargs=%(kwargs)s",
              {'r_id': r_id, 'kwargs': kwargs})
    router = networkclient(request).update_router(r_id, **kwargs).to_dict()
    return Router(router)


@profiler.trace
def router_get(request, router_id, **params):
    router = networkclient(request).get_router(router_id)
    return Router(router)


@profiler.trace
def router_list(request, **params):
    routers = networkclient(request).routers(**params)
    if not isinstance(routers, (types.GeneratorType, list)):
        routers = [routers]
    return [Router(r) for r in routers]


@profiler.trace
def router_list_on_l3_agent(request, l3_agent_id, **params):
    routers = networkclient(request).agent_hosted_routers(l3_agent_id,
                                                          **params)
    if not isinstance(routers, (types.GeneratorType, list)):
        routers = [routers]
    return [Router(r) for r in routers]


@profiler.trace
def router_delete(request, router_id):
    networkclient(request).delete_router(router_id)


@profiler.trace
def router_add_interface(request, router_id, subnet_id=None, port_id=None):
    client = networkclient(request)
    return client.add_interface_to_router(router=router_id,
                                          port_id=port_id,
                                          subnet_id=subnet_id)


@profiler.trace
def router_remove_interface(request, router_id, subnet_id=None, port_id=None):
    client = networkclient(request)
    return client.remove_interface_from_router(router=router_id,
                                               port_id=port_id,
                                               subnet_id=subnet_id)


@profiler.trace
def router_add_gateway(request, router_id, network_id, enable_snat=None):
    body = {'external_gateway_info': {'network_id': network_id}}
    if enable_snat is not None:
        body['external_gateway_info']['enable_snat'] = enable_snat
    networkclient(request).update_router(router_id, **body)


@profiler.trace
def router_remove_gateway(request, router_id):
    networkclient(request).update_router(router_id,
                                         **{'external_gateway_info': {}})


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
def tenant_quota_detail_get(request, tenant_id=None):
    tenant_id = tenant_id or request.user.tenant_id
    response = neutronclient(request).get('/quotas/%s/details' % tenant_id)
    return response['quota']


@profiler.trace
def default_quota_get(request, tenant_id=None):
    tenant_id = tenant_id or request.user.tenant_id
    response = neutronclient(request).show_quota_default(tenant_id)
    return base.QuotaSet(response['quota'])


@profiler.trace
def agent_list(request, **params):
    agents = networkclient(request).agents(**params)
    return [Agent(a.to_dict()) for a in agents]


@profiler.trace
def list_dhcp_agent_hosting_networks(request, network, **params):
    agents = networkclient(request).network_hosting_dhcp_agents(network,
                                                                **params)
    return [Agent(a.to_dict()) for a in agents]


@profiler.trace
def list_l3_agent_hosting_router(request, router, **params):
    agents = networkclient(request).routers_hosting_l3_agents(router,
                                                              **params)
    return [Agent(a.to_dict()) for a in agents]


@profiler.trace
def show_network_ip_availability(request, network_id):
    ip_availability = networkclient(request).get_network_ip_availability(
        network_id)
    return ip_availability.to_dict()


@profiler.trace
def add_network_to_dhcp_agent(request, dhcp_agent, network_id):
    return networkclient(request).add_dhcp_agent_to_network(
        agent=dhcp_agent,
        network=network_id)


@profiler.trace
def remove_network_from_dhcp_agent(request, dhcp_agent, network_id):
    return networkclient(request).remove_dhcp_agent_from_network(dhcp_agent,
                                                                 network_id)


@profiler.trace
def provider_list(request):
    return networkclient(request).service_providers()


def floating_ip_pools_list(request):
    return FloatingIpManager(request).list_pools()


@memoized
def tenant_floating_ip_list(request, all_tenants=False, **search_opts):
    return FloatingIpManager(request).list(all_tenants=all_tenants,
                                           **search_opts)


def floating_ip_port_forwarding_list(request, fip):
    return PortForwardingManager(request).list(fip)


def floating_ip_port_forwarding_create(request, fip, **params):
    return PortForwardingManager(request).create(fip, **params)


def floating_ip_port_forwarding_update(request, fip, **params):
    return PortForwardingManager(request).update(fip, **params)


def floating_ip_port_forwarding_get(request, fip, pfw):
    return PortForwardingManager(request).get(fip, pfw)


def floating_ip_port_forwarding_delete(request, fip, pfw):
    return PortForwardingManager(request).delete(fip, pfw)


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


def floating_ip_target_list_by_instance(request, instance_id, cache=None):
    return FloatingIpManager(request).list_targets_by_instance(
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
                               cidr, group_id, description=None):
    return SecurityGroupManager(request).rule_create(
        parent_group_id, direction, ethertype, ip_protocol,
        from_port, to_port, cidr, group_id, description)


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

    # NOTE(e0ne): we don't need to call neutron if we have no instances
    if not servers:
        return

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
    except neutron_exc.NotFound as e:
        LOG.error('Neutron resource does not exist. %s', e)
        return
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
    network_names = dict((network.id, network.name_or_id)
                         for network in networks)

    for server in servers:
        try:
            addresses = _server_get_addresses(
                request,
                server,
                instances_ports,
                ports_floating_ips,
                network_names)
        except Exception as e:
            LOG.error(str(e))
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
        return {'OS-EXT-IPS-MAC:mac_addr': mac,
                'version': version,
                'addr': ip,
                'OS-EXT-IPS:type': type}

    addresses = collections.defaultdict(list)
    instance_ports = ports.get(server.id, [])
    for port in instance_ports:
        network_name = network_names.get(port.network_id)
        if network_name is not None:
            if port.fixed_ips:
                for fixed_ip in port.fixed_ips:
                    addresses[network_name].append(
                        _format_address(port.mac_address,
                                        fixed_ip['ip_address'],
                                        'fixed'))
            else:
                addresses[network_name] = []
            port_fips = floating_ips.get(port.id, [])
            for fip in port_fips:
                addresses[network_name].append(
                    _format_address(port.mac_address,
                                    fip.floating_ip_address,
                                    'floating'))

    return dict(addresses)


@profiler.trace
@memoized
def list_extensions(request):
    """List neutron extensions.

    :param request: django request object
    """
    neutron_api = networkclient(request)
    try:
        extensions_list = neutron_api.extensions()
    except exceptions.ServiceCatalogException:
        return {}
    return tuple(extensions_list)


@profiler.trace
def is_extension_supported(request, extension_alias):
    """Check if a specified extension is supported.

    :param request: django request object
    :param extension_alias: neutron extension alias
    """
    extensions = list_extensions(request)
    for extension in extensions:
        if extension['alias'] == extension_alias:
            return True
    else:
        return False


@profiler.trace
def is_extension_floating_ip_port_forwarding_supported(request):
    try:
        return is_extension_supported(
            request, extension_alias='floating-ip-port-forwarding')
    except Exception as e:
        LOG.error("It was not possible to check if the "
                  "floating-ip-port-forwarding extension is enabled in "
                  "neutron. Port forwardings will not be enabled.: %s", e)
        return False


# TODO(amotoki): Clean up 'default' parameter because the default
# values are pre-defined now, so 'default' argument is meaningless
# in most cases.
def is_enabled_by_config(name, default=True):
    try:
        return setting_utils.get_dict_config('OPENSTACK_NEUTRON_NETWORK', name)
    except KeyError:
        # No default value is defined.
        # This is a fallback logic for horizon plugins.
        return default


# TODO(amotoki): Clean up 'default' parameter because the default
# values are pre-defined now, so 'default' argument is meaningless
# in most cases.
@memoized
def is_service_enabled(request, config_name, ext_name, default=True):
    return (is_enabled_by_config(config_name, default) and
            is_extension_supported(request, ext_name))


@memoized
def is_quotas_extension_supported(request):
    return (is_enabled_by_config('enable_quotas') and
            is_extension_supported(request, 'quotas'))


@memoized
def is_router_enabled(request):
    return (is_enabled_by_config('enable_router') and
            is_extension_supported(request, 'router'))


# FEATURE_MAP is used to define:
# - related neutron extension name (key: "extension")
# - corresponding dashboard config (key: "config")
# - RBAC policies (key: "policies")
# If a key is not contained, the corresponding permission check is skipped.
FEATURE_MAP = {
    'dvr': {
        'extension': 'dvr',
        'config': {
            'name': 'enable_distributed_router',
        },
        'policies': {
            'get': 'get_router:distributed',
            'create': 'create_router:distributed',
            'update': 'update_router:distributed',
        }
    },
    'l3-ha': {
        'extension': 'l3-ha',
        'config': {
            'name': 'enable_ha_router',
        },
        'policies': {
            'get': 'get_router:ha',
            'create': 'create_router:ha',
            'update': 'update_router:ha',
        }
    },
    'ext-gw-mode': {
        'extension': 'ext-gw-mode',
        'policies': {
            'create_router_enable_snat':
                'create_router:external_gateway_info:enable_snat',
            'update_router_enable_snat':
                'update_router:external_gateway_info:enable_snat',
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
    feature_info = FEATURE_MAP.get(feature)
    if not feature_info:
        raise ValueError("The requested feature '%(feature)s' is unknown. "
                         "Please make sure to specify a feature defined "
                         "in FEATURE_MAP.")

    # Check dashboard settings
    feature_config = feature_info.get('config')
    if feature_config:
        if not setting_utils.get_dict_config('OPENSTACK_NEUTRON_NETWORK',
                                             feature_config['name']):
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
    policy = networkclient(request).create_qos_policy(**kwargs)
    return QoSPolicy(policy.to_dict())


def policy_list(request, **kwargs):
    """List of QoS Policies."""
    policies = networkclient(request).qos_policies(**kwargs)
    return [QoSPolicy(p.to_dict()) for p in policies]


@profiler.trace
def policy_get(request, policy_id, **kwargs):
    """Get QoS policy for a given policy id."""
    policy = networkclient(request).get_qos_policy(policy_id)
    return QoSPolicy(policy.to_dict())


@profiler.trace
def policy_delete(request, policy_id):
    """Delete QoS policy for a given policy id."""
    networkclient(request).delete_qos_policy(policy_id)


class DSCPMarkingRule(NeutronAPIDictWrapper):
    """Wrapper for neutron DSCPMarkingRule."""


@profiler.trace
def dscp_marking_rule_create(request, policy_id, **kwargs):
    """Create a DSCP Marking rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param dscp_mark: integer
    :return: A dscp_mark_rule object.
    """
    dscp_marking_rule = networkclient(request).create_qos_dscp_marking_rule(
        policy_id, **kwargs)
    return DSCPMarkingRule(dscp_marking_rule.to_dict())


@profiler.trace
def dscp_marking_rule_update(request, policy_id, rule_id, **kwargs):
    """Update a DSCP Marking Limit Rule."""

    dscpmarking_update = networkclient(request).update_qos_dscp_marking_rule(
        rule_id, policy_id, **kwargs)
    return DSCPMarkingRule(dscpmarking_update.to_dict())


def dscp_marking_rule_delete(request, policy_id, rule_id):
    """Deletes a DSCP Marking Rule."""

    networkclient(request).delete_qos_dscp_marking_rule(
        rule_id, policy_id)


class MinimumBandwidthRule(NeutronAPIDictWrapper):
    """Wrapper for neutron MinimumBandwidthRule."""


@profiler.trace
def minimum_bandwidth_rule_create(request, policy_id, **kwargs):
    """Create a Minimum Bandwidth rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param min_kbps: integer
    :param direction: string (egress or ingress)
    :return: A minimum_bandwidth_rule object.
    """
    minimum_bandwidth_rule = networkclient(
        request).create_qos_minimum_bandwidth_rule(
            policy_id, **kwargs)
    return MinimumBandwidthRule(minimum_bandwidth_rule.to_dict())


@profiler.trace
def minimum_bandwidth_rule_update(request, policy_id, rule_id, **kwargs):
    """Update a Minimum Bandwidth rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param min_kbps: integer
    :param direction: string (egress or ingress)
    :return: A minimum_bandwidth_rule object.
    """
    minbandwidth_update = networkclient(
        request).update_qos_minimum_bandwidth_rule(
            rule_id, policy_id, **kwargs)
    return MinimumBandwidthRule(minbandwidth_update.to_dict())


def minimum_bandwidth_rule_delete(request, policy_id, rule_id):
    """Deletes a Minimum Bandwidth Rule."""
    networkclient(request).delete_qos_minimum_bandwidth_rule(
        rule_id, policy_id)


class BandwidthLimitRule(NeutronAPIDictWrapper):
    """Wrapper for neutron BandwidthLimitRule."""


@profiler.trace
def bandwidth_limit_rule_create(request, policy_id, **kwargs):
    """Create a Bandwidth Limit rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param max_kbps: integer
    :param max_burst_kbps: integer
    :param direction: string (egress or ingress)
    :return: A bandwidth_limit_rule object.
    """
    bandwidth_limit_rule = networkclient(
        request).create_qos_bandwidth_limit_rule(policy_id, **kwargs)
    return BandwidthLimitRule(bandwidth_limit_rule.to_dict())


@profiler.trace
def bandwidth_limit_rule_update(request, policy_id, rule_id, **kwargs):
    """Update a Bandwidth Limit rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param max_kbps: integer
    :param max_burst_kbps: integer
    :param direction: string (egress or ingress)
    :return: A bandwidth_limit_rule object.
    """
    bandwidthlimit_update = networkclient(
        request).update_qos_bandwidth_limit_rule(rule_id, policy_id, **kwargs)
    return BandwidthLimitRule(bandwidthlimit_update.to_dict())


@profiler.trace
def bandwidth_limit_rule_delete(request, policy_id, rule_id):
    """Deletes a Bandwidth Limit Rule."""
    networkclient(request).delete_qos_bandwidth_limit_rule(rule_id, policy_id)


class MinimumPacketRateRule(NeutronAPIDictWrapper):
    """Wrapper for neutron MinimumPacketRateRule."""


@profiler.trace
def minimum_packet_rate_rule_create(request, policy_id, **kwargs):
    """Create a Minimum Packet Rate rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param min_kpps: integer
    :param direction: string (egress or ingress)
    :return: A minimum_packet_rate_rule object.
    """
    minimum_packet_rate_rule = networkclient(
        request).create_qos_minimum_packet_rate_rule(
            policy_id, **kwargs)
    return MinimumPacketRateRule(minimum_packet_rate_rule.to_dict())


@profiler.trace
def minimum_packet_rate_rule_update(request, policy_id, rule_id, **kwargs):
    """Update a Minimum Packet Rate rule.

    :param request: request context
    :param policy_id: Id of the policy
    :param min_kpps: integer
    :param direction: string (egress or ingress)
    :return: A minimum_packet_rate_rule object.
    """
    minpacketrate_update = networkclient(
        request).update_qos_minimum_packet_rate_rule(
            rule_id, policy_id, **kwargs)
    return MinimumPacketRateRule(minpacketrate_update)


def minimum_packet_rate_rule_delete(request, policy_id, rule_id):
    """Deletes a Minimum Packet Rate Rule."""
    networkclient(request).delete_qos_minimum_packet_rate_rule(
        rule_id, policy_id)


@profiler.trace
def list_availability_zones(request, resource=None, state=None):
    az_list = networkclient(request).availability_zones()
    if resource:
        az_list = [az.to_dict() for az in az_list
                   if az['resource'] == resource]
    if state:
        az_list = [az.to_dict() for az in az_list
                   if az['state'] == state]

    return sorted(az_list, key=lambda zone: zone['name'])


class RBACPolicy(NeutronAPIDictWrapper):
    """Wrapper for neutron RBAC Policy."""

    def __init__(self, apidict):
        if 'target_project_id' in apidict:
            apidict['target_tenant'] = apidict['target_project_id']
        super().__init__(apidict=apidict)


def rbac_policy_create(request, **kwargs):
    """Create a RBAC Policy.

    :param request: request context
    :param target_tenant: target tenant of the policy
    :param tenant_id: owner tenant of the policy(Not recommended)
    :param object_type: network or qos_policy
    :param object_id: object id of policy
    :param action: access_as_shared or access_as_external
    :return: RBACPolicy object
    """
    rbac_policy = networkclient(request).create_rbac_policy(**kwargs)
    return RBACPolicy(rbac_policy.to_dict())


def rbac_policy_list(request, **kwargs):
    """List of RBAC Policies."""
    policies = networkclient(request).rbac_policies(**kwargs)
    return [RBACPolicy(p.to_dict()) for p in policies]


def rbac_policy_update(request, policy_id, **kwargs):
    """Update a RBAC Policy.

    :param request: request context
    :param policy_id: target policy id
    :param target_tenant: target tenant of the policy
    :return: RBACPolicy object
    """
    rbac_policy = networkclient(request).update_rbac_policy(
        policy_id, **kwargs)
    return RBACPolicy(rbac_policy.to_dict())


@profiler.trace
def rbac_policy_get(request, policy_id):
    """Get RBAC policy for a given policy id."""
    policy = networkclient(request).get_rbac_policy(policy_id)
    return RBACPolicy(policy.to_dict())


@profiler.trace
def rbac_policy_delete(request, policy_id):
    """Delete RBAC policy for a given policy id."""
    networkclient(request).delete_rbac_policy(policy_id)
