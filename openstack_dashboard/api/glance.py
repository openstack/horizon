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
from six.moves import _thread as thread

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa
from openstack_dashboard.api import base


LOG = logging.getLogger(__name__)
VERSIONS = base.APIVersionManager("image", preferred_version=2)

try:
    from glanceclient.v2 import client as glance_client_v2
    VERSIONS.load_supported_version(2, {"client": glance_client_v2,
                                        "version": 2})
except ImportError:
    pass

try:
    from glanceclient.v1 import client as glance_client_v1
    VERSIONS.load_supported_version(1, {"client": glance_client_v1,
                                        "version": 1})
except ImportError:
    pass


@memoized
def glanceclient(request, version='1'):
    url = base.url_for(request, 'image')
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    return glance_client.Client(version, url, token=request.user.token.id,
                                insecure=insecure, cacert=cacert)


def image_delete(request, image_id):
    return glanceclient(request).images.delete(image_id)


def image_get(request, image_id):
    """Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    image = glanceclient(request).images.get(image_id)
    if not hasattr(image, 'name'):
        image.name = None
    return image


def is_image_public(im):
    is_public_v1 = getattr(im, 'is_public', None)
    if is_public_v1 is not None:
        return is_public_v1
    else:
        return im.visibility == 'public'


def image_list_detailed(request, marker=None, sort_dir='desc',
                        sort_key='created_at', filters=None, paginate=False,
                        reversed_order=False):
    """Thin layer above glanceclient, for handling pagination issues.

    It provides iterating both forward and backward on top of ascetic
    OpenStack pagination API - which natively supports only iterating forward
    through the entries. Thus in order to retrieve list of objects at previous
    page, a request with the reverse entries order had to be made to Glance,
    using the first object id on current page as the marker - restoring
    the original items ordering before sending them back to the UI.

    .. param:: request

        The request object coming from browser to be passed further into
        Glance service.

    .. param:: marker

        The id of an object which defines a starting point of a query sent to
        Glance service.

    .. param:: sort_dir

        The direction by which the resulting image list throughout all pages
        (if pagination is enabled) will be sorted. Could be either 'asc'
        (ascending) or 'desc' (descending), defaults to 'desc'.

    .. param:: sort_key

        The name of key by by which the resulting image list throughout all
        pages (if pagination is enabled) will be sorted. Defaults to
        'created_at'.

    .. param:: filters

        A dictionary of filters passed as is to Glance service.

    .. param:: paginate

        Whether the pagination is enabled. If it is, then the number of
        entries on a single page of images table is limited to the specific
        number stored in browser cookies.

    .. param:: reversed_order

        Set this flag to True when it's necessary to get a reversed list of
        images from Glance (used for navigating the images list back in UI).
    """
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

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

    return images, has_more_data, has_prev_data


def image_update(request, image_id, **kwargs):
    image_data = kwargs.get('data', None)
    try:
        return glanceclient(request).images.update(image_id, **kwargs)
    finally:
        if image_data:
            try:
                os.remove(image_data.file.name)
            except Exception as e:
                filename = str(image_data.file)
                if hasattr(image_data.file, 'name'):
                    filename = image_data.file.name
                msg = (('Failed to remove temporary image file '
                        '%(file)s (%(e)s)') %
                       dict(file=filename, e=str(e)))
                LOG.warning(msg)


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

    image = glanceclient(request).images.create(**kwargs)

    if data:
        if isinstance(data, TemporaryUploadedFile):
            # Hack to fool Django, so we can keep file open in the new thread.
            data.file.close_called = True
        if isinstance(data, InMemoryUploadedFile):
            # Clone a new file for InMemeoryUploadedFile.
            # Because the old one will be closed by Django.
            data = SimpleUploadedFile(data.name,
                                      data.read(),
                                      data.content_type)
        thread.start_new_thread(image_update,
                                (request, image.id),
                                {'data': data,
                                 'purge_props': False})

    return image


def image_update_properties(request, image_id, remove_props=None, **kwargs):
    """Add or update a custom property of an image."""
    return glanceclient(request, '2').images.update(image_id,
                                                    remove_props,
                                                    **kwargs)


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
        if getattr(self._apiresource, 'visibility') == 'public':
            return True
        else:
            return False


def filter_properties_target(namespaces_iter,
                             resource_types,
                             properties_target):
    """Filter metadata namespaces based on the given resource types and
    properties target.

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
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
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


def metadefs_namespace_create(request, namespace):
    return glanceclient(request, '2').metadefs_namespace.create(**namespace)


def metadefs_namespace_update(request, namespace_name, **properties):
    return glanceclient(request, '2').metadefs_namespace.update(
        namespace_name,
        **properties)


def metadefs_namespace_delete(request, namespace_name):
    return glanceclient(request, '2').metadefs_namespace.delete(namespace_name)


def metadefs_resource_types_list(request):
    # Listing Resource Types requires the v2 API. If not supported we return
    # an empty array so callers don't need to worry about version checking.
    if get_version() < 2:
        return []
    else:
        return glanceclient(request, '2').metadefs_resource_type.list()


def metadefs_namespace_resource_types(request, namespace_name):
    resource_types = glanceclient(request, '2').metadefs_resource_type.get(
        namespace_name)

    # metadefs_resource_type.get() returns generator, converting it to list
    return list(resource_types)


def metadefs_namespace_add_resource_type(request,
                                         namespace_name,
                                         resource_type):
    return glanceclient(request, '2').metadefs_resource_type.associate(
        namespace_name, **resource_type)


def metadefs_namespace_remove_resource_type(request,
                                            namespace_name,
                                            resource_type_name):
    glanceclient(request, '2').metadefs_resource_type.deassociate(
        namespace_name, resource_type_name)


def get_version():
    return VERSIONS.active
