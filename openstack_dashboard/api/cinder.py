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

import logging

from django.conf import settings
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from cinderclient import api_versions
from cinderclient import client as cinder_client
from cinderclient import exceptions as cinder_exception
from cinderclient.v2.contrib import list_extensions as cinder_list_extensions

from horizon import exceptions
from horizon.utils import functions as utils
from horizon.utils.memoized import memoized
from horizon.utils.memoized import memoized_with_request

from openstack_dashboard.api import base
from openstack_dashboard.api import microversions
from openstack_dashboard.api import nova
from openstack_dashboard.contrib.developer.profiler import api as profiler

LOG = logging.getLogger(__name__)


# API static values
VOLUME_STATE_AVAILABLE = "available"
DEFAULT_QUOTA_NAME = 'default'

# Available consumer choices associated with QOS Specs
CONSUMER_CHOICES = (
    ('back-end', _('back-end')),
    ('front-end', _('front-end')),
    ('both', pgettext_lazy('Both of front-end and back-end', u'both')),
)

VERSIONS = base.APIVersionManager("volume", preferred_version='2')

try:
    from cinderclient.v2 import client as cinder_client_v2
    VERSIONS.load_supported_version('2', {"client": cinder_client_v2,
                                          "version": '2'})
except ImportError:
    pass


class BaseCinderAPIResourceWrapper(base.APIResourceWrapper):

    @property
    def name(self):
        # If a volume doesn't have a name, use its id.
        return (getattr(self._apiresource, 'name', None) or
                getattr(self._apiresource, 'display_name', None) or
                getattr(self._apiresource, 'id', None))

    @property
    def description(self):
        return (getattr(self._apiresource, 'description', None) or
                getattr(self._apiresource, 'display_description', None))


class Volume(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status', 'created_at',
              'volume_type', 'availability_zone', 'imageRef', 'bootable',
              'snapshot_id', 'source_volid', 'attachments', 'tenant_name',
              'consistencygroup_id', 'os-vol-host-attr:host',
              'os-vol-tenant-attr:tenant_id', 'metadata',
              'volume_image_metadata', 'encrypted', 'transfer']

    @property
    def is_bootable(self):
        return self.bootable == 'true'


class VolumeSnapshot(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status',
              'created_at', 'volume_id',
              'os-extended-snapshot-attributes:project_id',
              'metadata']


class VolumeType(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'extra_specs', 'created_at', 'encryption',
              'associated_qos_spec', 'description',
              'os-extended-snapshot-attributes:project_id']


class VolumeConsistencyGroup(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'status', 'availability_zone',
              'created_at', 'volume_types']


class VolumeCGSnapshot(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'status',
              'created_at', 'consistencygroup_id']


class VolumeBackup(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'container', 'size', 'status',
              'created_at', 'volume_id', 'availability_zone']
    _volume = None

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value


class QosSpecs(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'consumer', 'specs']


class VolTypeExtraSpec(object):
    def __init__(self, type_id, key, val):
        self.type_id = type_id
        self.id = key
        self.key = key
        self.value = val


class QosSpec(object):
    def __init__(self, id, key, val):
        self.id = id
        self.key = key
        self.value = val


class VolumeTransfer(base.APIResourceWrapper):

    _attrs = ['id', 'name', 'created_at', 'volume_id', 'auth_key']


class VolumePool(base.APIResourceWrapper):

    _attrs = ['name', 'pool_name', 'total_capacity_gb', 'free_capacity_gb',
              'allocated_capacity_gb', 'QoS_support', 'reserved_percentage',
              'volume_backend_name', 'vendor_name', 'driver_version',
              'storage_protocol', 'extra_specs']


def get_auth_params_from_request(request):
    auth_url = base.url_for(request, 'identity')
    cinder_urls = []
    for service_name in ('volumev3', 'volumev2', 'volume'):
        try:
            cinder_url = base.url_for(request, service_name)
            cinder_urls.append((service_name, cinder_url))
        except exceptions.ServiceCatalogException:
            pass
    if not cinder_urls:
        raise exceptions.ServiceCatalogException(
            "no volume service configured")
    cinder_urls = tuple(cinder_urls)  # need to make it cacheable
    return(
        request.user.username,
        request.user.token.id,
        request.user.tenant_id,
        cinder_urls,
        auth_url,
    )


