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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from novaclient import api_versions
from novaclient import client as nova_client
from novaclient import exceptions as nova_exceptions
from novaclient.v2 import instance_action as nova_instance_action
from novaclient.v2 import list_extensions as nova_list_extensions
from novaclient.v2 import servers as nova_servers

from horizon import exceptions as horizon_exceptions
from horizon.utils import functions as utils
from horizon.utils.memoized import memoized
from horizon.utils.memoized import memoized_with_request

from openstack_dashboard.api import base
from openstack_dashboard.api import microversions
from openstack_dashboard.contrib.developer.profiler import api as profiler

LOG = logging.getLogger(__name__)

# Supported compute versions
VERSIONS = base.APIVersionManager("compute", preferred_version=2)
VERSIONS.load_supported_version(1.1, {"client": nova_client, "version": 1.1})
VERSIONS.load_supported_version(2, {"client": nova_client, "version": 2})

# API static values
INSTANCE_ACTIVE_STATE = 'ACTIVE'
VOLUME_STATE_AVAILABLE = "available"
DEFAULT_QUOTA_NAME = 'default'
INSECURE = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
CACERT = getattr(settings, 'OPENSTACK_SSL_CACERT', None)


@memoized
def get_microversion(request, feature):
    client = novaclient(request)
    min_ver, max_ver = api_versions._get_server_version_range(client)
    return (microversions.get_microversion_for_feature(
        'nova', feature, api_versions.APIVersion, min_ver, max_ver))


def is_feature_available(request, feature):
    return bool(get_microversion(request, feature))


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


class Server(base.APIResourceWrapper):
    """Simple wrapper around novaclient.server.Server.

    Preserves the request info so image name can later be retrieved.
    """
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links',
              'metadata', 'name', 'private_ip', 'public_ip', 'status', 'uuid',
              'image_name', 'VirtualInterfaces', 'flavor', 'key_name', 'fault',
              'tenant_id', 'user_id', 'created', 'locked',
              'OS-EXT-STS:power_state', 'OS-EXT-STS:task_state',
              'OS-EXT-SRV-ATTR:instance_name', 'OS-EXT-SRV-ATTR:host',
              'OS-EXT-AZ:availability_zone', 'OS-DCF:diskConfig']

    def __init__(self, apiresource, request):
        super(Server, self).__init__(apiresource)
        self.request = request

    # TODO(gabriel): deprecate making a call to Glance as a fallback.
    @property
    def image_name(self):
        import glanceclient.exc as glance_exceptions
        from openstack_dashboard.api import glance

        if not self.image:
            return None
        if hasattr(self.image, 'name'):
            return self.image.name
        if 'name' in self.image:
            return self.image['name']
        else:
            try:
                image = glance.image_get(self.request, self.image['id'])
                self.image['name'] = image.name
                return image.name
            except (glance_exceptions.ClientException,
                    horizon_exceptions.ServiceCatalogException):
                self.image['name'] = None
                return None

    @property
    def internal_name(self):
        return getattr(self, 'OS-EXT-SRV-ATTR:instance_name', "")

    @property
    def availability_zone(self):
        return getattr(self, 'OS-EXT-AZ:availability_zone', "")

    @property
    def host_server(self):
        return getattr(self, 'OS-EXT-SRV-ATTR:host', '')


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


def get_auth_params_from_request(request):
    """Extracts properties needed by novaclient call from the request object.

    These will be used to memoize the calls to novaclient.
    """
    return (
        request.user.username,
        request.user.token.id,
        request.user.tenant_id,
        request.user.token.project.get('domain_id'),
        base.url_for(request, 'compute'),
        base.url_for(request, 'identity')
    )


@memoized_with_request(get_auth_params_from_request)
def novaclient(request_auth_params, version=None):
    (
        username,
        token_id,
        project_id,
        project_domain_id,
        nova_url,
        auth_url
    ) = request_auth_params
    if version is None:
        version = VERSIONS.get_active_version()['version']
    c = nova_client.Client(version,
                           username,
                           token_id,
                           project_id=project_id,
                           project_domain_id=project_domain_id,
                           auth_url=auth_url,
                           insecure=INSECURE,
                           cacert=CACERT,
                           http_log_debug=settings.DEBUG,
                           auth_token=token_id,
                           endpoint_override=nova_url)
    return c


def upgrade_api(request, client, version):
    """Ugrade the nova API to the specified version if possible."""

    min_ver, max_ver = api_versions._get_server_version_range(client)
    if min_ver <= api_versions.APIVersion(version) <= max_ver:
        client = novaclient(request, version)
    return client


