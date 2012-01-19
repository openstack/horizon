# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
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

import logging

from novaclient.v1_1 import client as nova_client
from novaclient.v1_1 import security_group_rules as nova_rules
from novaclient.v1_1.servers import REBOOT_HARD

from horizon.api.base import *
from horizon.api.deprecated import check_openstackx
from horizon.api.deprecated import extras_api


LOG = logging.getLogger(__name__)


# API static values
INSTANCE_ACTIVE_STATE = 'ACTIVE'
VOLUME_STATE_AVAILABLE = "available"


class Flavor(APIResourceWrapper):
    """Simple wrapper around openstackx.admin.flavors.Flavor"""
    _attrs = ['disk', 'id', 'links', 'name', 'ram', 'vcpus']


class FloatingIp(APIResourceWrapper):
    """Simple wrapper for floating ip pools"""
    _attrs = ['ip', 'fixed_ip', 'instance_id', 'id', 'pool']


class FloatingIpPool(APIResourceWrapper):
    """Simple wrapper for floating ips"""
    _attrs = ['name']


class KeyPair(APIResourceWrapper):
    """Simple wrapper around openstackx.extras.keypairs.Keypair"""
    _attrs = ['fingerprint', 'name', 'private_key']


class VirtualInterface(APIResourceWrapper):
    _attrs = ['id', 'mac_address']


class Volume(APIResourceWrapper):
    """Nova Volume representation"""
    _attrs = ['id', 'status', 'displayName', 'size', 'volumeType', 'createdAt',
              'attachments', 'displayDescription']


class VNCConsole(APIDictWrapper):
    """Simple wrapper for floating ips"""
    _attrs = ['url', 'type']


class Quota(object):
    """ Basic wrapper for individual limits in a quota."""
    def __init__(self, name, limit):
        self.name = name
        self.limit = limit

    def __repr__(self):
        return "<Quota: (%s, %s)>" % (self.name, self.limit)


class QuotaSet(object):
    """ Basic wrapper for quota sets."""
    def __init__(self, apiresource):
        self.items = []
        for k in apiresource._info.keys():
            if k in ['id']:
                continue
            v = int(apiresource._info[k])
            q = Quota(k, v)
            self.items.append(q)
            setattr(self, k, v)


class Server(APIResourceWrapper):
    """Simple wrapper around openstackx.extras.server.Server

       Preserves the request info so image name can later be retrieved
    """
    _attrs = ['addresses', 'attrs', 'hostId', 'id', 'image', 'links',
             'metadata', 'name', 'private_ip', 'public_ip', 'status', 'uuid',
             'image_name', 'VirtualInterfaces', 'flavor', 'key_name',
             'OS-EXT-STS:power_state', 'OS-EXT-STS:task_state']

    def __init__(self, apiresource, request):
        super(Server, self).__init__(apiresource)
        self.request = request

    @property
    def image_name(self):
        from glance.common import exception as glance_exceptions
        from horizon.api import glance
        try:
            image = glance.image_get_meta(self.request, self.image['id'])
            return image.name
        except glance_exceptions.NotFound:
            return "(not found)"

    def reboot(self, hardness=REBOOT_HARD):
        novaclient(self.request).servers.reboot(self.id, hardness)


class Usage(APIResourceWrapper):
    """Simple wrapper around openstackx.extras.usage.Usage"""
    _attrs = ['begin', 'instances', 'stop', 'tenant_id',
             'total_active_disk_size', 'total_active_instances',
             'total_active_ram_size', 'total_active_vcpus', 'total_cpu_usage',
             'total_disk_usage', 'total_hours', 'total_ram_usage']


class SecurityGroup(APIResourceWrapper):
    """Simple wrapper around openstackx.extras.security_groups.SecurityGroup"""
    _attrs = ['id', 'name', 'description', 'tenant_id']

    @property
    def rules(self):
        """ Wraps transmitted rule info in the novaclient rule class. """
        if not hasattr(self, "_rules"):
            manager = nova_rules.SecurityGroupRuleManager
            self._rules = [nova_rules.SecurityGroupRule(manager, rule) for \
                           rule in self._apiresource.rules]
        return self._rules

    @rules.setter
    def rules(self, value):
        self._rules = value


