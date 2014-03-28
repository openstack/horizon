# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from django.utils.translation import ugettext_lazy as _

from cinderclient.v1.contrib import list_extensions as cinder_list_extensions

from horizon import exceptions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base
from openstack_dashboard.api import nova

LOG = logging.getLogger(__name__)


# API static values
VOLUME_STATE_AVAILABLE = "available"
DEFAULT_QUOTA_NAME = 'default'


VERSIONS = base.APIVersionManager("volume", preferred_version=1)

try:
    from cinderclient.v1 import client as cinder_client_v1
    VERSIONS.load_supported_version(1, {"client": cinder_client_v1,
                                        "version": 1})
except ImportError:
    pass

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


class Volume(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status', 'created_at',
              'volume_type', 'availability_zone', 'imageRef', 'bootable'
              'snapshot_id', 'source_volid', 'attachments', 'tenant_name',
              'os-vol-host-attr:host', 'os-vol-tenant-attr:tenant_id',
              'metadata']


class VolumeSnapshot(BaseCinderAPIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status',
              'created_at', 'volume_id',
              'os-extended-snapshot-attributes:project_id']


def cinderclient(request):
    api_version = VERSIONS.get_active_version()

    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    cinder_url = ""
    try:
        # The cinder client assumes that the v2 endpoint type will be
        # 'volumev2'. However it also allows 'volume' type as a
        # fallback if the requested version is 2 and there is no
        # 'volumev2' endpoint.
        if api_version['version'] == 2:
            try:
                cinder_url = base.url_for(request, 'volumev2')
            except exceptions.ServiceCatalogException:
                LOG.warning("Cinder v2 requested but no 'volumev2' service "
                            "type available in Keystone catalog. Falling back "
                            "to 'volume'.")
        if cinder_url == "":
            cinder_url = base.url_for(request, 'volume')
    except exceptions.ServiceCatalogException:
        LOG.debug('no volume service configured.')
        return None
    LOG.debug('cinderclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, cinder_url))
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


def volume_list(request, search_opts=None):
    """To see all volumes in the cloud as an admin you can pass in a special
    search option: {'all_tenants': 1}
    """
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return [Volume(v) for v in c_client.volumes.list(search_opts=search_opts)]


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


def volume_update(request, volume_id, name, description):
    vol_data = {'name': name,
                'description': description}
    vol_data = _replace_v2_parameters(vol_data)
    return cinderclient(request).volumes.update(volume_id,
                                                **vol_data)


def volume_snapshot_get(request, snapshot_id):
    snapshot = cinderclient(request).volume_snapshots.get(snapshot_id)
    return VolumeSnapshot(snapshot)


def volume_snapshot_list(request):
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return [VolumeSnapshot(s) for s in c_client.volume_snapshots.list()]


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


def tenant_quota_get(request, tenant_id):
    c_client = cinderclient(request)
    if c_client is None:
        return base.QuotaSet()
    return base.QuotaSet(c_client.quotas.get(tenant_id))


def tenant_quota_update(request, tenant_id, **kwargs):
    return cinderclient(request).quotas.update(tenant_id, **kwargs)


def default_quota_get(request, tenant_id):
    return base.QuotaSet(cinderclient(request).quotas.defaults(tenant_id))


def volume_type_list(request):
    return cinderclient(request).volume_types.list()


def volume_type_create(request, name):
    return cinderclient(request).volume_types.create(name)


def volume_type_delete(request, volume_type_id):
    return cinderclient(request).volume_types.delete(volume_type_id)


def tenant_absolute_limits(request):
    limits = cinderclient(request).limits.get().absolute
    limits_dict = {}
    for limit in limits:
        # -1 is used to represent unlimited quotas
        if limit.value == -1:
            limits_dict[limit.name] = float("inf")
        else:
            limits_dict[limit.name] = limit.value
    return limits_dict


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