@memoized_with_request(get_auth_params_from_request)
def cinderclient(request_auth_params, version=None):
    if version is None:
        api_version = VERSIONS.get_active_version()
        version = api_version['version']
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

    username, token_id, tenant_id, cinder_urls, auth_url = request_auth_params
    version = base.Version(version)
    if version == 2:
        service_names = ('volumev2', 'volume')
    elif version == 3:
        service_names = ('volumev3', 'volume')
    else:
        service_names = ('volume',)
    for name, cinder_url in cinder_urls:
        if name in service_names:
            break
    else:
        raise exceptions.ServiceCatalogException(
            "Cinder {version} requested but no '{service}' service "
            "type available in Keystone catalog.".format(version=version,
                                                         service=service_names)
        )
    c = cinder_client.Client(
        version,
        username,
        token_id,
        project_id=tenant_id,
        auth_url=auth_url,
        insecure=insecure,
        cacert=cacert,
        http_log_debug=settings.DEBUG,
    )
    c.client.auth_token = token_id
    c.client.management_url = cinder_url
    return c


def get_microversion(request, feature):
    for service_name in ('volume', 'volumev2', 'volumev3'):
        try:
            cinder_url = base.url_for(request, service_name)
            break
        except exceptions.ServiceCatalogException:
            continue
    else:
        return None
    min_ver, max_ver = cinder_client.get_server_version(cinder_url)
    return (microversions.get_microversion_for_feature(
        'cinder', feature, api_versions.APIVersion, min_ver, max_ver))


def _replace_v2_parameters(data):
    if VERSIONS.active < 2:
        data['display_name'] = data['name']
        data['display_description'] = data['description']
        del data['name']
        del data['description']
    return data


def version_get():
    api_version = VERSIONS.get_active_version()
    return api_version['version']


def volume_list(request, search_opts=None, marker=None, sort_dir="desc"):
    volumes, _, __ = volume_list_paged(
        request, search_opts=search_opts, marker=marker, paginate=False,
        sort_dir=sort_dir)
    return volumes


def update_pagination(entities, page_size, marker, sort_dir):
    has_more_data, has_prev_data = False, False
    if len(entities) > page_size:
        has_more_data = True
        entities.pop()
        if marker is not None:
            has_prev_data = True
    # first page condition when reached via prev back
    elif sort_dir == 'asc' and marker is not None:
        has_more_data = True
    # last page condition
    elif marker is not None:
        has_prev_data = True

    return entities, has_more_data, has_prev_data


@profiler.trace
def volume_list_paged(request, search_opts=None, marker=None, paginate=False,
                      sort_dir="desc"):
    """List volumes with pagination.

    To see all volumes in the cloud as an admin you can pass in a special
    search option: {'all_tenants': 1}
    """
    has_more_data = False
    has_prev_data = False
    volumes = []

    c_client = cinderclient(request)
    if c_client is None:
        return volumes, has_more_data, has_prev_data

    # build a dictionary of volume_id -> transfer
    transfers = {t.volume_id: t
                 for t in transfer_list(request, search_opts=search_opts)}

    if VERSIONS.active > 1 and paginate:
        page_size = utils.get_page_size(request)
        # sort_key and sort_dir deprecated in kilo, use sort
        # if pagination is true, we use a single sort parameter
        # by default, it is "created_at"
        sort = 'created_at:' + sort_dir
        for v in c_client.volumes.list(search_opts=search_opts,
                                       limit=page_size + 1,
                                       marker=marker,
                                       sort=sort):
            v.transfer = transfers.get(v.id)
            volumes.append(Volume(v))
        volumes, has_more_data, has_prev_data = update_pagination(
            volumes, page_size, marker, sort_dir)
    else:
        for v in c_client.volumes.list(search_opts=search_opts):
            v.transfer = transfers.get(v.id)
            volumes.append(Volume(v))

    return volumes, has_more_data, has_prev_data


@profiler.trace
def volume_get(request, volume_id):
    volume_data = cinderclient(request).volumes.get(volume_id)

    for attachment in volume_data.attachments:
        if "server_id" in attachment:
            instance = nova.server_get(request, attachment['server_id'])
            attachment['instance_name'] = instance.name
        else:
            # Nova volume can occasionally send back error'd attachments
            # the lack a server_id property; to work around that we'll
            # give the attached instance a generic name.
            attachment['instance_name'] = _("Unknown instance")

    volume_data.transfer = None
    if volume_data.status == 'awaiting-transfer':
        for transfer in transfer_list(request):
            if transfer.volume_id == volume_id:
                volume_data.transfer = transfer
                break

    return Volume(volume_data)


