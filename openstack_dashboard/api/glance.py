# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
from __future__ import division

import collections
import itertools
import json
import logging
import os

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import TemporaryUploadedFile

import glanceclient as glance_client
import six
from six.moves import _thread as thread

from horizon.utils.memoized import memoized
from openstack_dashboard.api import base
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard.utils import settings as utils

# Python 3.8 removes the ability to import the abstract base classes from
# 'collections', but 'collections.abc' is not present in Python 2.7
# TODO(stephenfin): Remove when we drop support for Python 2.7
# pylint: disable=ungrouped-imports
if hasattr(collections, 'abc'):
    from collections.abc import Iterable
else:
    from collections import Iterable


LOG = logging.getLogger(__name__)
VERSIONS = base.APIVersionManager("image", preferred_version=2)

try:
    # pylint: disable=ungrouped-imports
    from glanceclient.v2 import client as glance_client_v2
    VERSIONS.load_supported_version(2, {"client": glance_client_v2,
                                        "version": 2})
except ImportError:
    pass
try:
    # pylint: disable=ungrouped-imports
    from glanceclient.v1 import client as glance_client_v1
    VERSIONS.load_supported_version(1, {"client": glance_client_v1,
                                        "version": 1})
except ImportError:
    pass

# TODO(e0ne): remove this workaround once glanceclient will raise
# RequestURITooLong exception

# NOTE(e0ne): set MAX_URI_LEN to 8KB like Neutron does
MAX_URI_LEN = 8192

URI_FILTER_PREFIX = "/v2/images?id=in:"
# NOTE(e0ne): 36 is a lengght of UUID, we need tp have '+' for sapparator.
# Decreasing value by 1 to make sure it could be send to a server
MAX_IMGAGES_PER_REQUEST = \
    (MAX_URI_LEN - len(URI_FILTER_PREFIX)) // (36 + 1) - 1


class Image(base.APIResourceWrapper):
    _attrs = {"architecture", "container_format", "disk_format", "created_at",
              "owner", "size", "id", "status", "updated_at", "checksum",
              "visibility", "name", "is_public", "protected", "min_disk",
              "min_ram"}
    _ext_attrs = {"file", "locations", "schema", "tags", "virtual_size",
                  "kernel_id", "ramdisk_id", "image_url"}

    def __getattribute__(self, attr):
        # Because Glance v2 treats custom properties as normal
        # attributes, we need to be more flexible than the resource
        # wrappers usually allow. In v1 they were defined under a
        # "properties" attribute.
        if VERSIONS.active >= 2 and attr == "properties":
            return {k: v for (k, v) in self._apiresource.items()
                    if self.property_visible(k)}
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return getattr(self._apiresource, attr)

    @property
    def name(self):
        return getattr(self._apiresource, 'name', None)

    @property
    def size(self):
        image_size = getattr(self._apiresource, 'size', 0)
        if image_size is None:
            return 0
        return image_size

    @size.setter
    def size(self, value):
        self._apiresource.size = value

    @property
    def is_public(self):
        # Glance v2 no longer has a 'is_public' attribute, but uses a
        # 'visibility' attribute instead.
        return (getattr(self._apiresource, 'is_public', None) or
                getattr(self._apiresource, 'visibility', None) == "public")

    def property_visible(self, prop_name, show_ext_attrs=False):
        if show_ext_attrs:
            return prop_name not in self._attrs
        else:
            return prop_name not in (self._attrs | self._ext_attrs)

    def to_dict(self, show_ext_attrs=False):
        # When using v1 Image objects (including when running unit tests
        # for v2), self._apiresource is not iterable. In that case,
        # the properties are included in the apiresource dict, so
        # just return that dict.
        if not isinstance(self._apiresource, Iterable):
            return self._apiresource.to_dict()
        image_dict = super(Image, self).to_dict()
        image_dict['is_public'] = self.is_public
        image_dict['properties'] = {
            k: self._apiresource[k] for k in self._apiresource
            if self.property_visible(k, show_ext_attrs=show_ext_attrs)}
        return image_dict

    def __eq__(self, other_image):
        return self._apiresource == other_image._apiresource

    def __ne__(self, other_image):
        return not self.__eq__(other_image)


