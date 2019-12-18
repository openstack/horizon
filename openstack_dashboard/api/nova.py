# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
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

import collections
import logging
from operator import attrgetter

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from novaclient import api_versions
from novaclient import exceptions as nova_exceptions
from novaclient.v2 import instance_action as nova_instance_action
from novaclient.v2 import list_extensions as nova_list_extensions
from novaclient.v2 import servers as nova_servers

from horizon import exceptions as horizon_exceptions
from horizon.utils import memoized

from openstack_dashboard.api import _nova
from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard.utils import settings as utils

LOG = logging.getLogger(__name__)

# API static values
INSTANCE_ACTIVE_STATE = 'ACTIVE'
VOLUME_STATE_AVAILABLE = "available"
DEFAULT_QUOTA_NAME = 'default'


get_microversion = _nova.get_microversion
server_get = _nova.server_get
Server = _nova.Server


def is_feature_available(request, features):
    return bool(get_microversion(request, features))


class VolumeMultiattachNotSupported(horizon_exceptions.HorizonException):
    status_code = 400


class VNCConsole(base.APIDictWrapper):
    """Wrapper for the "console" dictionary.

    Returned by the novaclient.servers.get_vnc_console method.
    """
    _attrs = ['url', 'type']


class SPICEConsole(base.APIDictWrapper):
    """Wrapper for the "console" dictionary.

    Returned by the novaclient.servers.get_spice_console method.
    """
    _attrs = ['url', 'type']


class RDPConsole(base.APIDictWrapper):
    """Wrapper for the "console" dictionary.

    Returned by the novaclient.servers.get_rdp_console method.
    """
    _attrs = ['url', 'type']


class SerialConsole(base.APIDictWrapper):
    """Wrapper for the "console" dictionary.

    Returned by the novaclient.servers.get_serial_console method.
    """
    _attrs = ['url', 'type']


class MKSConsole(base.APIDictWrapper):
    """Wrapper for the "console" dictionary.

    Returned by the novaclient.servers.get_mks_console method.
    """
    _attrs = ['url', 'type']


class Hypervisor(base.APIDictWrapper):
    """Simple wrapper around novaclient.hypervisors.Hypervisor."""

    _attrs = ['manager', '_loaded', '_info', 'hypervisor_hostname', 'id',
              'servers']

    @property
    def servers(self):
        # if hypervisor doesn't have servers, the attribute is not present
        servers = []
        try:
            servers = self._apidict.servers
        except Exception:
            pass

        return servers


class NovaUsage(base.APIResourceWrapper):
    """Simple wrapper around contrib/simple_usage.py."""

    _attrs = ['start', 'server_usages', 'stop', 'tenant_id',
              'total_local_gb_usage', 'total_memory_mb_usage',
              'total_vcpus_usage', 'total_hours']

    def get_summary(self):
        return {'instances': self.total_active_instances,
                'memory_mb': self.memory_mb,
                'vcpus': self.vcpus,
                'vcpu_hours': self.vcpu_hours,
                'local_gb': self.local_gb,
                'disk_gb_hours': self.disk_gb_hours,
                'memory_mb_hours': self.memory_mb_hours}

    @property
    def total_active_instances(self):
        return sum(1 for s in self.server_usages if s['ended_at'] is None)

    @property
    def vcpus(self):
        return sum(s['vcpus'] for s in self.server_usages
                   if s['ended_at'] is None)

    @property
    def vcpu_hours(self):
        return getattr(self, "total_vcpus_usage", 0)

    @property
    def local_gb(self):
        return sum(s['local_gb'] for s in self.server_usages
                   if s['ended_at'] is None)

    @property
    def memory_mb(self):
        return sum(s['memory_mb'] for s in self.server_usages
                   if s['ended_at'] is None)

    @property
    def disk_gb_hours(self):
        return getattr(self, "total_local_gb_usage", 0)

    @property
    def memory_mb_hours(self):
        return getattr(self, "total_memory_mb_usage", 0)


class FlavorExtraSpec(object):
    def __init__(self, flavor_id, key, val):
        self.flavor_id = flavor_id
        self.id = key
        self.key = key
        self.value = val