class SecurityGroupRule(APIResourceWrapper):
    """ Simple wrapper for individual rules in a SecurityGroup. """
    _attrs = ['id', 'ip_protocol', 'from_port', 'to_port', 'ip_range']

    def __unicode__(self):
        vals = {'from': self.from_port,
                'to': self.to_port,
                'cidr': self.ip_range['cidr']}
        return 'ALLOW %(from)s:%(to)s from %(cidr)s' % vals


def novaclient(request):
    LOG.debug('novaclient connection created using token "%s" and url "%s"' %
              (request.user.token, url_for(request, 'compute')))
    c = nova_client.Client(request.user.username,
                           request.user.token,
                           project_id=request.user.tenant_id,
                           auth_url=url_for(request, 'compute'))
    c.client.auth_token = request.user.token
    c.client.management_url = url_for(request, 'compute')
    return c


def server_vnc_console(request, instance_id, type='novnc'):
    return VNCConsole(novaclient(request).servers.get_vnc_console(instance_id,
                                                  type)['console'])


def flavor_create(request, name, memory, vcpu, disk, flavor_id):
    return Flavor(novaclient(request).flavors.create(
            name, int(memory), int(vcpu), int(disk), flavor_id))


def flavor_delete(request, flavor_id, purge=False):
    novaclient(request).flavors.delete(flavor_id, purge)


def flavor_get(request, flavor_id):
    return Flavor(novaclient(request).flavors.get(flavor_id))


def flavor_list(request):
    return [Flavor(f) for f in novaclient(request).flavors.list()]


def tenant_floating_ip_list(request):
    """
    Fetches a list of all floating ips.
    """
    return [FloatingIp(ip) for ip in novaclient(request).floating_ips.list()]


def floating_ip_pools_list(request):
    """
    Fetches a list of all floating ip pools.
    """
    return [FloatingIpPool(pool)
            for pool in novaclient(request).floating_ip_pools.list()]


def tenant_floating_ip_get(request, floating_ip_id):
    """
    Fetches a floating ip.
    """
    return novaclient(request).floating_ips.get(floating_ip_id)


def tenant_floating_ip_allocate(request, pool=None):
    """
    Allocates a floating ip to tenant.
    Optionally you may provide a pool for which you would like the IP.
    """
    return novaclient(request).floating_ips.create(pool=pool)


def tenant_floating_ip_release(request, floating_ip_id):
    """
    Releases floating ip from the pool of a tenant.
    """
    return novaclient(request).floating_ips.delete(floating_ip_id)


def snapshot_create(request, instance_id, name):
    return novaclient(request).servers.create_image(instance_id, name)


def keypair_create(request, name):
    return KeyPair(novaclient(request).keypairs.create(name))


def keypair_import(request, name, public_key):
    return KeyPair(novaclient(request).keypairs.create(name, public_key))


def keypair_delete(request, keypair_id):
    novaclient(request).keypairs.delete(keypair_id)


def keypair_list(request):
    return [KeyPair(key) for key in novaclient(request).keypairs.list()]


def server_create(request, name, image, flavor, key_name, user_data,
                  security_groups, block_device_mapping, instance_count=1):
    return Server(novaclient(request).servers.create(
            name, image, flavor, userdata=user_data,
            security_groups=security_groups,
            key_name=key_name, block_device_mapping=block_device_mapping,
            min_count=instance_count), request)


def server_delete(request, instance):
    novaclient(request).servers.delete(instance)


def server_get(request, instance_id):
    return Server(novaclient(request).servers.get(instance_id), request)


def server_list(request):
    # (sleepsonthefloor) explicitly filter by project id, so admins
    # can retrieve a list that includes -only- their instances if destired.
    # admin_server_list() returns all servers.
    return [Server(s, request) for s in novaclient(request).\
            servers.list(True, {'project_id': request.user.tenant_id})]


