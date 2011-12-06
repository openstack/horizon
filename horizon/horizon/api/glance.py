# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
import urlparse

from glance import client as glance_client

from horizon.api.base import *


LOG = logging.getLogger(__name__)


class Image(APIDictWrapper):
    """Simple wrapper around glance image dictionary"""
    _attrs = ['checksum', 'container_format', 'created_at', 'deleted',
             'deleted_at', 'disk_format', 'id', 'is_public', 'location',
             'name', 'properties', 'size', 'status', 'updated_at', 'owner']

    def __getattr__(self, attrname):
        if attrname == "properties":
            return ImageProperties(super(Image, self).__getattr__(attrname))
        else:
            return super(Image, self).__getattr__(attrname)


class ImageProperties(APIDictWrapper):
    """Simple wrapper around glance image properties dictionary"""
    _attrs = ['architecture', 'image_location', 'image_state', 'kernel_id',
             'project_id', 'ramdisk_id', 'image_type']


def glance_api(request):
    o = urlparse.urlparse(url_for(request, 'image'))
    LOG.debug('glance_api connection created for host "%s:%d"' %
                     (o.hostname, o.port))
    return glance_client.Client(o.hostname,
                                o.port,
                                auth_tok=request.user.token)


def image_create(request, image_meta, image_file):
    return Image(glance_api(request).add_image(image_meta, image_file))


def image_delete(request, image_id):
    return glance_api(request).delete_image(image_id)


def image_get(request, image_id):
    """
    Returns the actual image file from Glance for image with
    supplied identifier
    """
    return glance_api(request).get_image(image_id)[1]


def image_get_meta(request, image_id):
    """
    Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    return Image(glance_api(request).get_image_meta(image_id))


def image_list_detailed(request):
    return [Image(i) for i in glance_api(request).get_images_detailed()]


def image_update(request, image_id, image_meta=None):
    image_meta = image_meta and image_meta or {}
    return Image(glance_api(request).update_image(image_id,
                                                  image_meta=image_meta))


def snapshot_list_detailed(request):
    filters = {}
    filters['property-image_type'] = 'snapshot'
    filters['is_public'] = 'none'
    return [Image(i) for i in glance_api(request)
                             .get_images_detailed(filters=filters)]
