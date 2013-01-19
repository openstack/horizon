# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""Abstraction layer of networking functionalities.

Now Nova and Quantum have duplicated features.
Thie API layer is introduced to hide the differences between them
from dashboard implementations.
"""

import abc


class NetworkClient(object):
    def __init__(self, request):
        from openstack_dashboard import api
        if api.base.is_service_enabled(request, 'network'):
            self.floating_ips = api.quantum.FloatingIpManager(request)
        else:
            self.floating_ips = api.nova.FloatingIpManager(request)


class FloatingIpManager(object):
    """Abstract class to implement Floating IP methods

    FloatingIP object returned from methods in this class
    must contains the following attributes:
    - id : ID of Floating IP
    - ip : Floating IP address
    - pool : ID of Floating IP pool from which the address is allocated
    - fixed_ip : Fixed IP address of a VIF associated with the address
    - port_id : ID of a VIF associated with the address
                (instance_id when Nova floating IP is used)
    - instance_id : Instance ID of an associated with the Floating IP
"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_pools(self):
        """Fetches a list of all floating IP pools.

        A list of FloatingIpPool object is returned.
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
        allocate an floating IP.
        """
        pass

    @abc.abstractmethod
    def release(self, floating_ip_id):
        """Releases a floating IP specified."""
        pass

    @abc.abstractmethod
    def associate(self, floating_ip_id, port_id):
        """Associates the floating IP to the port.

        port_id is a fixed IP of a instance (Nova) or
        a port_id attached to a VNIC of a instance.
        """
        pass

    @abc.abstractmethod
    def disassociate(self, floating_ip_id, port_id):
        """Disassociates the floating IP from the port.

        port_id is a fixed IP of a instance (Nova) or
        a port_id attached to a VNIC of a instance.
        """
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
    def get_target_id_by_instance(self, instance_id):
        """Returns a target ID of floating IP association based on
        a backend implementation.
        """
        pass

    @abc.abstractmethod
    def is_simple_associate_supported(self):
        """Returns True if the default floating IP pool is enabled."""
        pass


def floating_ip_pools_list(request):
    return NetworkClient(request).floating_ips.list_pools()


def tenant_floating_ip_list(request):
    return NetworkClient(request).floating_ips.list()


def tenant_floating_ip_get(request, floating_ip_id):
    return NetworkClient(request).floating_ips.get(floating_ip_id)


def tenant_floating_ip_allocate(request, pool=None):
    return NetworkClient(request).floating_ips.allocate(pool)


def tenant_floating_ip_release(request, floating_ip_id):
    return NetworkClient(request).floating_ips.release(floating_ip_id)


def floating_ip_associate(request, floating_ip_id, port_id):
    return NetworkClient(request).floating_ips.associate(floating_ip_id,
                                                         port_id)


def floating_ip_disassociate(request, floating_ip_id, port_id):
    return NetworkClient(request).floating_ips.disassociate(floating_ip_id,
                                                            port_id)


def floating_ip_target_list(request):
    return NetworkClient(request).floating_ips.list_targets()


def floating_ip_target_get_by_instance(request, instance_id):
    return NetworkClient(request).floating_ips.get_target_id_by_instance(
        instance_id)