def server_console_output(request, instance_id, tail_length=None):
    """Gets console output of an instance"""
    return novaclient(request).servers.get_console_output(instance_id,
                                                          length=tail_length)


@check_openstackx
def admin_server_list(request):
    return [Server(s, request) for s in novaclient(request).servers.list()]


def server_pause(request, instance_id):
    novaclient(request).servers.pause(instance_id)


def server_unpause(request, instance_id):
    novaclient(request).servers.unpause(instance_id)


def server_suspend(request, instance_id):
    novaclient(request).servers.suspend(instance_id)


def server_resume(request, instance_id):
    novaclient(request).servers.resume(instance_id)


def server_reboot(request,
                  instance_id,
                  hardness=REBOOT_HARD):
    server = server_get(request, instance_id)
    server.reboot(hardness)


def server_update(request, instance_id, name):
    return novaclient(request).servers.update(instance_id, name=name)


def server_add_floating_ip(request, server, address):
    """
    Associates floating IP to server's fixed IP.
    """
    server = novaclient(request).servers.get(server)
    fip = novaclient(request).floating_ips.get(address)

    return novaclient(request).servers.add_floating_ip(server, fip)


def server_remove_floating_ip(request, server, address):
    """
    Removes relationship between floating and server's fixed ip.
    """
    fip = novaclient(request).floating_ips.get(address)
    server = novaclient(request).servers.get(fip.instance_id)

    return novaclient(request).servers.remove_floating_ip(server, fip)


def tenant_quota_get(request, tenant_id):
    return QuotaSet(novaclient(request).quotas.get(tenant_id))


def tenant_quota_update(request, tenant_id, **kwargs):
    novaclient(request).quotas.update(tenant_id, **kwargs)


def tenant_quota_defaults(request, tenant_id):
    return QuotaSet(novaclient(request).quotas.defaults(tenant_id))


@check_openstackx
def usage_get(request, tenant_id, start, end):
    return Usage(extras_api(request).usage.get(tenant_id, start, end))


@check_openstackx
def usage_list(request, start, end):
    return [Usage(u) for u in extras_api(request).usage.list(start, end)]


def security_group_list(request):
    return [SecurityGroup(g) for g in novaclient(request).\
                                     security_groups.list()]


def security_group_get(request, security_group_id):
    return SecurityGroup(novaclient(request).\
                         security_groups.get(security_group_id))


def security_group_create(request, name, description):
    return SecurityGroup(novaclient(request).\
                         security_groups.create(name, description))


def security_group_delete(request, security_group_id):
    novaclient(request).security_groups.delete(security_group_id)


def security_group_rule_create(request, parent_group_id, ip_protocol=None,
                               from_port=None, to_port=None, cidr=None,
                               group_id=None):
    return SecurityGroupRule(novaclient(request).\
                             security_group_rules.create(parent_group_id,
                                                         ip_protocol,
                                                         from_port,
                                                         to_port,
                                                         cidr,
                                                         group_id))


def security_group_rule_delete(request, security_group_rule_id):
    novaclient(request).security_group_rules.delete(security_group_rule_id)


def virtual_interfaces_list(request, instance_id):
    return novaclient(request).virtual_interfaces.list(instance_id)


def volume_list(request):
    return [Volume(vol) for vol in novaclient(request).volumes.list()]


def volume_get(request, volume_id):
    return Volume(novaclient(request).volumes.get(volume_id))


def volume_instance_list(request, instance_id):
    return novaclient(request).volumes.get_server_volumes(instance_id)


def volume_create(request, size, name, description):
    return Volume(novaclient(request).volumes.create(
            size, display_name=name, display_description=description))


def volume_delete(request, volume_id):
    novaclient(request).volumes.delete(volume_id)


def volume_attach(request, volume_id, instance_id, device):
    novaclient(request).volumes.create_server_volume(
            instance_id, volume_id, device)


def volume_detach(request, instance_id, attachment_id):
    novaclient(request).volumes.delete_server_volume(
            instance_id, attachment_id)
