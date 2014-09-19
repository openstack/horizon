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


from django.conf import settings
import glanceclient as glance_client
from six.moves import _thread as thread

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa
from openstack_dashboard.api import base


LOG = logging.getLogger(__name__)


@memoized
def glanceclient(request, version='1'):
    url = base.url_for(request, 'image')
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    LOG.debug('glanceclient connection created using token "%s" and url "%s"'
              % (request.user.token.id, url))
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


def image_list_detailed(request, marker=None, sort_dir='desc',
                        sort_key='created_at', filters=None, paginate=False):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'filters': filters or {}}
    if marker:
        kwargs['marker'] = marker
    kwargs['sort_dir'] = sort_dir
    kwargs['sort_key'] = sort_key

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
        elif sort_dir == 'asc' and marker is not None:
            has_more_data = True
        # last page condition
        elif marker is not None:
            has_prev_data = True
    else:
        images = list(images_iter)
    return (images, has_more_data, has_prev_data)


def image_update(request, image_id, **kwargs):
    return glanceclient(request).images.update(image_id, **kwargs)


def image_create(request, **kwargs):
    copy_from = kwargs.pop('copy_from', None)
    data = kwargs.pop('data', None)

    image = glanceclient(request).images.create(**kwargs)

    if data:
        thread.start_new_thread(image_update,
                                (request, image.id),
                                {'data': data,
                                 'purge_props': False})
    elif copy_from:
        thread.start_new_thread(image_update,
                                (request, image.id),
                                {'copy_from': copy_from,
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


class Namespace(BaseGlanceMetadefAPIResourceWrapper):

    _attrs = ['namespace', 'display_name', 'description',
              'resource_type_associations', 'visibility', 'protected',
              'created_at', 'updated_at', 'properties', 'objects']

    @property
    def resource_type_associations(self):
        result = [resource_type['name'] for resource_type in
                    getattr(self._apiresource, 'resource_type_associations')]
        return result

    @property
    def public(self):
        if getattr(self._apiresource, 'visibility') == 'public':
            return True
        else:
            return False


def metadefs_namespace_get(request, namespace, resource_type=None, wrap=False):
    namespace = glanceclient(request, '2').\
        metadefs_namespace.get(namespace, resource_type=resource_type)
    # There were problems with using the wrapper class in
    # in nested json serialization. So sometimes, it is not desirable
    # to wrap.
    if wrap:
        return Namespace(namespace)
    else:
        return namespace


def metadefs_namespace_list(request,
                            filters={},
                            sort_dir='desc',
                            sort_key='created_at',
                            marker=None,
                            paginate=False):
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
        elif sort_dir == 'asc' and marker is not None:
            has_more_data = True
        # last page condition
        elif marker is not None:
            has_prev_data = True
    else:
        namespaces = list(namespaces_iter)

    namespaces = [Namespace(namespace) for namespace in namespaces]
    return namespaces, has_more_data, has_prev_data