@profiler.trace
def volume_create(request, size, name, description, volume_type,
                  snapshot_id=None, metadata=None, image_id=None,
                  availability_zone=None, source_volid=None):
    data = {'name': name,
            'description': description,
            'volume_type': volume_type,
            'snapshot_id': snapshot_id,
            'metadata': metadata,
            'imageRef': image_id,
            'availability_zone': availability_zone,
            'source_volid': source_volid}
    data = _replace_v2_parameters(data)

    volume = cinderclient(request).volumes.create(size, **data)
    return Volume(volume)


@profiler.trace
def volume_extend(request, volume_id, new_size):
    return cinderclient(request).volumes.extend(volume_id, new_size)


@profiler.trace
def volume_delete(request, volume_id):
    return cinderclient(request).volumes.delete(volume_id)


@profiler.trace
def volume_retype(request, volume_id, new_type, migration_policy):
    return cinderclient(request).volumes.retype(volume_id,
                                                new_type,
                                                migration_policy)


@profiler.trace
def volume_set_bootable(request, volume_id, bootable):
    return cinderclient(request).volumes.set_bootable(volume_id,
                                                      bootable)


@profiler.trace
def volume_update(request, volume_id, name, description):
    vol_data = {'name': name,
                'description': description}
    vol_data = _replace_v2_parameters(vol_data)
    return cinderclient(request).volumes.update(volume_id,
                                                **vol_data)


@profiler.trace
def volume_set_metadata(request, volume_id, metadata):
    return cinderclient(request).volumes.set_metadata(volume_id, metadata)


@profiler.trace
def volume_delete_metadata(request, volume_id, keys):
    return cinderclient(request).volumes.delete_metadata(volume_id, keys)


@profiler.trace
def volume_reset_state(request, volume_id, state):
    return cinderclient(request).volumes.reset_state(volume_id, state)


@profiler.trace
def volume_upload_to_image(request, volume_id, force, image_name,
                           container_format, disk_format):
    return cinderclient(request).volumes.upload_to_image(volume_id,
                                                         force,
                                                         image_name,
                                                         container_format,
                                                         disk_format)


@profiler.trace
def volume_get_encryption_metadata(request, volume_id):
    return cinderclient(request).volumes.get_encryption_metadata(volume_id)


@profiler.trace
def volume_migrate(request, volume_id, host, force_host_copy=False,
                   lock_volume=False):
    return cinderclient(request).volumes.migrate_volume(volume_id,
                                                        host,
                                                        force_host_copy,
                                                        lock_volume)


@profiler.trace
def volume_snapshot_get(request, snapshot_id):
    snapshot = cinderclient(request).volume_snapshots.get(snapshot_id)
    return VolumeSnapshot(snapshot)


@profiler.trace
def volume_snapshot_list(request, search_opts=None):
    snapshots, _, __ = volume_snapshot_list_paged(request,
                                                  search_opts=search_opts,
                                                  paginate=False)
    return snapshots


@profiler.trace
def volume_snapshot_list_paged(request, search_opts=None, marker=None,
                               paginate=False, sort_dir="desc"):
    has_more_data = False
    has_prev_data = False
    snapshots = []
    c_client = cinderclient(request)
    if c_client is None:
        return snapshots, has_more_data, has_more_data

    if VERSIONS.active > 1 and paginate:
        page_size = utils.get_page_size(request)
        # sort_key and sort_dir deprecated in kilo, use sort
        # if pagination is true, we use a single sort parameter
        # by default, it is "created_at"
        sort = 'created_at:' + sort_dir
        for s in c_client.volume_snapshots.list(search_opts=search_opts,
                                                limit=page_size + 1,
                                                marker=marker,
                                                sort=sort):
            snapshots.append(VolumeSnapshot(s))

        snapshots, has_more_data, has_prev_data = update_pagination(
            snapshots, page_size, marker, sort_dir)
    else:
        for s in c_client.volume_snapshots.list(search_opts=search_opts):
            snapshots.append(VolumeSnapshot(s))

    return snapshots, has_more_data, has_prev_data


