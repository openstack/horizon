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
from six.moves import urllib

from horizon import exceptions
from horizon.utils.memoized import memoized

from openstack_dashboard.api import _nova
from openstack_dashboard.api import base
from openstack_dashboard.api import microversions
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard.utils import settings as utils


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

VERSIONS = base.APIVersionManager("volume", preferred_version='3')

try:
    # pylint: disable=ungrouped-imports
    from cinderclient.v2 import client as cinder_client_v2
    VERSIONS.load_supported_version('2', {"client": cinder_client_v2,
                                          "version": '2'})
    from cinderclient.v3 import client as cinder_client_v3
    VERSIONS.load_supported_version('3', {"client": cinder_client_v3,
                                          "version": '3'})
except ImportError:
    pass


class BaseCinderAPIResourceWrapper(base.APIResourceWrapper):

    @property
    def name(self):
        # If a volume doesn't have a name, use its id.
        return (getattr(self._apiresource, 'name', None) or
                getattr(self._apiresource, 'id', None))

    @property
    def description(self):
        return (getattr(self._apiresource, 'description', None) or
                getattr(self._apiresource, 'display_description', None))


class Volume(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status', 'created_at',
              'volume_type', 'availability_zone', 'imageRef', 'bootable',
              'snapshot_id', 'source_volid', 'attachments', 'tenant_name',
              'group_id', 'consistencygroup_id', 'os-vol-host-attr:host',
              'os-vol-tenant-attr:tenant_id', 'metadata',
              'volume_image_metadata', 'encrypted', 'transfer',
              'multiattach']

    @property
    def is_bootable(self):
        return self.bootable == 'true'

    @property
    def tenant_id(self):
        return getattr(self, 'os-vol-tenant-attr:tenant_id', "")


class VolumeSnapshot(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status',
              'created_at', 'volume_id', 'group_snapshot_id',
              'os-extended-snapshot-attributes:project_id',
              'metadata']

    @property
    def project_id(self):
        return getattr(self, 'os-extended-snapshot-attributes:project_id', "")


class VolumeType(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'extra_specs', 'created_at', 'encryption',
              'associated_qos_spec', 'description',
              'os-extended-snapshot-attributes:project_id']


class VolumeBackup(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'container', 'size', 'status',
              'created_at', 'volume_id', 'availability_zone', 'snapshot_id']
    _volume = None
    _snapshot = None

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value

    @property
    def snapshot(self):
        return self._snapshot

    @snapshot.setter
    def snapshot(self, value):
        self._snapshot = value


class QosSpecs(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'consumer', 'specs']


class VolTypeExtraSpec(object):
    def __init__(self, type_id, key, val):
        self.type_id = type_id
        self.id = key
        self.key = key
        self.value = val


class GroupTypeSpec(object):
    def __init__(self, group_type_id, key, val):
        self.group_type_id = group_type_id
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


class Group(base.APIResourceWrapper):
    _attrs = ['id', 'status', 'availability_zone', 'created_at', 'name',
              'description', 'group_type', 'volume_types',
              'group_snapshot_id', 'source_group_id', 'replication_status',
              'project_id']


class GroupSnapshot(base.APIResourceWrapper):
    _attrs = ['id', 'name', 'description', 'status', 'created_at',
              'group_id', 'group_type_id', 'project_id']


class GroupType(base.APIResourceWrapper):
    _attrs = ['id', 'name', 'description', 'is_public', 'group_specs']


def _find_cinder_url(request, version=None):
    if version is None:
        api_version = VERSIONS.get_active_version()
        version = api_version['version']
    version = base.Version(version)

    # We support only cinder v2 and v3.
    if version.major == 3:
        candidates = ['volumev3', 'volume']
    else:
        candidates = ['volumev2', 'volume']

    for service_name in candidates:
        try:
            return version, base.url_for(request, service_name)
        except exceptions.ServiceCatalogException:
            pass
    else:
        raise exceptions.ServiceCatalogException(
            ("Cinder %(version)s requested but no '%(service)s' service "
             "type available in Keystone catalog.") %
            {'version': version, 'service': candidates})


