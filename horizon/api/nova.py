# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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
from novaclient.v1_1.security_groups import SecurityGroup as NovaSecurityGroup
from novaclient.v1_1.servers import REBOOT_HARD

from horizon.api.base import APIResourceWrapper, APIDictWrapper, url_for

from django.utils.translation import ugettext as _

LOG = logging.getLogger(__name__)


# API static values
INSTANCE_ACTIVE_STATE = 'ACTIVE'
VOLUME_STATE_AVAILABLE = "available"


class VNCConsole(APIDictWrapper):
    """Wrapper for the "console" dictionary returned by the
    novaclient.servers.get_vnc_console method.
    """
    _attrs = ['url', 'type']


class Quota(object):
    """Wrapper for individual limits in a quota."""
    def __init__(self, name, limit):
        self.name = name
        self.limit = limit

    def __repr__(self):
        return "<Quota: (%s, %s)>" % (self.name, self.limit)


class QuotaSet(object):
    """Wrapper for novaclient.quotas.QuotaSet objects which wraps the
    individual quotas inside Quota objects.
    """
    def __init__(self, apiresource):
        self.items = []
        for k in apiresource._info.keys():
            if k in ['id']:
                continue
            limit = apiresource._info[k]
            v = int(limit) if limit is not None else limit
            q = Quota(k, v)
            self.items.append(q)
            setattr(self, k, v)


class Server(APIResourceWrapper):
    """Simple wrapper around novaclient.server.Server

       Preserves the request info so image name can later be retrieved

    """
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links',
             'metadata', 'name', 'private_ip', 'public_ip', 'status', 'uuid',
             'image_name', 'VirtualInterfaces', 'flavor', 'key_name',
             'tenant_id', 'user_id', 'OS-EXT-STS:power_state',
             'OS-EXT-STS:task_state', 'OS-EXT-SRV-ATTR:instance_name',
             'OS-EXT-SRV-ATTR:host']

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

    @property
    def internal_name(self):
        return getattr(self, 'OS-EXT-SRV-ATTR:instance_name', "")

    def reboot(self, hardness=REBOOT_HARD):
        novaclient(self.request).servers.reboot(self.id, hardness)


class Usage(APIResourceWrapper):
    """Simple wrapper around contrib/simple_usage.py."""
    _attrs = ['start', 'server_usages', 'stop', 'tenant_id',
             'total_local_gb_usage', 'total_memory_mb_usage',
             'total_vcpus_usage', 'total_hours']

    def get_summary(self):
        return {'instances': self.total_active_instances,
                'memory_mb': self.memory_mb,
                'vcpus': getattr(self, "total_vcpus_usage", 0),
                'vcpu_hours': self.vcpu_hours,
                'local_gb': self.local_gb,
                'disk_gb_hours': self.disk_gb_hours}

    @property
    def total_active_instances(self):
        return sum(1 for s in self.server_usages if s['ended_at'] == None)

    @property
    def vcpus(self):
        return sum(s['vcpus'] for s in self.server_usages
                   if s['ended_at'] == None)

    @property
    def vcpu_hours(self):
        return getattr(self, "total_hours", 0)

    @property
    def local_gb(self):
        return sum(s['local_gb'] for s in self.server_usages
                   if s['ended_at'] == None)

    @property
    def memory_mb(self):
        return sum(s['memory_mb'] for s in self.server_usages
                   if s['ended_at'] == None)

    @property
    def disk_gb_hours(self):
        return getattr(self, "total_local_gb_usage", 0)


class SecurityGroup(APIResourceWrapper):
    """Wrapper around novaclient.security_groups.SecurityGroup which wraps its
    rules in SecurityGroupRule objects and allows access to them.
    """
    _attrs = ['id', 'name', 'description', 'tenant_id']

    @property
    def rules(self):
        """Wraps transmitted rule info in the novaclient rule class."""
        if not hasattr(self, "_rules"):
            manager = nova_rules.SecurityGroupRuleManager
            self._rules = [nova_rules.SecurityGroupRule(manager, rule) for \
                           rule in self._apiresource.rules]
        return self._rules

    @rules.setter
    def rules(self, value):
        self._rules = value