@profiler.trace
def volume_snapshot_create(request, volume_id, name,
                           description=None, force=False):
    data = {'name': name,
            'description': description,
            'force': force}
    data = _replace_v2_parameters(data)

    return VolumeSnapshot(cinderclient(request).volume_snapshots.create(
        volume_id, **data))


@profiler.trace
def volume_snapshot_delete(request, snapshot_id):
    return cinderclient(request).volume_snapshots.delete(snapshot_id)


@profiler.trace
def volume_snapshot_update(request, snapshot_id, name, description):
    snapshot_data = {'name': name,
                     'description': description}
    snapshot_data = _replace_v2_parameters(snapshot_data)
    return cinderclient(request).volume_snapshots.update(snapshot_id,
                                                         **snapshot_data)


@profiler.trace
def volume_snapshot_set_metadata(request, snapshot_id, metadata):
    return cinderclient(request).volume_snapshots.set_metadata(
        snapshot_id, metadata)


@profiler.trace
def volume_snapshot_delete_metadata(request, snapshot_id, keys):
    return cinderclient(request).volume_snapshots.delete_metadata(
        snapshot_id, keys)


@profiler.trace
def volume_snapshot_reset_state(request, snapshot_id, state):
    return cinderclient(request).volume_snapshots.reset_state(
        snapshot_id, state)


@profiler.trace
def volume_cgroup_get(request, cgroup_id):
    cgroup = cinderclient(request).consistencygroups.get(cgroup_id)
    return VolumeConsistencyGroup(cgroup)


@profiler.trace
def volume_cgroup_get_with_vol_type_names(request, cgroup_id):
    cgroup = volume_cgroup_get(request, cgroup_id)
    vol_types = volume_type_list(request)
    cgroup.volume_type_names = []
    for vol_type_id in cgroup.volume_types:
        for vol_type in vol_types:
            if vol_type.id == vol_type_id:
                cgroup.volume_type_names.append(vol_type.name)
                break
    return cgroup


@profiler.trace
def volume_cgroup_list(request, search_opts=None):
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return [VolumeConsistencyGroup(s) for s in c_client.consistencygroups.list(
        search_opts=search_opts)]


@profiler.trace
def volume_cgroup_list_with_vol_type_names(request, search_opts=None):
    cgroups = volume_cgroup_list(request, search_opts)
    vol_types = volume_type_list(request)
    for cgroup in cgroups:
        cgroup.volume_type_names = []
        for vol_type_id in cgroup.volume_types:
            for vol_type in vol_types:
                if vol_type.id == vol_type_id:
                    cgroup.volume_type_names.append(vol_type.name)
                    break

    return cgroups


@profiler.trace
def volume_cgroup_create(request, volume_types, name,
                         description=None, availability_zone=None):
    data = {'name': name,
            'description': description,
            'availability_zone': availability_zone}

    cgroup = cinderclient(request).consistencygroups.create(volume_types,
                                                            **data)
    return VolumeConsistencyGroup(cgroup)


@profiler.trace
def volume_cgroup_create_from_source(request, name, cg_snapshot_id=None,
                                     source_cgroup_id=None,
                                     description=None,
                                     user_id=None, project_id=None):
    return VolumeConsistencyGroup(
        cinderclient(request).consistencygroups.create_from_src(
            cg_snapshot_id,
            source_cgroup_id,
            name,
            description,
            user_id,
            project_id))


@profiler.trace
def volume_cgroup_delete(request, cgroup_id, force=False):
    return cinderclient(request).consistencygroups.delete(cgroup_id, force)


@profiler.trace
def volume_cgroup_update(request, cgroup_id, name=None, description=None,
                         add_vols=None, remove_vols=None):
    cgroup_data = {}
    if name:
        cgroup_data['name'] = name
    if description:
        cgroup_data['description'] = description
    if add_vols:
        cgroup_data['add_volumes'] = add_vols
    if remove_vols:
        cgroup_data['remove_volumes'] = remove_vols
    return cinderclient(request).consistencygroups.update(cgroup_id,
                                                          **cgroup_data)


def volume_cg_snapshot_create(request, cgroup_id, name,
                              description=None):
    return VolumeCGSnapshot(
        cinderclient(request).cgsnapshots.create(
            cgroup_id,
            name,
            description))


def volume_cg_snapshot_get(request, cg_snapshot_id):
    cgsnapshot = cinderclient(request).cgsnapshots.get(cg_snapshot_id)
    return VolumeCGSnapshot(cgsnapshot)


