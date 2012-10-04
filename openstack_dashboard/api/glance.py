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

import logging
import thread
import urlparse

from django.conf import settings

import glanceclient as glance_client

from openstack_dashboard.api.base import url_for


LOG = logging.getLogger(__name__)


def glanceclient(request):
    o = urlparse.urlparse(url_for(request, 'image'))
    url = "://".join((o.scheme, o.netloc))
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    LOG.debug('glanceclient connection created using token "%s" and url "%s"'
              % (request.user.token.id, url))
    return glance_client.Client('1', url, token=request.user.token.id,
                                insecure=insecure)


def image_delete(request, image_id):
    return glanceclient(request).images.delete(image_id)


def image_get(request, image_id):
    """
    Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    return glanceclient(request).images.get(image_id)


def image_list_detailed(request, marker=None, filters=None):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
    kwargs = {'filters': filters or {}}
    if marker:
        kwargs['marker'] = marker
    images = list(glanceclient(request).images.list(page_size=page_size,
                                                    limit=limit,
                                                    **kwargs))
    # Glance returns (page_size + 1) items if more items are available
    if(len(images) > page_size):
        return (images[0:-1], True)
    else:
        return (images, False)


def image_update(request, image_id, **kwargs):
    return glanceclient(request).images.update(image_id, **kwargs)


def image_create(request, **kwargs):
    copy_from = None

    if kwargs.get('copy_from'):
        copy_from = kwargs.pop('copy_from')

    image = glanceclient(request).images.create(**kwargs)

    if copy_from:
        thread.start_new_thread(image_update,
                                (request, image.id),
                                {'copy_from': copy_from})

    return image


def snapshot_list_detailed(request, marker=None, extra_filters=None):
    filters = {'property-image_type': 'snapshot'}
    filters.update(extra_filters or {})
    return image_list_detailed(request, marker, filters)
