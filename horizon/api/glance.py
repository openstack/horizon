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
import urlparse

from glanceclient.v1 import client as glance_client

from horizon.api.base import url_for


LOG = logging.getLogger(__name__)


def glanceclient(request):
    o = urlparse.urlparse(url_for(request, 'image'))
    url = "://".join((o.scheme, o.netloc))
    LOG.debug('glanceclient connection created using token "%s" and url "%s"' %
              (request.user.token, url))
    return glance_client.Client(endpoint=url, token=request.user.token)


def image_delete(request, image_id):
    return glanceclient(request).images.delete(image_id)


def image_get(request, image_id):
    """
    Returns an Image object populated with metadata for image
    with supplied identifier.
    """
    return glanceclient(request).images.get(image_id)


def image_list_detailed(request, filters=None):
    filters = filters or {}
    return glanceclient(request).images.list(filters=filters)


def image_update(request, image_id, **kwargs):
    return glanceclient(request).images.update(image_id, **kwargs)


def snapshot_list_detailed(request, extra_filters=None):
    filters = {'property-image_type': 'snapshot'}
    filters.update(extra_filters or {})
    return glanceclient(request).images.list(filters=filters)