def volume_cg_snapshot_list(request, search_opts=None):
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return [VolumeCGSnapshot(s) for s in c_client.cgsnapshots.list(
        search_opts=search_opts)]


def volume_cg_snapshot_delete(request, cg_snapshot_id):
    return cinderclient(request).cgsnapshots.delete(cg_snapshot_id)


@memoized
def volume_backup_supported(request):
    """This method will determine if cinder supports backup."""
    # TODO(lcheng) Cinder does not expose the information if cinder
    # backup is configured yet. This is a workaround until that
    # capability is available.
    # https://bugs.launchpad.net/cinder/+bug/1334856
    cinder_config = getattr(settings, 'OPENSTACK_CINDER_FEATURES', {})
    return cinder_config.get('enable_backup', False)


@profiler.trace
def volume_backup_get(request, backup_id):
    backup = cinderclient(request).backups.get(backup_id)
    return VolumeBackup(backup)


def volume_backup_list(request):
    backups, _, __ = volume_backup_list_paged(request, paginate=False)
    return backups


@profiler.trace
def volume_backup_list_paged(request, marker=None, paginate=False,
                             sort_dir="desc"):
    has_more_data = False
    has_prev_data = False
    backups = []

    c_client = cinderclient(request)
    if c_client is None:
        return backups, has_more_data, has_prev_data

    if VERSIONS.active > 1 and paginate:
        page_size = utils.get_page_size(request)
        # sort_key and sort_dir deprecated in kilo, use sort
        # if pagination is true, we use a single sort parameter
        # by default, it is "created_at"
        sort = 'created_at:' + sort_dir
        for b in c_client.backups.list(limit=page_size + 1,
                                       marker=marker,
                                       sort=sort):
            backups.append(VolumeBackup(b))

        backups, has_more_data, has_prev_data = update_pagination(
            backups, page_size, marker, sort_dir)
    else:
        for b in c_client.backups.list():
            backups.append(VolumeBackup(b))

    return backups, has_more_data, has_prev_data


@profiler.trace
def volume_backup_create(request,
                         volume_id,
                         container_name,
                         name,
                         description,
                         force=False):
    # need to ensure the container name is not an empty
    # string, but pass None to get the container name
    # generated correctly
    backup = cinderclient(request).backups.create(
        volume_id,
        container=container_name if container_name else None,
        name=name,
        description=description,
        force=force)
    return VolumeBackup(backup)


@profiler.trace
def volume_backup_delete(request, backup_id):
    return cinderclient(request).backups.delete(backup_id)


@profiler.trace
def volume_backup_restore(request, backup_id, volume_id):
    return cinderclient(request).restores.restore(backup_id=backup_id,
                                                  volume_id=volume_id)


@profiler.trace
def volume_manage(request,
                  host,
                  identifier,
                  id_type,
                  name,
                  description,
                  volume_type,
                  availability_zone,
                  metadata,
                  bootable):
    source = {id_type: identifier}
    return cinderclient(request).volumes.manage(
        host=host,
        ref=source,
        name=name,
        description=description,
        volume_type=volume_type,
        availability_zone=availability_zone,
        metadata=metadata,
        bootable=bootable)


@profiler.trace
def volume_unmanage(request, volume_id):
    return cinderclient(request).volumes.unmanage(volume=volume_id)


@profiler.trace
def tenant_quota_get(request, tenant_id):
    c_client = cinderclient(request)
    if c_client is None:
        return base.QuotaSet()
    return base.QuotaSet(c_client.quotas.get(tenant_id))


@profiler.trace
def tenant_quota_update(request, tenant_id, **kwargs):
    return cinderclient(request).quotas.update(tenant_id, **kwargs)


@profiler.trace
def default_quota_get(request, tenant_id):
    return base.QuotaSet(cinderclient(request).quotas.defaults(tenant_id))


def volume_type_list_with_qos_associations(request):
    vol_types = volume_type_list(request)
    vol_types_dict = {}

    # initialize and build a dictionary for lookup access below
    for vol_type in vol_types:
        vol_type.associated_qos_spec = ""
        vol_types_dict[vol_type.id] = vol_type

    # get all currently defined qos specs
    qos_specs = qos_spec_list(request)
    for qos_spec in qos_specs:
        # get all volume types this qos spec is associated with
        assoc_vol_types = qos_spec_get_associations(request, qos_spec.id)
        for assoc_vol_type in assoc_vol_types:
            # update volume type to hold this association info
            vol_type = vol_types_dict[assoc_vol_type.id]
            vol_type.associated_qos_spec = qos_spec.name

    return vol_types