@profiler.trace
def server_vnc_console(request, instance_id, console_type='novnc'):
    return VNCConsole(novaclient(request).servers.get_vnc_console(
        instance_id, console_type)['console'])


@profiler.trace
def server_spice_console(request, instance_id, console_type='spice-html5'):
    return SPICEConsole(novaclient(request).servers.get_spice_console(
        instance_id, console_type)['console'])


@profiler.trace
def server_rdp_console(request, instance_id, console_type='rdp-html5'):
    return RDPConsole(novaclient(request).servers.get_rdp_console(
        instance_id, console_type)['console'])


@profiler.trace
def server_serial_console(request, instance_id, console_type='serial'):
    return SerialConsole(novaclient(request).servers.get_serial_console(
        instance_id, console_type)['console'])


@profiler.trace
def flavor_create(request, name, memory, vcpu, disk, flavorid='auto',
                  ephemeral=0, swap=0, metadata=None, is_public=True,
                  rxtx_factor=1):
    flavor = novaclient(request).flavors.create(name, memory, vcpu, disk,
                                                flavorid=flavorid,
                                                ephemeral=ephemeral,
                                                swap=swap, is_public=is_public,
                                                rxtx_factor=rxtx_factor)
    if (metadata):
        flavor_extra_set(request, flavor.id, metadata)
    return flavor


@profiler.trace
def flavor_delete(request, flavor_id):
    novaclient(request).flavors.delete(flavor_id)


@profiler.trace
def flavor_get(request, flavor_id, get_extras=False):
    flavor = novaclient(request).flavors.get(flavor_id)
    if get_extras:
        flavor.extras = flavor_get_extras(request, flavor.id, True, flavor)
    return flavor


@profiler.trace
@memoized
def flavor_list(request, is_public=True, get_extras=False):
    """Get the list of available instance sizes (flavors)."""
    flavors = novaclient(request).flavors.list(is_public=is_public)
    if get_extras:
        for flavor in flavors:
            flavor.extras = flavor_get_extras(request, flavor.id, True, flavor)
    return flavors


@profiler.trace
def update_pagination(entities, page_size, marker, sort_dir, sort_key,
                      reversed_order):
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
        entities = sorted(entities, key=lambda entity:
                          (getattr(entity, sort_key) or '').lower(),
                          reverse=(sort_dir == 'asc'))

    return entities, has_more_data, has_prev_data


@profiler.trace
@memoized
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
        flavors = novaclient(request).flavors.list(is_public=is_public,
                                                   marker=marker,
                                                   limit=page_size + 1,
                                                   sort_key=sort_key,
                                                   sort_dir=sort_dir)
        flavors, has_more_data, has_prev_data = update_pagination(
            flavors, page_size, marker, sort_dir, sort_key, reversed_order)
    else:
        flavors = novaclient(request).flavors.list(is_public=is_public)

    if get_extras:
        for flavor in flavors:
            flavor.extras = flavor_get_extras(request, flavor.id, True, flavor)

    return (flavors, has_more_data, has_prev_data)


@profiler.trace
@memoized
def flavor_access_list(request, flavor=None):
    """Get the list of access instance sizes (flavors)."""
    return novaclient(request).flavor_access.list(flavor=flavor)


@profiler.trace
def add_tenant_to_flavor(request, flavor, tenant):
    """Add a tenant to the given flavor access list."""
    return novaclient(request).flavor_access.add_tenant_access(
        flavor=flavor, tenant=tenant)


@profiler.trace
def remove_tenant_from_flavor(request, flavor, tenant):
    """Remove a tenant from the given flavor access list."""
    return novaclient(request).flavor_access.remove_tenant_access(
        flavor=flavor, tenant=tenant)


@profiler.trace
def flavor_get_extras(request, flavor_id, raw=False, flavor=None):
    """Get flavor extra specs."""
    if flavor is None:
        flavor = novaclient(request).flavors.get(flavor_id)
    extras = flavor.get_keys()
    if raw:
        return extras
    return [FlavorExtraSpec(flavor_id, key, value) for
            key, value in extras.items()]


@profiler.trace
def flavor_extra_delete(request, flavor_id, keys):
    """Unset the flavor extra spec keys."""
    flavor = novaclient(request).flavors.get(flavor_id)
    return flavor.unset_keys(keys)