class QuotaSet(base.QuotaSet):

    # We don't support nova-network, so we exclude nova-network relatd
    # quota fields from the response.
    ignore_quotas = {
        "floating_ips",
        "fixed_ips",
        "security_groups",
        "security_group_rules",
    }


def upgrade_api(request, client, version):
    """Ugrade the nova API to the specified version if possible."""

    min_ver, max_ver = api_versions._get_server_version_range(client)
    if min_ver <= api_versions.APIVersion(version) <= max_ver:
        client = _nova.novaclient(request, version)
    return client


@profiler.trace
def server_vnc_console(request, instance_id, console_type='novnc'):
    nc = _nova.novaclient(request)
    console = nc.servers.get_vnc_console(instance_id, console_type)
    return VNCConsole(console['console'])


@profiler.trace
def server_spice_console(request, instance_id, console_type='spice-html5'):
    nc = _nova.novaclient(request)
    console = nc.servers.get_spice_console(instance_id, console_type)
    return SPICEConsole(console['console'])


@profiler.trace
def server_rdp_console(request, instance_id, console_type='rdp-html5'):
    nc = _nova.novaclient(request)
    console = nc.servers.get_rdp_console(instance_id, console_type)
    return RDPConsole(console['console'])


@profiler.trace
def server_serial_console(request, instance_id, console_type='serial'):
    nc = _nova.novaclient(request)
    console = nc.servers.get_serial_console(instance_id, console_type)
    return SerialConsole(console['console'])


@profiler.trace
def server_mks_console(request, instance_id, console_type='mks'):
    microver = get_microversion(request, "remote_console_mks")
    nc = _nova.novaclient(request, microver)
    console = nc.servers.get_mks_console(instance_id, console_type)
    return MKSConsole(console['remote_console'])


@profiler.trace
def flavor_create(request, name, memory, vcpu, disk, flavorid='auto',
                  ephemeral=0, swap=0, metadata=None, is_public=True,
                  rxtx_factor=1):
    flavor = _nova.novaclient(request).flavors.create(name, memory, vcpu, disk,
                                                      flavorid=flavorid,
                                                      ephemeral=ephemeral,
                                                      swap=swap,
                                                      is_public=is_public,
                                                      rxtx_factor=rxtx_factor)
    if (metadata):
        flavor_extra_set(request, flavor.id, metadata)
    return flavor


@profiler.trace
def flavor_delete(request, flavor_id):
    _nova.novaclient(request).flavors.delete(flavor_id)


@profiler.trace
def flavor_get(request, flavor_id, get_extras=False):
    flavor = _nova.novaclient(request).flavors.get(flavor_id)
    if get_extras:
        flavor.extras = flavor_get_extras(request, flavor.id, True, flavor)
    return flavor


@profiler.trace
@memoized.memoized
def flavor_list(request, is_public=True, get_extras=False):
    """Get the list of available instance sizes (flavors)."""
    flavors = _nova.novaclient(request).flavors.list(is_public=is_public)
    if get_extras:
        for flavor in flavors:
            flavor.extras = flavor_get_extras(request, flavor.id, True, flavor)
    return flavors


@profiler.trace
def update_pagination(entities, page_size, marker, reversed_order=False):
    has_more_data = has_prev_data = False
    if len(entities) > page_size:
        has_more_data = True
        entities.pop()
        if marker is not None:
            has_prev_data = True
    # first page condition when reached via prev back
    elif reversed_order and marker is not None:
        has_more_data = True
    # last page condition
    elif marker is not None:
        has_prev_data = True

    # restore the original ordering here
    if reversed_order:
        entities.reverse()

    return entities, has_more_data, has_prev_data