def volume_type_get_with_qos_association(request, volume_type_id):
    vol_type = volume_type_get(request, volume_type_id)
    vol_type.associated_qos_spec = ""

    # get all currently defined qos specs
    qos_specs = qos_spec_list(request)
    for qos_spec in qos_specs:
        # get all volume types this qos spec is associated with
        assoc_vol_types = qos_spec_get_associations(request, qos_spec.id)
        for assoc_vol_type in assoc_vol_types:
            if vol_type.id == assoc_vol_type.id:
                # update volume type to hold this association info
                vol_type.associated_qos_spec = qos_spec.name
                return vol_type

    return vol_type


@profiler.trace
def default_quota_update(request, **kwargs):
    cinderclient(request).quota_classes.update(DEFAULT_QUOTA_NAME, **kwargs)


@profiler.trace
def volume_type_list(request):
    return cinderclient(request).volume_types.list()


@profiler.trace
def volume_type_create(request, name, description=None, is_public=True):
    return cinderclient(request).volume_types.create(name, description,
                                                     is_public)


@profiler.trace
def volume_type_update(request, volume_type_id, name=None, description=None,
                       is_public=None):
    return cinderclient(request).volume_types.update(volume_type_id,
                                                     name,
                                                     description,
                                                     is_public)


@profiler.trace
@memoized
def volume_type_default(request):
    return cinderclient(request).volume_types.default()


@profiler.trace
def volume_type_delete(request, volume_type_id):
    try:
        return cinderclient(request).volume_types.delete(volume_type_id)
    except cinder_exception.BadRequest:
        raise exceptions.BadRequest(_(
            "This volume type is used by one or more volumes."))


@profiler.trace
def volume_type_get(request, volume_type_id):
    return cinderclient(request).volume_types.get(volume_type_id)


@profiler.trace
def volume_encryption_type_create(request, volume_type_id, data):
    return cinderclient(request).volume_encryption_types.create(volume_type_id,
                                                                specs=data)


@profiler.trace
def volume_encryption_type_delete(request, volume_type_id):
    return cinderclient(request).volume_encryption_types.delete(volume_type_id)


@profiler.trace
def volume_encryption_type_get(request, volume_type_id):
    return cinderclient(request).volume_encryption_types.get(volume_type_id)


@profiler.trace
def volume_encryption_type_list(request):
    return cinderclient(request).volume_encryption_types.list()


@profiler.trace
def volume_encryption_type_update(request, volume_type_id, data):
    return cinderclient(request).volume_encryption_types.update(volume_type_id,
                                                                specs=data)


@profiler.trace
def volume_type_extra_get(request, type_id, raw=False):
    vol_type = volume_type_get(request, type_id)
    extras = vol_type.get_keys()
    if raw:
        return extras
    return [VolTypeExtraSpec(type_id, key, value) for
            key, value in extras.items()]


def volume_type_extra_set(request, type_id, metadata):
    vol_type = volume_type_get(request, type_id)
    if not metadata:
        return None
    return vol_type.set_keys(metadata)


def volume_type_extra_delete(request, type_id, keys):
    vol_type = volume_type_get(request, type_id)
    return vol_type.unset_keys(keys)


@profiler.trace
def qos_spec_list(request):
    return cinderclient(request).qos_specs.list()


@profiler.trace
def qos_spec_get(request, qos_spec_id):
    return cinderclient(request).qos_specs.get(qos_spec_id)


@profiler.trace
def qos_spec_delete(request, qos_spec_id):
    return cinderclient(request).qos_specs.delete(qos_spec_id, force=True)


@profiler.trace
def qos_spec_create(request, name, specs):
    return cinderclient(request).qos_specs.create(name, specs)


def qos_spec_get_keys(request, qos_spec_id, raw=False):
    spec = qos_spec_get(request, qos_spec_id)
    qos_specs = spec.specs
    if raw:
        return spec
    return [QosSpec(qos_spec_id, key, value) for
            key, value in qos_specs.items()]