@profiler.trace
def flavor_extra_set(request, flavor_id, metadata):
    """Set the flavor extra spec keys."""
    flavor = novaclient(request).flavors.get(flavor_id)
    if (not metadata):  # not a way to delete keys
        return None
    return flavor.set_keys(metadata)


@profiler.trace
def snapshot_create(request, instance_id, name):
    return novaclient(request).servers.create_image(instance_id, name)


@profiler.trace
def keypair_create(request, name):
    return novaclient(request).keypairs.create(name)


@profiler.trace
def keypair_import(request, name, public_key):
    return novaclient(request).keypairs.create(name, public_key)


@profiler.trace
def keypair_delete(request, keypair_id):
    novaclient(request).keypairs.delete(keypair_id)


@profiler.trace
def keypair_list(request):
    return novaclient(request).keypairs.list()


@profiler.trace
def keypair_get(request, keypair_id):
    return novaclient(request).keypairs.get(keypair_id)


@profiler.trace
def server_create(request, name, image, flavor, key_name, user_data,
                  security_groups, block_device_mapping=None,
                  block_device_mapping_v2=None, nics=None,
                  availability_zone=None, instance_count=1, admin_pass=None,
                  disk_config=None, config_drive=None, meta=None,
                  scheduler_hints=None):
    return Server(novaclient(request).servers.create(
        name.strip(), image, flavor, userdata=user_data,
        security_groups=security_groups,
        key_name=key_name, block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics, availability_zone=availability_zone,
        min_count=instance_count, admin_pass=admin_pass,
        disk_config=disk_config, config_drive=config_drive,
        meta=meta, scheduler_hints=scheduler_hints), request)


@profiler.trace
def server_delete(request, instance_id):
    novaclient(request).servers.delete(instance_id)


def get_novaclient_with_locked_status(request):
    microversion = get_microversion(request, "locked_attribute")
    return novaclient(request, version=microversion)


@profiler.trace
def server_get(request, instance_id):
    return Server(get_novaclient_with_locked_status(request).servers.get(
        instance_id), request)


@profiler.trace
def server_list(request, search_opts=None, detailed=True):
    nova_client = get_novaclient_with_locked_status(request)
    page_size = utils.get_page_size(request)
    paginate = False
    if search_opts is None:
        search_opts = {}
    elif 'paginate' in search_opts:
        paginate = search_opts.pop('paginate')
        if paginate:
            search_opts['limit'] = page_size + 1

    all_tenants = search_opts.get('all_tenants', False)
    if all_tenants:
        search_opts['all_tenants'] = True
    else:
        search_opts['project_id'] = request.user.tenant_id

    servers = [Server(s, request)
               for s in nova_client.servers.list(detailed, search_opts)]

    has_more_data = False
    if paginate and len(servers) > page_size:
        servers.pop(-1)
        has_more_data = True
    elif paginate and len(servers) == getattr(settings, 'API_RESULT_LIMIT',
                                              1000):
        has_more_data = True
    return (servers, has_more_data)


@profiler.trace
def server_console_output(request, instance_id, tail_length=None):
    """Gets console output of an instance."""
    return novaclient(request).servers.get_console_output(instance_id,
                                                          length=tail_length)


@profiler.trace
def server_pause(request, instance_id):
    novaclient(request).servers.pause(instance_id)


@profiler.trace
def server_unpause(request, instance_id):
    novaclient(request).servers.unpause(instance_id)


@profiler.trace
def server_suspend(request, instance_id):
    novaclient(request).servers.suspend(instance_id)


@profiler.trace
def server_resume(request, instance_id):
    novaclient(request).servers.resume(instance_id)


@profiler.trace
def server_shelve(request, instance_id):
    novaclient(request).servers.shelve(instance_id)


@profiler.trace
def server_unshelve(request, instance_id):
    novaclient(request).servers.unshelve(instance_id)


@profiler.trace
def server_reboot(request, instance_id, soft_reboot=False):
    hardness = nova_servers.REBOOT_HARD
    if soft_reboot:
        hardness = nova_servers.REBOOT_SOFT
    novaclient(request).servers.reboot(instance_id, hardness)


@profiler.trace
def server_rebuild(request, instance_id, image_id, password=None,
                   disk_config=None):
    return novaclient(request).servers.rebuild(instance_id, image_id,
                                               password, disk_config)


@profiler.trace
def server_update(request, instance_id, name):
    return novaclient(request).servers.update(instance_id, name=name.strip())


@profiler.trace
def server_migrate(request, instance_id):
    novaclient(request).servers.migrate(instance_id)