@profiler.trace
@memoized.memoized
def flavor_list_paged(request, is_public=True, get_extras=False, marker=None,
                      paginate=False, sort_key="name", sort_dir="desc",
                      reversed_order=False):
    """Get the list of available instance sizes (flavors)."""
    has_more_data = False
    has_prev_data = False

    if paginate:
        if reversed_order:
            sort_dir = 'desc' if sort_dir == 'asc' else 'asc'
        page_size = utils.get_page_size(request)
        flavors = _nova.novaclient(request).flavors.list(is_public=is_public,
                                                         marker=marker,
                                                         limit=page_size + 1,
                                                         sort_key=sort_key,
                                                         sort_dir=sort_dir)
        flavors, has_more_data, has_prev_data = update_pagination(
            flavors, page_size, marker, reversed_order)
    else:
        flavors = _nova.novaclient(request).flavors.list(is_public=is_public)

    if get_extras:
        for flavor in flavors:
            flavor.extras = flavor_get_extras(request, flavor.id, True, flavor)

    return (flavors, has_more_data, has_prev_data)


@profiler.trace
@memoized.memoized
def flavor_access_list(request, flavor=None):
    """Get the list of access instance sizes (flavors)."""
    return _nova.novaclient(request).flavor_access.list(flavor=flavor)


@profiler.trace
def add_tenant_to_flavor(request, flavor, tenant):
    """Add a tenant to the given flavor access list."""
    return _nova.novaclient(request).flavor_access.add_tenant_access(
        flavor=flavor, tenant=tenant)


@profiler.trace
def remove_tenant_from_flavor(request, flavor, tenant):
    """Remove a tenant from the given flavor access list."""
    return _nova.novaclient(request).flavor_access.remove_tenant_access(
        flavor=flavor, tenant=tenant)


@profiler.trace
def flavor_get_extras(request, flavor_id, raw=False, flavor=None):
    """Get flavor extra specs."""
    if flavor is None:
        flavor = _nova.novaclient(request).flavors.get(flavor_id)
    extras = flavor.get_keys()
    if raw:
        return extras
    return [FlavorExtraSpec(flavor_id, key, value) for
            key, value in extras.items()]


@profiler.trace
def flavor_extra_delete(request, flavor_id, keys):
    """Unset the flavor extra spec keys."""
    flavor = _nova.novaclient(request).flavors.get(flavor_id)
    return flavor.unset_keys(keys)


@profiler.trace
def flavor_extra_set(request, flavor_id, metadata):
    """Set the flavor extra spec keys."""
    flavor = _nova.novaclient(request).flavors.get(flavor_id)
    if (not metadata):  # not a way to delete keys
        return None
    return flavor.set_keys(metadata)


@profiler.trace
def snapshot_create(request, instance_id, name):
    return _nova.novaclient(request).servers.create_image(instance_id, name)


@profiler.trace
def keypair_create(request, name, key_type='ssh'):
    microversion = get_microversion(request, 'key_types')
    return _nova.novaclient(request, microversion).\
        keypairs.create(name, key_type=key_type)


@profiler.trace
def keypair_import(request, name, public_key, key_type='ssh'):
    microversion = get_microversion(request, 'key_types')
    return _nova.novaclient(request, microversion).\
        keypairs.create(name, public_key, key_type)


@profiler.trace
def keypair_delete(request, name):
    _nova.novaclient(request).keypairs.delete(name)


@profiler.trace
def keypair_list(request):
    microversion = get_microversion(request, 'key_type_list')
    return _nova.novaclient(request, microversion).keypairs.list()


@profiler.trace
def keypair_get(request, name):
    return _nova.novaclient(request).keypairs.get(name)


@profiler.trace
def server_create(request, name, image, flavor, key_name, user_data,
                  security_groups, block_device_mapping=None,
                  block_device_mapping_v2=None, nics=None,
                  availability_zone=None, instance_count=1, admin_pass=None,
                  disk_config=None, config_drive=None, meta=None,
                  scheduler_hints=None, description=None):
    microversion = get_microversion(request, ("instance_description",
                                              "auto_allocated_network"))
    nova_client = _nova.novaclient(request, version=microversion)

    # NOTE(amotoki): Handling auto allocated network
    # Nova API 2.37 or later, it accepts a special string 'auto' for nics
    # which means nova uses a network that is available for a current project
    # if one exists and otherwise it creates a network automatically.
    # This special handling is processed here as JS side assumes 'nics'
    # is a list and it is easiest to handle it here.
    if nics:
        is_auto_allocate = any(nic.get('net-id') == '__auto_allocate__'
                               for nic in nics)
        if is_auto_allocate:
            nics = 'auto'

    kwargs = {}
    if description is not None:
        kwargs['description'] = description

    return Server(nova_client.servers.create(
        name.strip(), image, flavor, userdata=user_data,
        security_groups=security_groups,
        key_name=key_name, block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics, availability_zone=availability_zone,
        min_count=instance_count, admin_pass=admin_pass,
        disk_config=disk_config, config_drive=config_drive,
        meta=meta, scheduler_hints=scheduler_hints, **kwargs), request)