class SecurityGroupRule(APIResourceWrapper):
    """ Wrapper for individual rules in a SecurityGroup. """
    _attrs = ['id', 'ip_protocol', 'from_port', 'to_port', 'ip_range', 'group']

    def __unicode__(self):
        if 'name' in self.group:
            vals = {'from': self.from_port,
                    'to': self.to_port,
                    'group': self.group['name']}
            return _('ALLOW %(from)s:%(to)s from %(group)s') % vals
        else:
            vals = {'from': self.from_port,
                    'to': self.to_port,
                    'cidr': self.ip_range['cidr']}
            return _('ALLOW %(from)s:%(to)s from %(cidr)s') % vals


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


def cinderclient(request):
    LOG.debug('cinderclient connection created using token "%s" and url "%s"' %
              (request.user.token, url_for(request, 'volume')))
    c = nova_client.Client(request.user.username,
                           request.user.token,
                           project_id=request.user.tenant_id,
                           auth_url=url_for(request, 'volume'))
    c.client.auth_token = request.user.token
    c.client.management_url = url_for(request, 'volume')
    return c


def server_vnc_console(request, instance_id, console_type='novnc'):
    return VNCConsole(novaclient(request).servers.get_vnc_console(instance_id,
                                                  console_type)['console'])


def flavor_create(request, name, memory, vcpu, disk, flavor_id, ephemeral=0):
    return novaclient(request).flavors.create(name, int(memory), int(vcpu),
                                              int(disk), flavor_id,
                                              ephemeral=int(ephemeral))


def flavor_delete(request, flavor_id):
    novaclient(request).flavors.delete(flavor_id)


def flavor_get(request, flavor_id):
    return novaclient(request).flavors.get(flavor_id)


def flavor_list(request):
    return novaclient(request).flavors.list()


def tenant_floating_ip_list(request):
    """Fetches a list of all floating ips."""
    return novaclient(request).floating_ips.list()


def floating_ip_pools_list(request):
    """Fetches a list of all floating ip pools."""
    return novaclient(request).floating_ip_pools.list()


def tenant_floating_ip_get(request, floating_ip_id):
    """Fetches a floating ip."""
    return novaclient(request).floating_ips.get(floating_ip_id)


def tenant_floating_ip_allocate(request, pool=None):
    """Allocates a floating ip to tenant. Optionally you may provide a pool
    for which you would like the IP.
    """
    return novaclient(request).floating_ips.create(pool=pool)


def tenant_floating_ip_release(request, floating_ip_id):
    """Releases floating ip from the pool of a tenant."""
    return novaclient(request).floating_ips.delete(floating_ip_id)


def snapshot_create(request, instance_id, name):
    return novaclient(request).servers.create_image(instance_id, name)


def keypair_create(request, name):
    return novaclient(request).keypairs.create(name)


def keypair_import(request, name, public_key):
    return novaclient(request).keypairs.create(name, public_key)


def keypair_delete(request, keypair_id):
    novaclient(request).keypairs.delete(keypair_id)


def keypair_list(request):
    return novaclient(request).keypairs.list()


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


def server_list(request, search_opts=None, all_tenants=False):
    if search_opts is None:
        search_opts = {}
    if all_tenants:
        search_opts['all_tenants'] = True
    else:
        search_opts['project_id'] = request.user.tenant_id
    return [Server(s, request) for s in novaclient(request).\
            servers.list(True, search_opts)]


def server_console_output(request, instance_id, tail_length=None):
    """Gets console output of an instance."""
    return novaclient(request).servers.get_console_output(instance_id,
                                                          length=tail_length)


def server_security_groups(request, instance_id):
    """Gets security groups of an instance."""
    # TODO(gabriel): This needs to be moved up to novaclient, and should
    # be removed once novaclient supports this call.
    security_groups = []
    nclient = novaclient(request)
    resp, body = nclient.client.get('/servers/%s/os-security-groups'
                                    % instance_id)
    if body:
        # Wrap data in SG objects as novaclient would.
        sg_objects = [NovaSecurityGroup(nclient.security_groups, sg) for
                      sg in body.get('security_groups', [])]
        # Then wrap novaclient's object with our own. Yes, sadly wrapping
        # with two layers of objects is necessary.
        security_groups = [SecurityGroup(sg) for sg in sg_objects]
        # Package up the rules, as well.
        for sg in security_groups:
            rule_objects = [SecurityGroupRule(rule) for rule in sg.rules]
            sg.rules = rule_objects
    return security_groups


def server_pause(request, instance_id):
    novaclient(request).servers.pause(instance_id)