@memoized
def cinderclient(request, version=None):
    version, cinder_url = _find_cinder_url(request, version)

    insecure = settings.OPENSTACK_SSL_NO_VERIFY
    cacert = settings.OPENSTACK_SSL_CACERT

    c = cinder_client.Client(
        version,
        request.user.username,
        request.user.token.id,
        project_id=request.user.tenant_id,
        auth_url=base.url_for(request, 'identity'),
        insecure=insecure,
        cacert=cacert,
        http_log_debug=settings.DEBUG,
    )
    c.client.auth_token = request.user.token.id
    c.client.management_url = cinder_url
    return c


def get_microversion(request, features):
    try:
        version, cinder_url = _find_cinder_url(request)
    except exceptions.ServiceCatalogException:
        return None
    min_ver, max_ver = _get_server_version(request, cinder_url)
    return microversions.get_microversion_for_features(
        'cinder', features, api_versions.APIVersion, min_ver, max_ver)


# NOTE(amotoki): Borrowed from cinderclient.client.get_server_version()
# to support custom SSL CA Cert support with cinderclient<5.
def _get_server_version(request, url):
    min_version = "2.0"
    current_version = "2.0"
    try:
        u = urllib.parse.urlparse(url)
        version_url = None

        # NOTE(andreykurilin): endpoint URL has at least 2 formats:
        #   1. The classic (legacy) endpoint:
        #       http://{host}:{optional_port}/v{2 or 3}/{project-id}
        #       http://{host}:{optional_port}/v{2 or 3}
        #   3. Under wsgi:
        #       http://{host}:{optional_port}/volume/v{2 or 3}
        for ver in ['v2', 'v3']:
            if u.path.endswith(ver) or "/{0}/".format(ver) in u.path:
                path = u.path[:u.path.rfind(ver)]
                version_url = '%s://%s%s' % (u.scheme, u.netloc, path)
                break

        if not version_url:
            # NOTE(andreykurilin): probably, it is one of the next cases:
            #  * https://volume.example.com/
            #  * https://example.com/volume
            # leave as is without cropping.
            version_url = url

        c = cinderclient(request)
        resp, data = c.client.request(version_url, 'GET')

        versions = data['versions']
        for version in versions:
            if '3.' in version['version']:
                min_version = version['min_version']
                current_version = version['version']
                break
            else:
                # Set the values, but don't break out the loop here in case v3
                # comes later
                min_version = '2.0'
                current_version = '2.0'
    except cinder_exception.ClientException as e:
        LOG.warning("Error in server version query:%s\n"
                    "Returning APIVersion 2.0", e)
    return (api_versions.APIVersion(min_version),
            api_versions.APIVersion(current_version))


def _cinderclient_with_features(request, features,
                                raise_exc=False, message=False):
    version = get_microversion(request, features)
    if version is None:
        if message:
            versions = microversions.get_requested_versions('cinder', features)
            if message is True:
                message = ('Insufficient microversion for cinder feature(s) '
                           '%(features)s. One of the following API '
                           'microversion(s) is required: %(versions).')
            LOG.warning(message,
                        {'features': features, 'versions': versions})
        if raise_exc:
            raise microversions.MicroVersionNotFound(features)
    if version is not None:
        version = version.get_string()
    return cinderclient(request, version=version)


def _cinderclient_with_generic_groups(request):
    return _cinderclient_with_features(request, 'groups')


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

    if sort_dir == 'asc':
        entities.reverse()

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

    # To support filtering with group_id, we need to use the microversion.
    c_client = _cinderclient_with_generic_groups(request)
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
    client = _cinderclient_with_generic_groups(request)
    volume_data = client.volumes.get(volume_id)

    for attachment in volume_data.attachments:
        if "server_id" in attachment:
            instance = _nova.server_get(request, attachment['server_id'])
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
                  availability_zone=None, source_volid=None,
                  group_id=None):
    client = _cinderclient_with_generic_groups(request)
    data = {'name': name,
            'description': description,
            'volume_type': volume_type,
            'snapshot_id': snapshot_id,
            'metadata': metadata,
            'imageRef': image_id,
            'availability_zone': availability_zone,
            'source_volid': source_volid,
            'group_id': group_id}

    volume = client.volumes.create(size, **data)
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
    cinderclient(request).volumes.reset_state(volume_id, state)


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
    client = _cinderclient_with_generic_groups(request)
    snapshot = client.volume_snapshots.get(snapshot_id)
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
    c_client = _cinderclient_with_generic_groups(request)
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

    return VolumeSnapshot(cinderclient(request).volume_snapshots.create(
        volume_id, **data))