@memoized
def glanceclient(request, version=None):
    api_version = VERSIONS.get_active_version()

    url = base.url_for(request, 'image')
    insecure = settings.OPENSTACK_SSL_NO_VERIFY
    cacert = settings.OPENSTACK_SSL_CACERT

    # TODO(jpichon): Temporarily keep both till we update the API calls
    # to stop hardcoding a version in this file. Once that's done we
    # can get rid of the deprecated 'version' parameter.
    if version is None:
        return api_version['client'].Client(url, token=request.user.token.id,
                                            insecure=insecure, cacert=cacert)
    else:
        return glance_client.Client(version, url, token=request.user.token.id,
                                    insecure=insecure, cacert=cacert)


# Note: Glance is adding more than just public and private in Newton or later
PUBLIC_TO_VISIBILITY_MAP = {
    None: None,
    True: 'public',
    False: 'private'
}

KNOWN_PROPERTIES = [
    'visibility', 'protected', 'disk_format',
    'container_format', 'min_disk', 'min_ram', 'name',
    'properties', 'kernel', 'ramdisk',
    'tags', 'import_data', 'source', 'image_id',
    'image_url', 'source_type', 'data', 'public',
    'checksum', 'created_at', 'deleted', 'is_copying',
    'deleted_at', 'is_public', 'virtual_size',
    'status', 'size', 'owner', 'id', 'updated_at',
    'kernel_id', 'ramdisk_id', 'image_file',
]


def _normalize_is_public_filter(filters):
    if not filters:
        return

    # Glance v1 uses filter 'is_public' (True, False).
    # Glance v2 uses filter 'visibility' ('public', 'private', ...).
    if VERSIONS.active >= 2:
        if 'is_public' in filters:
            # Glance v2: Replace 'is_public' with 'visibility'.
            visibility = PUBLIC_TO_VISIBILITY_MAP[filters['is_public']]
            del filters['is_public']
            if visibility is not None:
                filters['visibility'] = visibility
    elif 'visibility' in filters:
        # Glance v1: Replace 'visibility' with 'is_public'.
        filters['is_public'] = filters['visibility'] == "public"
        del filters['visibility']


def _normalize_owner_id_filter(filters):
    if not filters:
        return

    # Glance v1 uses filter 'property-owner_id' (Project ID).
    # Glance v2 uses filter 'owner' (Project ID).
    if VERSIONS.active >= 2:
        if 'property-owner_id' in filters:
            # Glance v2: Replace 'property-owner_id' with 'owner'.
            filters['owner'] = filters['property-owner_id']
            del filters['property-owner_id']
    elif 'owner' in filters:
        # Glance v1: Replace 'owner' with 'property-owner_id'.
        filters['property-owner_id'] = filters['owner']
        del filters['owner']


def _normalize_list_input(filters, **kwargs):
    _normalize_is_public_filter(filters)
    _normalize_owner_id_filter(filters)

    if VERSIONS.active < 2:
        # Glance v1 client processes some keywords specifically.
        # Others, it just takes as a nested dict called filters.
        # This results in the following being passed into the glance client:
        # {
        #    'is_public': u'true',
        #    'sort_key': u'name',
        #    'sort_dir': u'asc',
        #    'filters': {
        #        u'min_disk': u'0',
        #        u'name': u'mysql',
        #       'properties': {
        #           u'os_shutdown_timeout': u'1'
        #       }
        #    }
        # }
        v1_keywords = ['page_size', 'limit', 'sort_dir', 'sort_key', 'marker',
                       'is_public', 'return_req_id', 'paginate']

        filters = {}
        properties = {}
        for key, value in iter(kwargs.items()):
            if key in v1_keywords:
                continue
            else:
                filters[key] = value
            del kwargs[key]

        if properties:
            filters['properties'] = properties
        if filters:
            kwargs['filters'] = filters


@profiler.trace
def image_delete(request, image_id):
    return glanceclient(request).images.delete(image_id)


@profiler.trace
def image_get(request, image_id):
    """Returns an Image object populated with metadata for a given image."""
    image = glanceclient(request).images.get(image_id)
    return Image(image)


