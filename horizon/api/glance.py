# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import functools
import logging
import urlparse

from django.utils.decorators import available_attrs
from django.conf import settings

from glance import client as glance_client
from glance.common import exception as glance_exception

from horizon.api.base import APIDictWrapper, url_for


LOG = logging.getLogger(__name__)


def catch_glance_exception(func):
    """
    The glance client sometimes throws ``Exception`` classed exceptions for
    HTTP communication issues. Catch those, and rethrow them as
    ``glance_client.ClientConnectionErrors`` so that we can do something
    useful with them.
    """
    # TODO(johnp): Remove this once Bug 952618 is fixed in the glance client.
    @functools.wraps(func, assigned=available_attrs(func))
    def inner_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            exc_message = str(exc)
            if('Unknown error occurred' in exc_message or
                    'Internal Server error' in exc_message):
                raise glance_exception.ClientConnectionError(exc_message)
            raise
    return inner_func


class Image(APIDictWrapper):
    """
    Wrapper around glance image dictionary to make it object-like and provide
    access to image properties.
    """
    _attrs = ['checksum', 'container_format', 'created_at', 'deleted',
             'deleted_at', 'disk_format', 'id', 'is_public', 'location',
             'name', 'properties', 'size', 'status', 'updated_at', 'owner']

    def __getattr__(self, attrname):
        if attrname == "properties":
            if not hasattr(self, "_properties"):
                properties_dict = super(Image, self).__getattr__(attrname)
                self._properties = ImageProperties(properties_dict)
            return self._properties
        else:
            return super(Image, self).__getattr__(attrname)


class ImageProperties(APIDictWrapper):
    """
    Wrapper around glance image properties dictionary to make it object-like.
    """
    _attrs = ['architecture', 'image_location', 'image_state', 'kernel_id',
             'project_id', 'ramdisk_id', 'image_type']


@catch_glance_exception
def glanceclient(request):
    o = urlparse.urlparse(url_for(request, 'image'))
    LOG.debug('glanceclient connection created for host "%s:%d"' %
                     (o.hostname, o.port))
    return glance_client.Client(o.hostname,
                                o.port,
                                auth_tok=request.user.token)


@catch_glance_exception
def image_create(request, image_meta, image_file):
    return Image(glanceclient(request).add_image(image_meta, image_file))


@catch_glance_exception
def image_delete(request, image_id):
    return glanceclient(request).delete_image(image_id)


@catch_glance_exception
def image_get(request, image_id):
    """
    Returns the actual image file from Glance for image with
    supplied identifier
    """
    return glanceclient(request).get_image(image_id)[1]


@catch_glance_exception
def image_get_meta(request, image_id):
    """
    Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    return Image(glanceclient(request).get_image_meta(image_id))


@catch_glance_exception
def image_list_detailed(request, marker=None, filters=None):
    filters = filters or {}
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    image_dicts = glanceclient(request).get_images_detailed(limit=limit + 1,
                                                            marker=marker,
                                                            filters=filters)
    images = [Image(i) for i in image_dicts]
    if(len(images) > limit):
        return (images[0:-1], True)
    else:
        return (images, False)


@catch_glance_exception
def image_update(request, image_id, image_meta=None):
    image_meta = image_meta and image_meta or {}
    return Image(glanceclient(request).update_image(image_id,
                                                  image_meta=image_meta))


@catch_glance_exception
def snapshot_list_detailed(request, marker=None, extra_filters=None):
    filters = {'property-image_type': 'snapshot'}
    filters.update(extra_filters or {})
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    image_dicts = glanceclient(request).get_images_detailed(limit=limit + 1,
                                                            marker=marker,
                                                            filters=filters)
    images = [Image(i) for i in image_dicts]
    if(len(images) > limit):
        return (images[0:-1], True)
    else:
        return (images, False)