@profiler.trace
def server_live_migrate(request, instance_id, host, block_migration=False,
                        disk_over_commit=False):
    novaclient(request).servers.live_migrate(instance_id, host,
                                             block_migration,
                                             disk_over_commit)


@profiler.trace
def server_resize(request, instance_id, flavor, disk_config=None, **kwargs):
    novaclient(request).servers.resize(instance_id, flavor,
                                       disk_config, **kwargs)


@profiler.trace
def server_confirm_resize(request, instance_id):
    novaclient(request).servers.confirm_resize(instance_id)


@profiler.trace
def server_revert_resize(request, instance_id):
    novaclient(request).servers.revert_resize(instance_id)


@profiler.trace
def server_start(request, instance_id):
    novaclient(request).servers.start(instance_id)


@profiler.trace
def server_stop(request, instance_id):
    novaclient(request).servers.stop(instance_id)


@profiler.trace
def server_lock(request, instance_id):
    microversion = get_microversion(request, "locked_attribute")
    novaclient(request, version=microversion).servers.lock(instance_id)


@profiler.trace
def server_unlock(request, instance_id):
    microversion = get_microversion(request, "locked_attribute")
    novaclient(request, version=microversion).servers.unlock(instance_id)


@profiler.trace
def server_metadata_update(request, instance_id, metadata):
    novaclient(request).servers.set_meta(instance_id, metadata)


@profiler.trace
def server_metadata_delete(request, instance_id, keys):
    novaclient(request).servers.delete_meta(instance_id, keys)


@profiler.trace
def tenant_quota_get(request, tenant_id):
    return base.QuotaSet(novaclient(request).quotas.get(tenant_id))


@profiler.trace
def tenant_quota_update(request, tenant_id, **kwargs):
    if kwargs:
        novaclient(request).quotas.update(tenant_id, **kwargs)


@profiler.trace
def default_quota_get(request, tenant_id):
    return base.QuotaSet(novaclient(request).quotas.defaults(tenant_id))


@profiler.trace
def default_quota_update(request, **kwargs):
    novaclient(request).quota_classes.update(DEFAULT_QUOTA_NAME, **kwargs)


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
    client = upgrade_api(request, novaclient(request), '2.40')
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
    client = upgrade_api(request, novaclient(request), '2.40')
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
def virtual_interfaces_list(request, instance_id):
    return novaclient(request).virtual_interfaces.list(instance_id)


@profiler.trace
def get_x509_credentials(request):
    return novaclient(request).certs.create()


@profiler.trace
def get_x509_root_certificate(request):
    return novaclient(request).certs.get()


@profiler.trace
def get_password(request, instance_id, private_key=None):
    return novaclient(request).servers.get_password(instance_id, private_key)


@profiler.trace
def instance_volume_attach(request, volume_id, instance_id, device):
    return novaclient(request).volumes.create_server_volume(instance_id,
                                                            volume_id,
                                                            device)


@profiler.trace
def instance_volume_detach(request, instance_id, att_id):
    return novaclient(request).volumes.delete_server_volume(instance_id,
                                                            att_id)


@profiler.trace
def instance_volumes_list(request, instance_id):
    from openstack_dashboard.api import cinder

    volumes = novaclient(request).volumes.get_server_volumes(instance_id)

    for volume in volumes:
        volume_data = cinder.cinderclient(request).volumes.get(volume.id)
        volume.name = cinder.Volume(volume_data).name

    return volumes


@profiler.trace
def hypervisor_list(request):
    return novaclient(request).hypervisors.list()


@profiler.trace
def hypervisor_stats(request):
    return novaclient(request).hypervisors.statistics()


@profiler.trace
def hypervisor_search(request, query, servers=True):
    return novaclient(request).hypervisors.search(query, servers)