@profiler.trace
def image_list_detailed_by_ids(request, ids=None):
    images = []
    if not ids:
        return images
    for i in range(0, len(ids), MAX_IMGAGES_PER_REQUEST):
        ids_to_filter = ids[i:i + MAX_IMGAGES_PER_REQUEST]
        filters = {'id': 'in:' + ','.join(ids_to_filter)}
        images.extend(image_list_detailed(request, filters=filters)[0])

    return images


@profiler.trace
def image_list_detailed(request, marker=None, sort_dir='desc',
                        sort_key='created_at', filters=None, paginate=False,
                        reversed_order=False, **kwargs):
    """Thin layer above glanceclient, for handling pagination issues.

    It provides iterating both forward and backward on top of ascetic
    OpenStack pagination API - which natively supports only iterating forward
    through the entries. Thus in order to retrieve list of objects at previous
    page, a request with the reverse entries order had to be made to Glance,
    using the first object id on current page as the marker - restoring
    the original items ordering before sending them back to the UI.

    :param request:

        The request object coming from browser to be passed further into
        Glance service.

    :param marker:

        The id of an object which defines a starting point of a query sent to
        Glance service.

    :param sort_dir:

        The direction by which the resulting image list throughout all pages
        (if pagination is enabled) will be sorted. Could be either 'asc'
        (ascending) or 'desc' (descending), defaults to 'desc'.

    :param sort_key:

        The name of key by by which the resulting image list throughout all
        pages (if pagination is enabled) will be sorted. Defaults to
        'created_at'.

    :param filters:

        A dictionary of filters passed as is to Glance service.

    :param paginate:

        Whether the pagination is enabled. If it is, then the number of
        entries on a single page of images table is limited to the specific
        number stored in browser cookies.

    :param reversed_order:

        Set this flag to True when it's necessary to get a reversed list of
        images from Glance (used for navigating the images list back in UI).
    """
    limit = settings.API_RESULT_LIMIT
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    _normalize_list_input(filters, **kwargs)
    kwargs = {'filters': filters or {}}

    if marker:
        kwargs['marker'] = marker
    kwargs['sort_key'] = sort_key

    if not reversed_order:
        kwargs['sort_dir'] = sort_dir
    else:
        kwargs['sort_dir'] = 'desc' if sort_dir == 'asc' else 'asc'

    images_iter = glanceclient(request).images.list(page_size=request_size,
                                                    limit=limit,
                                                    **kwargs)
    has_prev_data = False
    has_more_data = False
    if paginate:
        images = list(itertools.islice(images_iter, request_size))
        # first and middle page condition
        if len(images) > page_size:
            images.pop(-1)
            has_more_data = True
            # middle page condition
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
            images = sorted(images, key=lambda image:
                            (getattr(image, sort_key) or '').lower(),
                            reverse=(sort_dir == 'desc'))
    else:
        images = list(images_iter)

    # TODO(jpichon): Do it better
    wrapped_images = []
    for image in images:
        wrapped_images.append(Image(image))

    return wrapped_images, has_more_data, has_prev_data


@profiler.trace
def image_update(request, image_id, **kwargs):
    image_data = kwargs.get('data', None)
    try:
        # Horizon doesn't support purging image properties. Make sure we don't
        # unintentionally remove properties when using v1. We don't need a
        # similar setting for v2 because you have to specify which properties
        # to remove, and the default is nothing gets removed.
        if VERSIONS.active < 2:
            kwargs['purge_props'] = False
        return Image(glanceclient(request).images.update(
            image_id, **kwargs))
    finally:
        if image_data:
            try:
                os.remove(image_data.file.name)
            except Exception as e:
                filename = str(image_data.file)
                if hasattr(image_data.file, 'name'):
                    filename = image_data.file.name
                LOG.warning('Failed to remove temporary image file '
                            '%(file)s (%(e)s)',
                            {'file': filename, 'e': e})


def get_image_upload_mode():
    mode = settings.HORIZON_IMAGES_UPLOAD_MODE
    if mode not in ('off', 'legacy', 'direct'):
        LOG.warning('HORIZON_IMAGES_UPLOAD_MODE has an unrecognized value of '
                    '"%s", reverting to default "legacy" value', mode)
        mode = 'legacy'
    return mode