@profiler.trace
def volume_snapshot_delete(request, snapshot_id):
    return cinderclient(request).volume_snapshots.delete(snapshot_id)


@profiler.trace
def volume_snapshot_update(request, snapshot_id, name, description):
    snapshot_data = {'name': name,
                     'description': description}
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


@memoized
def volume_backup_supported(request):
    """This method will determine if cinder supports backup."""
    # TODO(lcheng) Cinder does not expose the information if cinder
    # backup is configured yet. This is a workaround until that
    # capability is available.
    # https://bugs.launchpad.net/cinder/+bug/1334856
    return utils.get_dict_config('OPENSTACK_CINDER_FEATURES', 'enable_backup')


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
                         force=False,
                         snapshot_id=None):
    # need to ensure the container name is not an empty
    # string, but pass None to get the container name
    # generated correctly
    backup = cinderclient(request).backups.create(
        volume_id,
        container=container_name if container_name else None,
        name=name,
        description=description,
        snapshot_id=snapshot_id,
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
    cinderclient(request).volumes.manage(
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
def tenant_absolute_limits(request, tenant_id=None):
    _cinderclient = _cinderclient_with_features(
        request, ['limits_project_id_query'],
        message=('Insufficient microversion for GET limits with '
                 'project_id query. One of the following API micro '
                 'version is required: %(versions)s. '
                 'This causes bug 1810309 on updating quotas.'))
    limits = _cinderclient.limits.get(tenant_id=tenant_id).absolute
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
@memoized
def list_extensions(request):
    cinder_api = cinderclient(request)
    return tuple(cinder_list_extensions.ListExtManager(cinder_api).show_all())


@memoized
def extension_supported(request, extension_name):
    """This method will determine if Cinder supports a given extension name."""
    for extension in list_extensions(request):
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
    try:
        c_client = _cinderclient_with_features(request, ['message_list'],
                                               raise_exc=True, message=True)
    except microversions.MicroVersionNotFound:
        LOG.warning("Insufficient microversion for message_list")
        return []
    return c_client.messages.list(search_opts)


def is_volume_service_enabled(request):
    return bool(
        base.is_service_enabled(request, 'volumev3') or
        base.is_service_enabled(request, 'volumev2') or
        base.is_service_enabled(request, 'volume')
    )


def volume_type_access_list(request, volume_type):
    return cinderclient(request).volume_type_access.list(volume_type)


def volume_type_add_project_access(request, volume_type, project_id):
    return cinderclient(request).volume_type_access.add_project_access(
        volume_type, project_id)


def volume_type_remove_project_access(request, volume_type, project_id):
    return cinderclient(request).volume_type_access.remove_project_access(
        volume_type, project_id)


@profiler.trace
def group_type_list(request):
    client = _cinderclient_with_generic_groups(request)
    return [GroupType(t) for t in client.group_types.list()]


@profiler.trace
def group_type_get(request, group_type_id):
    client = _cinderclient_with_generic_groups(request)
    return GroupType(client.group_types.get(group_type_id))


@profiler.trace
def group_type_create(request, name, description=None, is_public=None):
    client = _cinderclient_with_generic_groups(request)
    params = {'name': name}
    if description is not None:
        params['description'] = description
    if is_public is not None:
        params['is_public'] = is_public
    return GroupType(client.group_types.create(**params))


@profiler.trace
def group_type_update(request, group_type_id, name=None, description=None,
                      is_public=None):
    client = _cinderclient_with_generic_groups(request)
    return GroupType(client.group_types.update(group_type_id,
                                               name,
                                               description,
                                               is_public))


@profiler.trace
def group_type_delete(request, group_type_id):
    client = _cinderclient_with_generic_groups(request)
    client.group_types.delete(group_type_id)


@profiler.trace
def group_type_spec_list(request, group_type_id, raw=False):
    group_type = group_type_get(request, group_type_id)
    specs = group_type._apiresource.get_keys()
    if raw:
        return specs
    return [GroupTypeSpec(group_type_id, key, value) for
            key, value in specs.items()]


@profiler.trace
def group_type_spec_set(request, group_type_id, metadata):
    group_type = group_type_get(request, group_type_id)
    if not metadata:
        return None
    return group_type._apiresource.set_keys(metadata)


@profiler.trace
def group_type_spec_unset(request, group_type_id, keys):
    group_type = group_type_get(request, group_type_id)
    return group_type._apiresource.unset_keys(keys)


@profiler.trace
def group_list(request, search_opts=None):
    client = _cinderclient_with_generic_groups(request)
    return [Group(g) for g in client.groups.list(search_opts=search_opts)]


@profiler.trace
def group_list_with_vol_type_names(request, search_opts=None):
    groups = group_list(request, search_opts)
    vol_types = volume_type_list(request)
    for group in groups:
        group.volume_type_names = []
        for vol_type_id in group.volume_types:
            for vol_type in vol_types:
                if vol_type.id == vol_type_id:
                    group.volume_type_names.append(vol_type.name)
                    break

    return groups


@profiler.trace
def group_get(request, group_id):
    client = _cinderclient_with_generic_groups(request)
    group = client.groups.get(group_id)
    return Group(group)


@profiler.trace
def group_get_with_vol_type_names(request, group_id):
    group = group_get(request, group_id)
    vol_types = volume_type_list(request)
    group.volume_type_names = []
    for vol_type_id in group.volume_types:
        for vol_type in vol_types:
            if vol_type.id == vol_type_id:
                group.volume_type_names.append(vol_type.name)
                break
    return group


@profiler.trace
def group_create(request, name, group_type, volume_types,
                 description=None, availability_zone=None):
    client = _cinderclient_with_generic_groups(request)
    params = {'name': name,
              'group_type': group_type,
              # cinderclient expects a comma-separated list of volume types.
              'volume_types': ','.join(volume_types)}
    if description is not None:
        params['description'] = description
    if availability_zone is not None:
        params['availability_zone'] = availability_zone
    return Group(client.groups.create(**params))


@profiler.trace
def group_create_from_source(request, name, group_snapshot_id=None,
                             source_group_id=None, description=None,
                             user_id=None, project_id=None):
    client = _cinderclient_with_generic_groups(request)
    return Group(client.groups.create_from_src(
        group_snapshot_id, source_group_id, name, description,
        user_id, project_id))


@profiler.trace
def group_delete(request, group_id, delete_volumes=False):
    client = _cinderclient_with_generic_groups(request)
    client.groups.delete(group_id, delete_volumes)


@profiler.trace
def group_update(request, group_id, name=None, description=None,
                 add_volumes=None, remove_volumes=None):
    data = {}
    if name is not None:
        data['name'] = name
    if description is not None:
        data['description'] = description
    if add_volumes:
        # cinderclient expects a comma-separated list of volume types.
        data['add_volumes'] = ','.join(add_volumes)
    if remove_volumes:
        # cinderclient expects a comma-separated list of volume types.
        data['remove_volumes'] = ','.join(remove_volumes)
    client = _cinderclient_with_generic_groups(request)
    return client.groups.update(group_id, **data)


def group_snapshot_create(request, group_id, name, description=None):
    client = _cinderclient_with_generic_groups(request)
    return GroupSnapshot(client.group_snapshots.create(group_id, name,
                                                       description))


def group_snapshot_get(request, group_snapshot_id):
    client = _cinderclient_with_generic_groups(request)
    return GroupSnapshot(client.group_snapshots.get(group_snapshot_id))


def group_snapshot_list(request, search_opts=None):
    client = _cinderclient_with_generic_groups(request)
    return [GroupSnapshot(s) for s
            in client.group_snapshots.list(search_opts=search_opts)]


def group_snapshot_delete(request, group_snapshot_id):
    client = _cinderclient_with_generic_groups(request)
    client.group_snapshots.delete(group_snapshot_id)