@profiler.trace
def qos_spec_set_keys(request, qos_spec_id, specs):
    return cinderclient(request).qos_specs.set_keys(qos_spec_id, specs)


@profiler.trace
def qos_spec_unset_keys(request, qos_spec_id, specs):
    return cinderclient(request).qos_specs.unset_keys(qos_spec_id, specs)


@profiler.trace
def qos_spec_associate(request, qos_specs, vol_type_id):
    return cinderclient(request).qos_specs.associate(qos_specs, vol_type_id)


@profiler.trace
def qos_spec_disassociate(request, qos_specs, vol_type_id):
    return cinderclient(request).qos_specs.disassociate(qos_specs, vol_type_id)


@profiler.trace
def qos_spec_get_associations(request, qos_spec_id):
    return cinderclient(request).qos_specs.get_associations(qos_spec_id)


def qos_specs_list(request):
    return [QosSpecs(s) for s in qos_spec_list(request)]


@profiler.trace
@memoized
def tenant_absolute_limits(request):
    limits = cinderclient(request).limits.get().absolute
    limits_dict = {}
    for limit in limits:
        if limit.value < 0:
            # In some cases, the absolute limits data in Cinder can get
            # out of sync causing the total.*Used limits to return
            # negative values instead of 0. For such cases, replace
            # negative values with 0.
            if limit.name.startswith('total') and limit.name.endswith('Used'):
                limits_dict[limit.name] = 0
            else:
                # -1 is used to represent unlimited quotas
                limits_dict[limit.name] = float("inf")
        else:
            limits_dict[limit.name] = limit.value
    return limits_dict


@profiler.trace
def service_list(request):
    return cinderclient(request).services.list()


@profiler.trace
def availability_zone_list(request, detailed=False):
    return cinderclient(request).availability_zones.list(detailed=detailed)


@profiler.trace
@memoized_with_request(cinderclient)
def list_extensions(cinder_api):
    return tuple(cinder_list_extensions.ListExtManager(cinder_api).show_all())


@memoized_with_request(list_extensions)
def extension_supported(extensions, extension_name):
    """This method will determine if Cinder supports a given extension name."""
    for extension in extensions:
        if extension.name == extension_name:
            return True
    return False


@profiler.trace
def transfer_list(request, detailed=True, search_opts=None):
    """List volume transfers.

    To see all volumes transfers as an admin pass in a special
    search option: {'all_tenants': 1}
    """
    c_client = cinderclient(request)
    try:
        return [VolumeTransfer(v) for v in c_client.transfers.list(
            detailed=detailed, search_opts=search_opts)]
    except cinder_exception.Forbidden as error:
        LOG.error(error)
        return []


@profiler.trace
def transfer_get(request, transfer_id):
    transfer_data = cinderclient(request).transfers.get(transfer_id)
    return VolumeTransfer(transfer_data)


@profiler.trace
def transfer_create(request, transfer_id, name):
    volume = cinderclient(request).transfers.create(transfer_id, name)
    return VolumeTransfer(volume)


@profiler.trace
def transfer_accept(request, transfer_id, auth_key):
    return cinderclient(request).transfers.accept(transfer_id, auth_key)


@profiler.trace
def transfer_delete(request, transfer_id):
    return cinderclient(request).transfers.delete(transfer_id)


@profiler.trace
def pool_list(request, detailed=False):
    c_client = cinderclient(request)
    if c_client is None:
        return []

    return [VolumePool(v) for v in c_client.pools.list(
        detailed=detailed)]


@profiler.trace
def message_list(request, search_opts=None):
    version = get_microversion(request, 'message_list')
    if version is None:
        LOG.warning("insufficient microversion for message_list")
        return []
    c_client = cinderclient(request, version=version)
    return c_client.messages.list(search_opts)


def is_volume_service_enabled(request):
    return bool(
        base.is_service_enabled(request, 'volume') or
        base.is_service_enabled(request, 'volumev2') or
        base.is_service_enabled(request, 'volumev3')
    )


def volume_type_access_list(request, volume_type):
    return cinderclient(request).volume_type_access.list(volume_type)


def volume_type_add_project_access(request, volume_type, project_id):
    return cinderclient(request).volume_type_access.add_project_access(
        volume_type, project_id)


def volume_type_remove_project_access(request, volume_type, project_id):
    return cinderclient(request).volume_type_access.remove_project_access(
        volume_type, project_id)