class ExternallyUploadedImage(Image):
    def __init__(self, apiresource, request):
        super(ExternallyUploadedImage, self).__init__(apiresource)
        image_endpoint = base.url_for(request, 'image', 'publicURL')
        if VERSIONS.active >= 2:
            upload_template = "%s/v2/images/%s/file"
        else:
            upload_template = "%s/v1/images/%s"
        self._url = upload_template % (image_endpoint, self.id)
        self._token_id = request.user.token.id

    def to_dict(self):
        base_dict = super(ExternallyUploadedImage, self).to_dict()
        base_dict.update({
            'upload_url': self._url,
            'token_id': self._token_id
        })
        return base_dict

    @property
    def upload_url(self):
        return self._url

    @property
    def token_id(self):
        return self._token_id


def create_image_metadata(data):
    """Generate metadata dict for a new image from a given form data."""

    # Default metadata
    meta = {'protected': data.get('protected', False),
            'disk_format': data.get('disk_format', 'raw'),
            'container_format': data.get('container_format', 'bare'),
            'min_disk': data.get('min_disk') or 0,
            'min_ram': data.get('min_ram') or 0,
            'name': data.get('name', '')}

    # Glance does not really do anything with container_format at the
    # moment. It requires it is set to the same disk_format for the three
    # Amazon image types, otherwise it just treats them as 'bare.' As such
    # we will just set that to be that here instead of bothering the user
    # with asking them for information we can already determine.
    if meta['disk_format'] in ('ami', 'aki', 'ari',):
        meta['container_format'] = meta['disk_format']
    elif meta['disk_format'] == 'docker':
        # To support docker containers we allow the user to specify
        # 'docker' as the format. In that case we really want to use
        # 'raw' as the disk format and 'docker' as the container format.
        meta['disk_format'] = 'raw'
        meta['container_format'] = 'docker'
    elif meta['disk_format'] == 'vhd':
        # If the user wishes to upload a vhd using Horizon, then
        # 'ovf' must be the container format
        meta['container_format'] = 'ovf'
    elif meta['disk_format'] == 'ova':
        # If the user wishes to upload an OVA using Horizon, then
        # 'ova' must be the container format and 'vmdk' must be the disk
        # format.
        meta['container_format'] = 'ova'
        meta['disk_format'] = 'vmdk'

    properties = {}

    for prop, key in [('description', 'description'),
                      ('kernel_id', 'kernel'),
                      ('ramdisk_id', 'ramdisk'),
                      ('architecture', 'architecture')]:
        if data.get(key):
            properties[prop] = data[key]

    _handle_unknown_properties(data, properties)

    if ('visibility' in data and
            data['visibility'] not in ['public', 'private', 'community',
                                       'shared']):
        raise KeyError('invalid visibility option: %s' % data['visibility'])
    _normalize_is_public_filter(data)

    if VERSIONS.active < 2:
        meta['properties'] = properties
        meta['is_public'] = data.get('is_public', False)
    else:
        meta['visibility'] = data.get('visibility', 'private')
        meta.update(properties)

    return meta


def _handle_unknown_properties(data, properties):
    # The Glance API takes in both known and unknown fields. Unknown fields
    # are assumed as metadata. To achieve this and continue to use the
    # existing horizon api wrapper, we need this function.  This way, the
    # client REST mirrors the Glance API.
    other_props = {
        k: v for (k, v) in data.items() if k not in KNOWN_PROPERTIES
    }
    properties.update(other_props)