@profiler.trace
def evacuate_host(request, host, target=None, on_shared_storage=False):
    # TODO(jmolle) This should be change for nova atomic api host_evacuate
    hypervisors = novaclient(request).hypervisors.search(host, True)
    response = []
    err_code = None
    for hypervisor in hypervisors:
        hyper = Hypervisor(hypervisor)
        # if hypervisor doesn't have servers, the attribute is not present
        for server in hyper.servers:
            try:
                novaclient(request).servers.evacuate(server['uuid'],
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
    hypervisors = novaclient(request).hypervisors.search(host, True)
    response = []
    err_code = None
    for hyper in hypervisors:
        for server in getattr(hyper, "servers", []):
            try:
                if live_migrate:
                    instance = server_get(request, server['uuid'])

                    # Checking that instance can be live-migrated
                    if instance.status in ["ACTIVE", "PAUSED"]:
                        novaclient(request).servers.live_migrate(
                            server['uuid'],
                            None,
                            block_migration,
                            disk_over_commit
                        )
                    else:
                        novaclient(request).servers.migrate(server['uuid'])
                else:
                    novaclient(request).servers.migrate(server['uuid'])
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
def tenant_absolute_limits(request, reserved=False):
    limits = novaclient(request).limits.get(reserved=reserved).absolute
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
    return novaclient(request).availability_zones.list(detailed=detailed)


@profiler.trace
def server_group_list(request):
    return novaclient(request).server_groups.list()


@profiler.trace
def service_list(request, binary=None):
    return novaclient(request).services.list(binary=binary)


@profiler.trace
def service_enable(request, host, binary):
    return novaclient(request).services.enable(host, binary)


@profiler.trace
def service_disable(request, host, binary, reason=None):
    if reason:
        return novaclient(request).services.disable_log_reason(host,
                                                               binary, reason)
    else:
        return novaclient(request).services.disable(host, binary)


@profiler.trace
def aggregate_details_list(request):
    result = []
    c = novaclient(request)
    for aggregate in c.aggregates.list():
        result.append(c.aggregates.get_details(aggregate.id))
    return result


@profiler.trace
def aggregate_create(request, name, availability_zone=None):
    return novaclient(request).aggregates.create(name, availability_zone)


@profiler.trace
def aggregate_delete(request, aggregate_id):
    return novaclient(request).aggregates.delete(aggregate_id)


@profiler.trace
def aggregate_get(request, aggregate_id):
    return novaclient(request).aggregates.get(aggregate_id)


@profiler.trace
def aggregate_update(request, aggregate_id, values):
    return novaclient(request).aggregates.update(aggregate_id, values)


@profiler.trace
def aggregate_set_metadata(request, aggregate_id, metadata):
    return novaclient(request).aggregates.set_metadata(aggregate_id, metadata)


@profiler.trace
def host_list(request):
    return novaclient(request).hosts.list()


@profiler.trace
def add_host_to_aggregate(request, aggregate_id, host):
    return novaclient(request).aggregates.add_host(aggregate_id, host)


@profiler.trace
def remove_host_from_aggregate(request, aggregate_id, host):
    return novaclient(request).aggregates.remove_host(aggregate_id, host)


@profiler.trace
def interface_attach(request,
                     server, port_id=None, net_id=None, fixed_ip=None):
    return novaclient(request).servers.interface_attach(server,
                                                        port_id,
                                                        net_id,
                                                        fixed_ip)


@profiler.trace
def interface_detach(request, server, port_id):
    return novaclient(request).servers.interface_detach(server, port_id)


@profiler.trace
@memoized_with_request(novaclient)
def list_extensions(nova_api):
    """List all nova extensions, except the ones in the blacklist."""
    blacklist = set(getattr(settings,
                            'OPENSTACK_NOVA_EXTENSIONS_BLACKLIST', []))
    return tuple(
        extension for extension in
        nova_list_extensions.ListExtManager(nova_api).show_all()
        if extension.name not in blacklist
    )


@profiler.trace
@memoized_with_request(list_extensions, 1)
def extension_supported(extension_name, extensions):
    """Determine if nova supports a given extension name.

    Example values for the extension_name include AdminActions, ConsoleOutput,
    etc.
    """
    for extension in extensions:
        if extension.name == extension_name:
            return True
    return False


@profiler.trace
def can_set_server_password():
    features = getattr(settings, 'OPENSTACK_HYPERVISOR_FEATURES', {})
    return features.get('can_set_password', False)


@profiler.trace
def instance_action_list(request, instance_id):
    return nova_instance_action.InstanceActionManager(
        novaclient(request)).list(instance_id)


@profiler.trace
def can_set_mount_point():
    """Return the Hypervisor's capability of setting mount points."""
    hypervisor_features = getattr(
        settings, "OPENSTACK_HYPERVISOR_FEATURES", {})
    return hypervisor_features.get("can_set_mount_point", False)


@profiler.trace
def requires_keypair():
    features = getattr(settings, 'OPENSTACK_HYPERVISOR_FEATURES', {})
    return features.get('requires_keypair', False)


def can_set_quotas():
    features = getattr(settings, 'OPENSTACK_HYPERVISOR_FEATURES', {})
    return features.get('enable_quotas', True)