@profiler.trace
def server_delete(request, instance_id):
    _nova.novaclient(request).servers.delete(instance_id)
    # Session is available and consistent for the current view
    # among Horizon django servers even in load-balancing setup,
    # so only the view listing the servers will recognize it as
    # own DeleteInstance action performed. Note that dict is passed
    # by reference in python. Quote from django's developer manual:
    # " You can read it and write to request.session at any point
    #   in your view. You can edit it multiple times."
    request.session['server_deleted'] = instance_id


def get_novaclient_with_locked_status(request):
    microversion = get_microversion(request, "locked_attribute")
    return _nova.novaclient(request, version=microversion)


@profiler.trace
def server_list_paged(request,
                      search_opts=None,
                      detailed=True,
                      sort_dir="desc"):
    has_more_data = False
    has_prev_data = False
    nova_client = get_novaclient_with_locked_status(request)
    page_size = utils.get_page_size(request)
    search_opts = {} if search_opts is None else search_opts
    marker = search_opts.get('marker', None)

    if not search_opts.get('all_tenants', False):
        search_opts['project_id'] = request.user.tenant_id

    if search_opts.pop('paginate', False):
        reversed_order = sort_dir == "asc"
        LOG.debug("Notify received on deleted server: %r",
                  ('server_deleted' in request.session))
        deleted = request.session.pop('server_deleted',
                                      None)
        view_marker = 'possibly_deleted' if deleted and marker else 'ok'
        search_opts['marker'] = deleted if deleted else marker
        search_opts['limit'] = page_size + 1
        # NOTE(amotoki): It looks like the 'sort_keys' must be unique to make
        # the pagination in the nova API works as expected. Multiple servers
        # can have a same 'created_at' as its resolution is a second.
        # To ensure the uniqueness we add 'uuid' to the sort keys.
        # 'display_name' is added before 'uuid' to list servers in the
        # alphabetical order.
        sort_keys = ['created_at', 'display_name', 'uuid']

        servers = [Server(s, request)
                   for s in nova_client.servers.list(detailed, search_opts,
                                                     sort_keys=sort_keys,
                                                     sort_dirs=[sort_dir] * 3)]

        if view_marker == 'possibly_deleted':
            if not servers:
                view_marker = 'head_deleted'
                reversed_order = False
                servers = [Server(s, request)
                           for s in
                           nova_client.servers.list(detailed,
                                                    search_opts,
                                                    sort_keys=sort_keys,
                                                    sort_dirs=['desc'] * 3)]
            if not servers:
                view_marker = 'tail_deleted'
                reversed_order = True
                servers = [Server(s, request)
                           for s in
                           nova_client.servers.list(detailed,
                                                    search_opts,
                                                    sort_keys=sort_keys,
                                                    sort_dirs=['asc'] * 3)]
        (servers, has_more_data, has_prev_data) = update_pagination(
            servers, page_size, marker, reversed_order)
        has_prev_data = (False
                         if view_marker == 'head_deleted'
                         else has_prev_data)
        has_more_data = (False
                         if view_marker == 'tail_deleted'
                         else has_more_data)
    else:
        servers = [Server(s, request)
                   for s in nova_client.servers.list(detailed, search_opts)]
    return (servers, has_more_data, has_prev_data)


@profiler.trace
def server_list(request, search_opts=None, detailed=True):
    (servers, has_more_data, _) = server_list_paged(request,
                                                    search_opts,
                                                    detailed)
    return (servers, has_more_data)