def server_unpause(request, instance_id):
    novaclient(request).servers.unpause(instance_id)


def server_suspend(request, instance_id):
    novaclient(request).servers.suspend(instance_id)


def server_resume(request, instance_id):
    novaclient(request).servers.resume(instance_id)


def server_reboot(request, instance_id, hardness=REBOOT_HARD):
    server = server_get(request, instance_id)
    server.reboot(hardness)


def server_update(request, instance_id, name):
    return novaclient(request).servers.update(instance_id, name=name)


def server_add_floating_ip(request, server, floating_ip):
    """Associates floating IP to server's fixed IP.
    """
    server = novaclient(request).servers.get(server)
    fip = novaclient(request).floating_ips.get(floating_ip)
    return novaclient(request).servers.add_floating_ip(server.id, fip.ip)


def server_remove_floating_ip(request, server, floating_ip):
    """Removes relationship between floating and server's fixed ip.
    """
    fip = novaclient(request).floating_ips.get(floating_ip)
    server = novaclient(request).servers.get(fip.instance_id)
    return novaclient(request).servers.remove_floating_ip(server.id, fip.ip)


def tenant_quota_get(request, tenant_id):
    return QuotaSet(novaclient(request).quotas.get(tenant_id))


def tenant_quota_update(request, tenant_id, **kwargs):
    novaclient(request).quotas.update(tenant_id, **kwargs)


def tenant_quota_defaults(request, tenant_id):
    return QuotaSet(novaclient(request).quotas.defaults(tenant_id))


def usage_get(request, tenant_id, start, end):
    return Usage(novaclient(request).usage.get(tenant_id, start, end))


def usage_list(request, start, end):
    return [Usage(u) for u in novaclient(request).usage.list(start, end, True)]


def tenant_quota_usages(request):
    """Builds a dictionary of current usage against quota for the current
    tenant.
    """
    # TODO(tres): Make this capture floating_ips and volumes as well.
    instances = server_list(request)
    floating_ips = tenant_floating_ip_list(request)
    quotas = tenant_quota_get(request, request.user.tenant_id)
    flavors = dict([(f.id, f) for f in flavor_list(request)])
    usages = {'instances': {'flavor_fields': [], 'used': len(instances)},
              'cores': {'flavor_fields': ['vcpus'], 'used': 0},
              'gigabytes': {'used': 0,
                            'flavor_fields': ['disk',
                                              'OS-FLV-EXT-DATA:ephemeral']},
              'ram': {'flavor_fields': ['ram'], 'used': 0},
              'floating_ips': {'flavor_fields': [], 'used': len(floating_ips)}}

    for usage in usages:
        for instance in instances:
            for flavor_field in usages[usage]['flavor_fields']:
                usages[usage]['used'] += getattr(
                        flavors[instance.flavor['id']], flavor_field, 0)
        usages[usage]['quota'] = getattr(quotas, usage)
        if usages[usage]['quota'] is None:
            usages[usage]['quota'] = float("inf")
            usages[usage]['available'] = float("inf")
        else:
            usages[usage]['available'] = usages[usage]['quota'] - \
                                         usages[usage]['used']

    return usages


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
    return cinderclient(request).volumes.list()


def volume_get(request, volume_id):
    return cinderclient(request).volumes.get(volume_id)


def volume_instance_list(request, instance_id):
    return novaclient(request).volumes.get_server_volumes(instance_id)


def volume_create(request, size, name, description):
    return cinderclient(request).volumes.create(size, display_name=name,
            display_description=description)


def volume_delete(request, volume_id):
    cinderclient(request).volumes.delete(volume_id)


def volume_attach(request, volume_id, instance_id, device):
    novaclient(request).volumes.create_server_volume(instance_id,
                                                     volume_id,
                                                     device)


def volume_detach(request, instance_id, attachment_id):
    novaclient(request).volumes.delete_server_volume(
            instance_id, attachment_id)


def volume_snapshot_list(request):
    return cinderclient(request).volume_snapshots.list()


def volume_snapshot_create(request, volume_id, name, description):
    return cinderclient(request).volume_snapshots.create(
            volume_id, display_name=name, display_description=description)


def volume_snapshot_delete(request, snapshot_id):
    cinderclient(request).volume_snapshots.delete(snapshot_id)


def get_x509_credentials(request):
    return novaclient(request).certs.create()


def get_x509_root_certificate(request):
    return novaclient(request).certs.get()
