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

Currently Nova and Neutron have duplicated features. This API layer is
introduced to abstract the differences between them for seamless consumption by
different dashboard implementations.
"""

from openstack_dashboard.api import base
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova


class NetworkClient(object):
    def __init__(self, request):
        neutron_enabled = base.is_service_enabled(request, 'network')

        if neutron_enabled:
            self.floating_ips = neutron.FloatingIpManager(request)
        else:
            self.floating_ips = nova.FloatingIpManager(request)

        if (neutron_enabled and
                neutron.is_extension_supported(request, 'security-group')):
            self.secgroups = neutron.SecurityGroupManager(request)
        else:
            self.secgroups = nova.SecurityGroupManager(request)


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


def floating_ip_disassociate(request, floating_ip_id):
    return NetworkClient(request).floating_ips.disassociate(floating_ip_id)


def floating_ip_target_list(request):
    return NetworkClient(request).floating_ips.list_targets()


def floating_ip_target_get_by_instance(request, instance_id, cache=None):
    return NetworkClient(request).floating_ips.get_target_id_by_instance(
        instance_id, cache)


def floating_ip_target_list_by_instance(request, instance_id, cache=None):
    floating_ips = NetworkClient(request).floating_ips
    return floating_ips.list_target_id_by_instance(instance_id, cache)


def floating_ip_simple_associate_supported(request):
    return NetworkClient(request).floating_ips.is_simple_associate_supported()


def floating_ip_supported(request):
    return NetworkClient(request).floating_ips.is_supported()


def security_group_list(request):
    return NetworkClient(request).secgroups.list()


def security_group_get(request, sg_id):
    return NetworkClient(request).secgroups.get(sg_id)


def security_group_create(request, name, desc):
    return NetworkClient(request).secgroups.create(name, desc)


def security_group_delete(request, sg_id):
    return NetworkClient(request).secgroups.delete(sg_id)


def security_group_update(request, sg_id, name, desc):
    return NetworkClient(request).secgroups.update(sg_id, name, desc)


def security_group_rule_create(request, parent_group_id,
                               direction, ethertype,
                               ip_protocol, from_port, to_port,
                               cidr, group_id):
    return NetworkClient(request).secgroups.rule_create(
        parent_group_id, direction, ethertype, ip_protocol,
        from_port, to_port, cidr, group_id)


def security_group_rule_delete(request, sgr_id):
    return NetworkClient(request).secgroups.rule_delete(sgr_id)


def server_security_groups(request, instance_id):
    return NetworkClient(request).secgroups.list_by_instance(instance_id)


def server_update_security_groups(request, instance_id,
                                  new_security_group_ids):
    return NetworkClient(request).secgroups.update_instance_security_group(
        instance_id, new_security_group_ids)


def security_group_backend(request):
    return NetworkClient(request).secgroups.backend


def servers_update_addresses(request, servers, all_tenants=False):
    """Retrieve servers networking information from Neutron if enabled.

       Should be used when up to date networking information is required,
       and Nova's networking info caching mechanism is not fast enough.

    """
    neutron_enabled = base.is_service_enabled(request, 'network')
    if neutron_enabled:
        neutron.servers_update_addresses(request, servers, all_tenants)