@profiler.trace
def server_console_output(request, instance_id, tail_length=None):
    """Gets console output of an instance."""
    nc = _nova.novaclient(request)
    return nc.servers.get_console_output(instance_id, length=tail_length)


@profiler.trace
def server_pause(request, instance_id):
    _nova.novaclient(request).servers.pause(instance_id)


@profiler.trace
def server_unpause(request, instance_id):
    _nova.novaclient(request).servers.unpause(instance_id)


@profiler.trace
def server_suspend(request, instance_id):
    _nova.novaclient(request).servers.suspend(instance_id)


@profiler.trace
def server_resume(request, instance_id):
    _nova.novaclient(request).servers.resume(instance_id)


@profiler.trace
def server_shelve(request, instance_id):
    _nova.novaclient(request).servers.shelve(instance_id)


@profiler.trace
def server_unshelve(request, instance_id):
    _nova.novaclient(request).servers.unshelve(instance_id)


@profiler.trace
def server_reboot(request, instance_id, soft_reboot=False):
    hardness = nova_servers.REBOOT_HARD
    if soft_reboot:
        hardness = nova_servers.REBOOT_SOFT
    _nova.novaclient(request).servers.reboot(instance_id, hardness)


@profiler.trace
def server_rebuild(request, instance_id, image_id, password=None,
                   disk_config=None, description=None):
    kwargs = {}
    if description:
        kwargs['description'] = description
    nc = _nova.get_novaclient_with_instance_desc(request)
    return nc.servers.rebuild(instance_id, image_id, password, disk_config,
                              **kwargs)


@profiler.trace
def server_update(request, instance_id, name, description=None):
    nc = _nova.get_novaclient_with_instance_desc(request)
    return nc.servers.update(instance_id, name=name.strip(),
                             description=description)


@profiler.trace
def server_migrate(request, instance_id):
    _nova.novaclient(request).servers.migrate(instance_id)


@profiler.trace
def server_live_migrate(request, instance_id, host, block_migration=False,
                        disk_over_commit=False):
    _nova.novaclient(request).servers.live_migrate(instance_id, host,
                                                   block_migration,
                                                   disk_over_commit)


@profiler.trace
def server_resize(request, instance_id, flavor, disk_config=None, **kwargs):
    _nova.novaclient(request).servers.resize(instance_id, flavor,
                                             disk_config, **kwargs)


@profiler.trace
def server_confirm_resize(request, instance_id):
    _nova.novaclient(request).servers.confirm_resize(instance_id)


@profiler.trace
def server_revert_resize(request, instance_id):
    _nova.novaclient(request).servers.revert_resize(instance_id)


@profiler.trace
def server_start(request, instance_id):
    _nova.novaclient(request).servers.start(instance_id)


@profiler.trace
def server_stop(request, instance_id):
    _nova.novaclient(request).servers.stop(instance_id)


@profiler.trace
def server_lock(request, instance_id):
    microversion = get_microversion(request, "locked_attribute")
    _nova.novaclient(request, version=microversion).servers.lock(instance_id)


@profiler.trace
def server_unlock(request, instance_id):
    microversion = get_microversion(request, "locked_attribute")
    _nova.novaclient(request, version=microversion).servers.unlock(instance_id)


@profiler.trace
def server_metadata_update(request, instance_id, metadata):
    _nova.novaclient(request).servers.set_meta(instance_id, metadata)


@profiler.trace
def server_metadata_delete(request, instance_id, keys):
    _nova.novaclient(request).servers.delete_meta(instance_id, keys)


@profiler.trace
def server_rescue(request, instance_id, password=None, image=None):
    _nova.novaclient(request).servers.rescue(instance_id,
                                             password=password,
                                             image=image)


@profiler.trace
def server_unrescue(request, instance_id):
    _nova.novaclient(request).servers.unrescue(instance_id)


@profiler.trace
def tenant_quota_get(request, tenant_id):
    return QuotaSet(_nova.novaclient(request).quotas.get(tenant_id))