@profiler.trace
def image_create(request, **kwargs):
    """Create image.

    :param kwargs:
        * copy_from: URL from which Glance server should immediately copy
            the data and store it in its configured image store.
        * data: Form data posted from client.
        * location: URL where the data for this image already resides.

    In the case of 'copy_from' and 'location', the Glance server
    will give us a immediate response from create and handle the data
    asynchronously.

    In the case of 'data' the process of uploading the data may take
    some time and is handed off to a separate thread.
    """
    data = kwargs.pop('data', None)
    location = None
    if VERSIONS.active >= 2:
        location = kwargs.pop('location', None)

    image = glanceclient(request).images.create(**kwargs)
    if location is not None:
        glanceclient(request).images.add_location(image.id, location, {})

    if data:
        if isinstance(data, six.string_types):
            # The image data is meant to be uploaded externally, return a
            # special wrapper to bypass the web server in a subsequent upload
            return ExternallyUploadedImage(image, request)
        elif isinstance(data, TemporaryUploadedFile):
            # Hack to fool Django, so we can keep file open in the new thread.
            if six.PY2:
                data.file.close_called = True
            else:
                data.file._closer.close_called = True
        elif isinstance(data, InMemoryUploadedFile):
            # Clone a new file for InMemeoryUploadedFile.
            # Because the old one will be closed by Django.
            data = SimpleUploadedFile(data.name,
                                      data.read(),
                                      data.content_type)
        if VERSIONS.active < 2:
            thread.start_new_thread(image_update,
                                    (request, image.id),
                                    {'data': data})
        else:
            def upload():
                try:
                    return glanceclient(request).images.upload(image.id, data)
                finally:
                    filename = str(data.file.name)
                    try:
                        os.remove(filename)
                    except OSError as e:
                        LOG.warning('Failed to remove temporary image file '
                                    '%(file)s (%(e)s)',
                                    {'file': filename, 'e': e})
            thread.start_new_thread(upload, ())

    return Image(image)


@profiler.trace
def image_update_properties(request, image_id, remove_props=None, **kwargs):
    """Add or update a custom property of an image."""
    return glanceclient(request, '2').images.update(image_id,
                                                    remove_props,
                                                    **kwargs)


@profiler.trace
def image_delete_properties(request, image_id, keys):
    """Delete custom properties for an image."""
    return glanceclient(request, '2').images.update(image_id, keys)


class BaseGlanceMetadefAPIResourceWrapper(base.APIResourceWrapper):

    @property
    def description(self):
        return (getattr(self._apiresource, 'description', None) or
                getattr(self._apiresource, 'display_name', None))

    def as_json(self, indent=4):
        result = collections.OrderedDict()
        for attr in self._attrs:
            if hasattr(self, attr):
                result[attr] = getattr(self, attr)
        return json.dumps(result, indent=indent)

    def to_dict(self):
        return self._apiresource


class Namespace(BaseGlanceMetadefAPIResourceWrapper):

    _attrs = ['namespace', 'display_name', 'description',
              'resource_type_associations', 'visibility', 'protected',
              'created_at', 'updated_at', 'properties', 'objects']

    @property
    def resource_type_names(self):
        result = [resource_type['name'] for resource_type in
                  getattr(self._apiresource, 'resource_type_associations')]

        return sorted(result)

    @property
    def public(self):
        return getattr(self._apiresource, 'visibility') == 'public'


def filter_properties_target(namespaces_iter,
                             resource_types,
                             properties_target):
    """Filter metadata namespaces.

    Filtering is done based ongiven resource types and a properties target.

    :param namespaces_iter: Metadata namespaces iterable.
    :param resource_types: List of resource type names.
    :param properties_target: Name of the properties target.
    """
    def filter_namespace(namespace):
        for asn in namespace.get('resource_type_associations'):
            if (asn.get('name') in resource_types and
                    asn.get('properties_target') == properties_target):
                return True
        return False
    return filter(filter_namespace, namespaces_iter)


@memoized
def metadefs_namespace_get(request, namespace, resource_type=None, wrap=False):
    namespace = glanceclient(request, '2').\
        metadefs_namespace.get(namespace, resource_type=resource_type)
    # There were problems with using the wrapper class in
    # nested json serialization. So sometimes, it is not desirable
    # to wrap.
    if wrap:
        return Namespace(namespace)
    else:
        return namespace


