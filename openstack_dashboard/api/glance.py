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

import itertools
import logging
import thread
import urlparse

from django.conf import settings  # noqa

import glanceclient as glance_client

from openstack_dashboard.api import base


LOG = logging.getLogger(__name__)


def glanceclient(request):
    o = urlparse.urlparse(base.url_for(request, 'image'))
    url = "://".join((o.scheme, o.netloc))
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    LOG.debug('glanceclient connection created using token "%s" and url "%s"'
              % (request.user.token.id, url))
    return glance_client.Client('1', url, token=request.user.token.id,
                                insecure=insecure, cacert=cacert)


def image_delete(request, image_id):
    return glanceclient(request).images.delete(image_id)


def image_get(request, image_id):
    """
    Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    return glanceclient(request).images.get(image_id)


def image_list_detailed(request, marker=None, filters=None, paginate=False):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = request.session.get('horizon_pagesize',
                                    getattr(settings, 'API_RESULT_PAGE_SIZE',
                                            20))

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {'filters': filters or {}}
    if marker:
        kwargs['marker'] = marker

    images_iter = glanceclient(request).images.list(page_size=request_size,
                                                    limit=limit,
                                                    **kwargs)
    has_more_data = False
    if paginate:
        images = list(itertools.islice(images_iter, request_size))
        if len(images) > page_size:
            images.pop(-1)
            has_more_data = True
    else:
        images = list(images_iter)
    return (images, has_more_data)


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