@profiler.trace
def tenant_quota_update(request, tenant_id, **kwargs):
    if kwargs:
        _nova.novaclient(request).quotas.update(tenant_id, **kwargs)


@profiler.trace
def default_quota_get(request, tenant_id):
    return QuotaSet(_nova.novaclient(request).quotas.defaults(tenant_id))


@profiler.trace
def default_quota_update(request, **kwargs):
    _nova.novaclient(request).quota_classes.update(DEFAULT_QUOTA_NAME,
                                                   **kwargs)


def _get_usage_marker(usage):
    marker = None
    if hasattr(usage, 'server_usages') and usage.server_usages:
        marker = usage.server_usages[-1].get('instance_id')
    return marker


def _get_usage_list_marker(usage_list):
    marker = None
    if usage_list:
        marker = _get_usage_marker(usage_list[-1])
    return marker


def _merge_usage(usage, next_usage):
    usage.server_usages.extend(next_usage.server_usages)
    usage.total_hours += next_usage.total_hours
    usage.total_memory_mb_usage += next_usage.total_memory_mb_usage
    usage.total_vcpus_usage += next_usage.total_vcpus_usage
    usage.total_local_gb_usage += next_usage.total_local_gb_usage


def _merge_usage_list(usages, next_usage_list):
    for next_usage in next_usage_list:
        if next_usage.tenant_id in usages:
            _merge_usage(usages[next_usage.tenant_id], next_usage)
        else:
            usages[next_usage.tenant_id] = next_usage


@profiler.trace
def usage_get(request, tenant_id, start, end):
    client = upgrade_api(request, _nova.novaclient(request), '2.40')
    usage = client.usage.get(tenant_id, start, end)
    if client.api_version >= api_versions.APIVersion('2.40'):
        # If the number of instances used to calculate the usage is greater
        # than max_limit, the usage will be split across multiple requests
        # and the responses will need to be merged back together.
        marker = _get_usage_marker(usage)
        while marker:
            next_usage = client.usage.get(tenant_id, start, end, marker=marker)
            marker = _get_usage_marker(next_usage)
            if marker:
                _merge_usage(usage, next_usage)
    return NovaUsage(usage)


@profiler.trace
def usage_list(request, start, end):
    client = upgrade_api(request, _nova.novaclient(request), '2.40')
    usage_list = client.usage.list(start, end, True)
    if client.api_version >= api_versions.APIVersion('2.40'):
        # If the number of instances used to calculate the usage is greater
        # than max_limit, the usage will be split across multiple requests
        # and the responses will need to be merged back together.
        usages = collections.OrderedDict()
        _merge_usage_list(usages, usage_list)
        marker = _get_usage_list_marker(usage_list)
        while marker:
            next_usage_list = client.usage.list(start, end, True,
                                                marker=marker)
            marker = _get_usage_list_marker(next_usage_list)
            if marker:
                _merge_usage_list(usages, next_usage_list)
        usage_list = usages.values()
    return [NovaUsage(u) for u in usage_list]


@profiler.trace
def get_password(request, instance_id, private_key=None):
    return _nova.novaclient(request).servers.get_password(instance_id,
                                                          private_key)


@profiler.trace
def instance_volume_attach(request, volume_id, instance_id, device):
    # If we have a multiattach volume, we need to use microversion>=2.60.
    volume = cinder.volume_get(request, volume_id)
    if volume.multiattach:
        version = get_microversion(request, 'multiattach')
        if version:
            client = _nova.novaclient(request, version)
        else:
            raise VolumeMultiattachNotSupported(
                _('Multiattach volumes are not yet supported.'))
    else:
        client = _nova.novaclient(request)
    return client.volumes.create_server_volume(
        instance_id, volume_id, device)


@profiler.trace
def instance_volume_detach(request, instance_id, att_id):
    return _nova.novaclient(request).volumes.delete_server_volume(instance_id,
                                                                  att_id)


@profiler.trace
def instance_volumes_list(request, instance_id):
    volumes = _nova.novaclient(request).volumes.get_server_volumes(instance_id)

    for volume in volumes:
        volume_data = cinder.cinderclient(request).volumes.get(volume.id)
        volume.name = cinder.Volume(volume_data).name

    return volumes