@profiler.trace
def metadefs_namespace_list(request,
                            filters=None,
                            sort_dir='asc',
                            sort_key='namespace',
                            marker=None,
                            paginate=False):
    """Retrieve a listing of Namespaces

    :param paginate: If true will perform pagination based on settings.
    :param marker: Specifies the namespace of the last-seen namespace.
             The typical pattern of limit and marker is to make an
             initial limited request and then to use the last
             namespace from the response as the marker parameter
             in a subsequent limited request. With paginate, limit
             is automatically set.
    :param sort_dir: The sort direction ('asc' or 'desc').
    :param sort_key: The field to sort on (for example, 'created_at'). Default
             is namespace. The way base namespaces are loaded into glance
             typically at first deployment is done in a single transaction
             giving them a potentially unpredictable sort result when using
             create_at.
    :param filters: specifies addition fields to filter on such as
             resource_types.
    :returns A tuple of three values:
        1) Current page results
        2) A boolean of whether or not there are previous page(s).
        3) A boolean of whether or not there are more page(s).

    """
    # Listing namespaces requires the v2 API. If not supported we return an
    # empty array so callers don't need to worry about version checking.
    if get_version() < 2:
        return [], False, False

    if filters is None:
        filters = {}
    limit = settings.API_RESULT_LIMIT
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'filters': filters}
    if marker:
        kwargs['marker'] = marker
    kwargs['sort_dir'] = sort_dir
    kwargs['sort_key'] = sort_key

    namespaces_iter = glanceclient(request, '2').metadefs_namespace.list(
        page_size=request_size, limit=limit, **kwargs)

    # Filter the namespaces based on the provided properties_target since this
    # is not supported by the metadata namespaces API.
    resource_types = filters.get('resource_types')
    properties_target = filters.get('properties_target')
    if resource_types and properties_target:
        namespaces_iter = filter_properties_target(namespaces_iter,
                                                   resource_types,
                                                   properties_target)

    has_prev_data = False
    has_more_data = False
    if paginate:
        namespaces = list(itertools.islice(namespaces_iter, request_size))
        # first and middle page condition
        if len(namespaces) > page_size:
            namespaces.pop(-1)
            has_more_data = True
            # middle page condition
            if marker is not None:
                has_prev_data = True
        # first page condition when reached via prev back
        elif sort_dir == 'desc' and marker is not None:
            has_more_data = True
        # last page condition
        elif marker is not None:
            has_prev_data = True
    else:
        namespaces = list(namespaces_iter)

    namespaces = [Namespace(namespace) for namespace in namespaces]
    return namespaces, has_more_data, has_prev_data


@profiler.trace
def metadefs_namespace_full_list(request, resource_type, filters=None,
                                 *args, **kwargs):
    filters = filters or {}
    filters['resource_types'] = [resource_type]
    namespaces, has_more_data, has_prev_data = metadefs_namespace_list(
        request, filters, *args, **kwargs
    )
    return [
        metadefs_namespace_get(request, x.namespace, resource_type)
        for x in namespaces
    ], has_more_data, has_prev_data


@profiler.trace
def metadefs_namespace_create(request, namespace):
    return glanceclient(request, '2').metadefs_namespace.create(**namespace)


@profiler.trace
def metadefs_namespace_update(request, namespace_name, **properties):
    return glanceclient(request, '2').metadefs_namespace.update(
        namespace_name,
        **properties)


@profiler.trace
def metadefs_namespace_delete(request, namespace_name):
    return glanceclient(request, '2').metadefs_namespace.delete(namespace_name)


@profiler.trace
def metadefs_resource_types_list(request):
    # Listing Resource Types requires the v2 API. If not supported we return
    # an empty array so callers don't need to worry about version checking.
    if get_version() < 2:
        return []
    else:
        return glanceclient(request, '2').metadefs_resource_type.list()


@profiler.trace
def metadefs_namespace_resource_types(request, namespace_name):
    resource_types = glanceclient(request, '2').metadefs_resource_type.get(
        namespace_name)

    # metadefs_resource_type.get() returns generator, converting it to list
    return list(resource_types)


@profiler.trace
def metadefs_namespace_add_resource_type(request,
                                         namespace_name,
                                         resource_type):
    return glanceclient(request, '2').metadefs_resource_type.associate(
        namespace_name, **resource_type)


@profiler.trace
def metadefs_namespace_remove_resource_type(request,
                                            namespace_name,
                                            resource_type_name):
    glanceclient(request, '2').metadefs_resource_type.deassociate(
        namespace_name, resource_type_name)


def get_version():
    return VERSIONS.active
