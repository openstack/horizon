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

import itertools
import logging
import thread

from django.conf import settings

import glanceclient as glance_client

from horizon.utils import functions as utils

from openstack_dashboard.api import base


LOG = logging.getLogger(__name__)


class ImageCustomProperty(object):
    def __init__(self, image_id, key, val):
        self.image_id = image_id
        self.id = key
        self.key = key
        self.value = val


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


def image_get_properties(request, image_id, reserved=True):
    """List all custom properties of an image."""
    image = glanceclient(request, '2').images.get(image_id)
    reserved_props = getattr(settings, 'IMAGE_RESERVED_CUSTOM_PROPERTIES', [])
    properties_list = []
    for key in image.keys():
        if reserved or key not in reserved_props:
            prop = ImageCustomProperty(image_id, key, image.get(key))
            properties_list.append(prop)
    return properties_list


def image_get_property(request, image_id, key, reserved=True):
    """Get a custom property of an image."""
    for prop in image_get_properties(request, image_id, reserved):
        if prop.key == key:
            return prop
    return None


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


def image_update_properties(request, image_id, **kwargs):
    """Add or update a custom property of an image."""
    return glanceclient(request, '2').images.update(image_id, None, **kwargs)


def image_delete_properties(request, image_id, keys):
    """Delete custom properties for an image."""
    return glanceclient(request, '2').images.update(image_id, keys)