@profiler.trace
def hypervisor_list(request):
    return _nova.novaclient(request).hypervisors.list()


@profiler.trace
def hypervisor_stats(request):
    return _nova.novaclient(request).hypervisors.statistics()


@profiler.trace
def hypervisor_search(request, query, servers=True):
    return _nova.novaclient(request).hypervisors.search(query, servers)


@profiler.trace
def evacuate_host(request, host, target=None, on_shared_storage=False):
    # TODO(jmolle) This should be change for nova atomic api host_evacuate
    hypervisors = _nova.novaclient(request).hypervisors.search(host, True)
    response = []
    err_code = None
    for hypervisor in hypervisors:
        hyper = Hypervisor(hypervisor)
        # if hypervisor doesn't have servers, the attribute is not present
        for server in hyper.servers:
            try:
                _nova.novaclient(request).servers.evacuate(server['uuid'],
                                                           target,
                                                           on_shared_storage)
            except nova_exceptions.ClientException as err:
                err_code = err.code
                msg = _("Name: %(name)s ID: %(uuid)s")
                msg = msg % {'name': server['name'], 'uuid': server['uuid']}
                response.append(msg)

    if err_code:
        msg = _('Failed to evacuate instances: %s') % ', '.join(response)
        raise nova_exceptions.ClientException(err_code, msg)

    return True


@profiler.trace
def migrate_host(request, host, live_migrate=False, disk_over_commit=False,
                 block_migration=False):
    nc = _nova.novaclient(request)
    hypervisors = nc.hypervisors.search(host, True)
    response = []
    err_code = None
    for hyper in hypervisors:
        for server in getattr(hyper, "servers", []):
            try:
                if live_migrate:
                    instance = server_get(request, server['uuid'])

                    # Checking that instance can be live-migrated
                    if instance.status in ["ACTIVE", "PAUSED"]:
                        nc.servers.live_migrate(
                            server['uuid'],
                            None,
                            block_migration,
                            disk_over_commit
                        )
                    else:
                        nc.servers.migrate(server['uuid'])
                else:
                    nc.servers.migrate(server['uuid'])
            except nova_exceptions.ClientException as err:
                err_code = err.code
                msg = _("Name: %(name)s ID: %(uuid)s")
                msg = msg % {'name': server['name'], 'uuid': server['uuid']}
                response.append(msg)

    if err_code:
        msg = _('Failed to migrate instances: %s') % ', '.join(response)
        raise nova_exceptions.ClientException(err_code, msg)

    return True


@profiler.trace
def tenant_absolute_limits(request, reserved=False, tenant_id=None):
    # Nova does not allow to specify tenant_id for non-admin users
    # even if tenant_id matches a tenant_id of the user.
    if tenant_id == request.user.tenant_id:
        tenant_id = None
    limits = _nova.novaclient(request).limits.get(reserved=reserved,
                                                  tenant_id=tenant_id).absolute
    limits_dict = {}
    for limit in limits:
        if limit.value < 0:
            # Workaround for nova bug 1370867 that absolute_limits
            # returns negative value for total.*Used instead of 0.
            # For such case, replace negative values with 0.
            if limit.name.startswith('total') and limit.name.endswith('Used'):
                limits_dict[limit.name] = 0
            else:
                # -1 is used to represent unlimited quotas
                limits_dict[limit.name] = float("inf")
        else:
            limits_dict[limit.name] = limit.value
    return limits_dict


@profiler.trace
def availability_zone_list(request, detailed=False):
    nc = _nova.novaclient(request)
    zones = nc.availability_zones.list(detailed=detailed)
    zones.sort(key=attrgetter('zoneName'))
    return zones


@profiler.trace
def server_group_list(request):
    return _nova.novaclient(request).server_groups.list()


@profiler.trace
def server_group_create(request, **kwargs):
    microversion = get_microversion(request, "servergroup_soft_policies")
    nc = _nova.novaclient(request, version=microversion)
    return nc.server_groups.create(**kwargs)


