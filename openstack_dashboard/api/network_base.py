# Copyright 2013 NEC Corporation
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

"""Abstraction layer for networking functionalities.

This module defines internal APIs for duplicated features between OpenStack
Compute and OpenStack Networking. The networking abstraction layer expects
methods defined in this module.
"""

import abc

import six


@six.add_metaclass(abc.ABCMeta)
class FloatingIpManager(object):
    """Abstract class to implement Floating IP methods

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

    @abc.abstractmethod
    def list_pools(self):
        """Fetches a list of all floating IP pools.

        A list of FloatingIpPool objects is returned.
        FloatingIpPool object is an APIResourceWrapper/APIDictWrapper
        where 'id' and 'name' attributes are defined.
        """
        pass

    @abc.abstractmethod
    def list(self):
        """Fetches a list all floating IPs.

        A returned value is a list of FloatingIp object.
        """
        pass

    @abc.abstractmethod
    def get(self, floating_ip_id):
        """Fetches the floating IP.

        It returns a FloatingIp object corresponding to floating_ip_id.
        """
        pass

    @abc.abstractmethod
    def allocate(self, pool=None):
        """Allocates a floating IP to the tenant.

        You must provide a pool name or id for which you would like to
        allocate a floating IP.
        """
        pass

    @abc.abstractmethod
    def release(self, floating_ip_id):
        """Releases a floating IP specified."""
        pass

    @abc.abstractmethod
    def associate(self, floating_ip_id, port_id):
        """Associates the floating IP to the port.

        port_id is a fixed IP of an instance (Nova) or
        a port_id attached to a VNIC of an instance.
        """
        pass

    @abc.abstractmethod
    def disassociate(self, floating_ip_id):
        """Disassociates the floating IP specified."""
        pass

    @abc.abstractmethod
    def list_targets(self):
        """Returns a list of association targets of instance VIFs.

        Each association target is represented as FloatingIpTarget object.
        FloatingIpTarget is a APIResourceWrapper/APIDictWrapper and
        'id' and 'name' attributes must be defined in each object.
        FloatingIpTarget.id can be passed as port_id in associate().
        FloatingIpTarget.name is displayed in Floating Ip Association Form.
        """
        pass

    @abc.abstractmethod
    def get_target_id_by_instance(self, instance_id, target_list=None):
        """Returns a target ID of floating IP association.

        Based on a backend implementation.

        :param instance_id: ID of target VM instance
        :param target_list: (optional) a list returned by list_targets().
            If specified, looking up is done against the specified list
            to save extra API calls to a back-end. Otherwise a target
            information is retrieved from a back-end inside the method.
        """
        pass

    @abc.abstractmethod
    def list_target_id_by_instance(self, instance_id, target_list=None):
        """Returns a list of instance's target IDs of floating IP association.

        Based on the backend implementation

        :param instance_id: ID of target VM instance
        :param target_list: (optional) a list returned by list_targets().
            If specified, looking up is done against the specified list
            to save extra API calls to a back-end. Otherwise target list
            is retrieved from a back-end inside the method.
        """
        pass

    @abc.abstractmethod
    def is_simple_associate_supported(self):
        """Returns True if the default floating IP pool is enabled."""
        pass

    @abc.abstractmethod
    def is_supported(self):
        """Returns True if floating IP feature is supported."""
        pass


@six.add_metaclass(abc.ABCMeta)
class SecurityGroupManager(object):
    """Abstract class to implement Security Group methods

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

    @abc.abstractmethod
    def list(self):
        """Fetches a list all security groups.

        A returned value is a list of SecurityGroup object.
        """
        pass

    @abc.abstractmethod
    def get(self, sg_id):
        """Fetches the security group.

        It returns a SecurityGroup object corresponding to sg_id.
        """
        pass

    @abc.abstractmethod
    def create(self, name, desc):
        """Create a new security group.

        It returns a SecurityGroup object created.
        """
        pass

    @abc.abstractmethod
    def delete(self, sg_id):
        """Delete the specified security group."""
        pass

    @abc.abstractmethod
    def rule_create(self, parent_group_id,
                    direction=None, ethertype=None,
                    ip_protocol=None, from_port=None, to_port=None,
                    cidr=None, group_id=None):
        """Create a new security group rule.

        :param parent_group_id: security group id a rule is created to
        :param direction: ingress or egress
        :param ethertype: ipv4, ipv6, ...
        :param ip_protocol: tcp, udp, icmp
        :param from_port: L4 port range min
        :param to_port: L4 port range max
        :param cidr: Source IP CIDR
        :param group_id: ID of Source Security Group
        """
        pass

    @abc.abstractmethod
    def rule_delete(self, sgr_id):
        """Delete the specified security group rule."""
        pass

    @abc.abstractmethod
    def list_by_instance(self, instance_id):
        """Get security groups of an instance."""
        pass

    @abc.abstractmethod
    def update_instance_security_group(self, instance_id,
                                       new_security_group_ids):
        """Update security groups of a specified instance."""
        pass
