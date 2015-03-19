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

from cinderclient.v2.contrib import list_extensions as cinder_list_extensions

from horizon import exceptions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base
from openstack_dashboard.api import nova

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

VERSIONS = base.APIVersionManager("volume", preferred_version=2)

try:
    from cinderclient.v2 import client as cinder_client_v2
    VERSIONS.load_supported_version(2, {"client": cinder_client_v2,
                                        "version": 2})
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

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._apiresource, key, None)
        return obj


class Volume(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status', 'created_at',
              'volume_type', 'availability_zone', 'imageRef', 'bootable',
              'snapshot_id', 'source_volid', 'attachments', 'tenant_name',
              'os-vol-host-attr:host', 'os-vol-tenant-attr:tenant_id',
              'metadata', 'volume_image_metadata', 'encrypted', 'transfer']

    @property
    def is_bootable(self):
        return self.bootable == 'true'


class VolumeSnapshot(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status',
              'created_at', 'volume_id',
              'os-extended-snapshot-attributes:project_id']


class VolumeType(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'extra_specs', 'created_at',
              'os-extended-snapshot-attributes:project_id']


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


@memoized
def cinderclient(request):
    api_version = VERSIONS.get_active_version()

    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    cinder_url = ""
    try:
        # The cinder client assumes that the v2 endpoint type will be
        # 'volumev2'.
        if api_version['version'] == 2:
            try:
                cinder_url = base.url_for(request, 'volumev2')
            except exceptions.ServiceCatalogException:
                LOG.warning("Cinder v2 requested but no 'volumev2' service "
                            "type available in Keystone catalog.")
    except exceptions.ServiceCatalogException:
        LOG.debug('no volume service configured.')
        raise
    c = api_version['client'].Client(request.user.username,
                                     request.user.token.id,
                                     project_id=request.user.tenant_id,
                                     auth_url=cinder_url,
                                     insecure=insecure,
                                     cacert=cacert,
                                     http_log_debug=settings.DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = cinder_url
    return c


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


def volume_list(request, search_opts=None):
    """To see all volumes in the cloud as an admin you can pass in a special
    search option: {'all_tenants': 1}
    """
    c_client = cinderclient(request)
    if c_client is None:
        return []

    # build a dictionary of volume_id -> transfer
    transfers = {t.volume_id: t
                 for t in transfer_list(request, search_opts=search_opts)}

    volumes = []
    for v in c_client.volumes.list(search_opts=search_opts):
        v.transfer = transfers.get(v.id)
        volumes.append(Volume(v))

    return volumes


def volume_get(request, volume_id):
    volume_data = cinderclient(request).volumes.get(volume_id)

    for attachment in volume_data.attachments:
        if "server_id" in attachment:
            instance = nova.server_get(request, attachment['server_id'])
            attachment['instance_name'] = instance.name
        else:
            # Nova volume can occasionally send attachments in error state
            # that lack a server_id property; to work around that we'll
            # give the attached instance a generic name.
            attachment['instance_name'] = _("Unknown instance")

    volume_data.transfer = None
    if volume_data.status == 'awaiting-transfer':
        for transfer in transfer_list(request):
            if transfer.volume_id == volume_id:
                volume_data.transfer = transfer
                break

    return Volume(volume_data)


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


def volume_extend(request, volume_id, new_size):
    return cinderclient(request).volumes.extend(volume_id, new_size)


def volume_delete(request, volume_id):
    return cinderclient(request).volumes.delete(volume_id)


def volume_retype(request, volume_id, new_type, migration_policy):
    return cinderclient(request).volumes.retype(volume_id,
                                                new_type,
                                                migration_policy)


def volume_set_bootable(request, volume_id, bootable):
    return cinderclient(request).volumes.set_bootable(volume_id,
                                                      bootable)


def volume_update(request, volume_id, name, description):
    vol_data = {'name': name,
                'description': description}
    vol_data = _replace_v2_parameters(vol_data)
    return cinderclient(request).volumes.update(volume_id,
                                                **vol_data)


def volume_reset_state(request, volume_id, state):
    return cinderclient(request).volumes.reset_state(volume_id, state)


def volume_upload_to_image(request, volume_id, force, image_name,
                           container_format, disk_format):
    return cinderclient(request).volumes.upload_to_image(volume_id,
                                                         force,
                                                         image_name,
                                                         container_format,
                                                         disk_format)


def volume_get_encryption_metadata(request, volume_id):
    return cinderclient(request).volumes.get_encryption_metadata(volume_id)


def volume_snapshot_get(request, snapshot_id):
    snapshot = cinderclient(request).volume_snapshots.get(snapshot_id)
    return VolumeSnapshot(snapshot)


def volume_snapshot_list(request, search_opts=None):
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return [VolumeSnapshot(s) for s in c_client.volume_snapshots.list(
        search_opts=search_opts)]


def volume_snapshot_create(request, volume_id, name,
                           description=None, force=False):
    data = {'name': name,
            'description': description,
            'force': force}
    data = _replace_v2_parameters(data)

    return VolumeSnapshot(cinderclient(request).volume_snapshots.create(
        volume_id, **data))


def volume_snapshot_delete(request, snapshot_id):
    return cinderclient(request).volume_snapshots.delete(snapshot_id)


def volume_snapshot_update(request, snapshot_id, name, description):
    snapshot_data = {'name': name,
                     'description': description}
    snapshot_data = _replace_v2_parameters(snapshot_data)
    return cinderclient(request).volume_snapshots.update(snapshot_id,
                                                         **snapshot_data)


def volume_snapshot_reset_state(request, snapshot_id, state):
    return cinderclient(request).volume_snapshots.reset_state(
        snapshot_id, state)


@memoized
def volume_backup_supported(request):
    """This method will determine if cinder supports backup.
    """
    # TODO(lcheng) Cinder does not expose the information if cinder
    # backup is configured yet. This is a workaround until that
    # capability is available.
    # https://bugs.launchpad.net/cinder/+bug/1334856
    cinder_config = getattr(settings, 'OPENSTACK_CINDER_FEATURES', {})
    return cinder_config.get('enable_backup', False)


def volume_backup_get(request, backup_id):
    backup = cinderclient(request).backups.get(backup_id)
    return VolumeBackup(backup)


def volume_backup_list(request):
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return [VolumeBackup(b) for b in c_client.backups.list()]


def volume_backup_create(request,
                         volume_id,
                         container_name,
                         name,
                         description):
    backup = cinderclient(request).backups.create(
        volume_id,
        container=container_name,
        name=name,
        description=description)
    return VolumeBackup(backup)


def volume_backup_delete(request, backup_id):
    return cinderclient(request).backups.delete(backup_id)


def volume_backup_restore(request, backup_id, volume_id):
    return cinderclient(request).restores.restore(backup_id=backup_id,
                                                  volume_id=volume_id)


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


def volume_unmanage(request, volume_id):
    return cinderclient(request).volumes.unmanage(volume=volume_id)


def tenant_quota_get(request, tenant_id):
    c_client = cinderclient(request)
    if c_client is None:
        return base.QuotaSet()
    return base.QuotaSet(c_client.quotas.get(tenant_id))


def tenant_quota_update(request, tenant_id, **kwargs):
    return cinderclient(request).quotas.update(tenant_id, **kwargs)


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


def default_quota_update(request, **kwargs):
    cinderclient(request).quota_classes.update(DEFAULT_QUOTA_NAME, **kwargs)


def volume_type_list(request):
    return cinderclient(request).volume_types.list()


def volume_type_create(request, name):
    return cinderclient(request).volume_types.create(name)


def volume_type_delete(request, volume_type_id):
    return cinderclient(request).volume_types.delete(volume_type_id)


def volume_type_get(request, volume_type_id):
    return cinderclient(request).volume_types.get(volume_type_id)


def volume_encryption_type_create(request, volume_type_id, data):
    return cinderclient(request).volume_encryption_types.create(volume_type_id,
                                                                specs=data)


def volume_encryption_type_delete(request, volume_type_id):
    return cinderclient(request).volume_encryption_types.delete(volume_type_id)


def volume_encryption_type_get(request, volume_type_id):
    return cinderclient(request).volume_encryption_types.get(volume_type_id)


def volume_encryption_type_list(request):
    return cinderclient(request).volume_encryption_types.list()


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
    return vol_type.unset_keys([keys])


def qos_spec_list(request):
    return cinderclient(request).qos_specs.list()


def qos_spec_get(request, qos_spec_id):
    return cinderclient(request).qos_specs.get(qos_spec_id)


def qos_spec_delete(request, qos_spec_id):
    return cinderclient(request).qos_specs.delete(qos_spec_id, force=True)


def qos_spec_create(request, name, specs):
    return cinderclient(request).qos_specs.create(name, specs)


def qos_spec_get_keys(request, qos_spec_id, raw=False):
    spec = qos_spec_get(request, qos_spec_id)
    qos_specs = spec.specs
    if raw:
        return spec
    return [QosSpec(qos_spec_id, key, value) for
            key, value in qos_specs.items()]


def qos_spec_set_keys(request, qos_spec_id, specs):
    return cinderclient(request).qos_specs.set_keys(qos_spec_id, specs)


def qos_spec_unset_keys(request, qos_spec_id, specs):
    return cinderclient(request).qos_specs.unset_keys(qos_spec_id, specs)


def qos_spec_associate(request, qos_specs, vol_type_id):
    return cinderclient(request).qos_specs.associate(qos_specs, vol_type_id)


def qos_spec_disassociate(request, qos_specs, vol_type_id):
    return cinderclient(request).qos_specs.disassociate(qos_specs, vol_type_id)


def qos_spec_get_associations(request, qos_spec_id):
    return cinderclient(request).qos_specs.get_associations(qos_spec_id)


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


def service_list(request):
    return cinderclient(request).services.list()


def availability_zone_list(request, detailed=False):
    return cinderclient(request).availability_zones.list(detailed=detailed)


@memoized
def list_extensions(request):
    return cinder_list_extensions.ListExtManager(cinderclient(request))\
        .show_all()


@memoized
def extension_supported(request, extension_name):
    """This method will determine if Cinder supports a given extension name.
    """
    extensions = list_extensions(request)
    for extension in extensions:
        if extension.name == extension_name:
            return True
    return False


def transfer_list(request, detailed=True, search_opts=None):
    """To see all volumes transfers as an admin pass in a special
    search option: {'all_tenants': 1}
    """
    c_client = cinderclient(request)
    return [VolumeTransfer(v) for v in c_client.transfers.list(
        detailed=detailed, search_opts=search_opts)]


def transfer_get(request, transfer_id):
    transfer_data = cinderclient(request).transfers.get(transfer_id)
    return VolumeTransfer(transfer_data)


def transfer_create(request, transfer_id, name):
    volume = cinderclient(request).transfers.create(transfer_id, name)
    return VolumeTransfer(volume)


def transfer_accept(request, transfer_id, auth_key):
    return cinderclient(request).transfers.accept(transfer_id, auth_key)


def transfer_delete(request, transfer_id):
    return cinderclient(request).transfers.delete(transfer_id)