@profiler.trace
def server_group_delete(request, servergroup_id):
    _nova.novaclient(request).server_groups.delete(servergroup_id)


@profiler.trace
def server_group_get(request, servergroup_id):
    microversion = get_microversion(request, "servergroup_user_info")
    return _nova.novaclient(request, version=microversion).server_groups.get(
        servergroup_id)


@profiler.trace
def service_list(request, binary=None):
    return _nova.novaclient(request).services.list(binary=binary)


@profiler.trace
def service_enable(request, host, binary):
    return _nova.novaclient(request).services.enable(host, binary)


@profiler.trace
def service_disable(request, host, binary, reason=None):
    if reason:
        return _nova.novaclient(request).services.disable_log_reason(
            host, binary, reason)
    else:
        return _nova.novaclient(request).services.disable(host, binary)


@profiler.trace
def aggregate_details_list(request):
    result = []
    c = _nova.novaclient(request)
    for aggregate in c.aggregates.list():
        result.append(c.aggregates.get_details(aggregate.id))
    return result


@profiler.trace
def aggregate_create(request, name, availability_zone=None):
    return _nova.novaclient(request).aggregates.create(name, availability_zone)


@profiler.trace
def aggregate_delete(request, aggregate_id):
    return _nova.novaclient(request).aggregates.delete(aggregate_id)


@profiler.trace
def aggregate_get(request, aggregate_id):
    return _nova.novaclient(request).aggregates.get(aggregate_id)


@profiler.trace
def aggregate_update(request, aggregate_id, values):
    _nova.novaclient(request).aggregates.update(aggregate_id, values)


@profiler.trace
def aggregate_set_metadata(request, aggregate_id, metadata):
    return _nova.novaclient(request).aggregates.set_metadata(aggregate_id,
                                                             metadata)


@profiler.trace
def add_host_to_aggregate(request, aggregate_id, host):
    _nova.novaclient(request).aggregates.add_host(aggregate_id, host)


@profiler.trace
def remove_host_from_aggregate(request, aggregate_id, host):
    _nova.novaclient(request).aggregates.remove_host(aggregate_id, host)


@profiler.trace
def interface_attach(request,
                     server, port_id=None, net_id=None, fixed_ip=None):
    return _nova.novaclient(request).servers.interface_attach(
        server, port_id, net_id, fixed_ip)


@profiler.trace
def interface_detach(request, server, port_id):
    return _nova.novaclient(request).servers.interface_detach(server, port_id)


@profiler.trace
@memoized.memoized
def list_extensions(request):
    """List all nova extensions, except the ones in the blacklist."""
    blacklist = set(settings.OPENSTACK_NOVA_EXTENSIONS_BLACKLIST)
    nova_api = _nova.novaclient(request)
    return tuple(
        extension for extension in
        nova_list_extensions.ListExtManager(nova_api).show_all()
        if extension.name not in blacklist
    )


@profiler.trace
@memoized.memoized
def extension_supported(extension_name, request):
    """Determine if nova supports a given extension name.

    Example values for the extension_name include AdminActions, ConsoleOutput,
    etc.
    """
    for ext in list_extensions(request):
        if ext.name == extension_name:
            return True
    return False


@profiler.trace
def can_set_server_password():
    return utils.get_dict_config('OPENSTACK_HYPERVISOR_FEATURES',
                                 'can_set_password')


@profiler.trace
def instance_action_list(request, instance_id):
    return nova_instance_action.InstanceActionManager(
        _nova.novaclient(request)).list(instance_id)


@profiler.trace
def can_set_mount_point():
    """Return the Hypervisor's capability of setting mount points."""
    return utils.get_dict_config('OPENSTACK_HYPERVISOR_FEATURES',
                                 'can_set_mount_point')


@profiler.trace
def requires_keypair():
    return utils.get_dict_config('OPENSTACK_HYPERVISOR_FEATURES',
                                 'requires_keypair')


def can_set_quotas():
    return utils.get_dict_config('OPENSTACK_HYPERVISOR_FEATURES',
                                 'enable_quotas')
