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

import logging

import cloudfiles
from django.conf import settings

from horizon.api.base import *


LOG = logging.getLogger(__name__)


class Container(APIResourceWrapper):
    """Simple wrapper around cloudfiles.container.Container"""
    _attrs = ['name', 'size_used', 'object_count', ]


class SwiftObject(APIResourceWrapper):
    _attrs = ['name', 'container', 'size', 'metadata', 'last_modified',
              'metadata']

    def sync_metadata(self):
        self._apiresource.sync_metadata()


class SwiftAuthentication(object):
    """Auth container to pass CloudFiles storage URL and token from
       session.
    """
    def __init__(self, storage_url, auth_token):
        self.storage_url = storage_url
        self.auth_token = auth_token

    def authenticate(self):
        return (self.storage_url, '', self.auth_token)


def swift_api(request):
    LOG.debug('object store connection created using token "%s"'
                ' and url "%s"' %
                (request.session['token'], url_for(request, 'object-store')))
    auth = SwiftAuthentication(url_for(request, 'object-store'),
                               request.session['token'])
    return cloudfiles.get_connection(auth=auth)


def swift_container_exists(request, container_name):
    try:
        swift_api(request).get_container(container_name)
        return True
    except cloudfiles.errors.NoSuchContainer:
        return False


def swift_object_exists(request, container_name, object_name):
    container = swift_api(request).get_container(container_name)

    try:
        container.get_object(object_name)
        return True
    except cloudfiles.errors.NoSuchObject:
        return False


def swift_get_containers(request, marker=None):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    containers = [Container(c) for c in swift_api(request).get_all_containers(
                    limit=limit + 1,
                    marker=marker)]
    if(len(containers) > limit):
        return (containers[0:-1], True)
    else:
        return (containers, False)


def swift_create_container(request, name):
    if swift_container_exists(request, name):
        raise Exception('Container with name %s already exists.' % (name))

    return Container(swift_api(request).create_container(name))


def swift_delete_container(request, name):
    swift_api(request).delete_container(name)


def swift_get_objects(request, container_name, prefix=None, marker=None):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    container = swift_api(request).get_container(container_name)
    objects = [SwiftObject(o) for o in
            container.get_objects(prefix=prefix, marker=marker,
                                  limit=limit + 1)]
    if(len(objects) > limit):
        return (objects[0:-1], True)
    else:
        return (objects, False)


def swift_copy_object(request, orig_container_name, orig_object_name,
                      new_container_name, new_object_name):
    container = swift_api(request).get_container(orig_container_name)

    if swift_object_exists(request, new_container_name, new_object_name):
        raise Exception('Object with name %s already exists in container %s'
        % (new_object_name, new_container_name))

    orig_obj = container.get_object(orig_object_name)
    return orig_obj.copy_to(new_container_name, new_object_name)


def swift_upload_object(request, container_name, object_name, object_data):
    container = swift_api(request).get_container(container_name)
    obj = container.create_object(object_name)
    obj.write(object_data)
    return obj


def swift_delete_object(request, container_name, object_name):
    container = swift_api(request).get_container(container_name)
    container.delete_object(object_name)


def swift_get_object(request, container_name, object_name):
    container = swift_api(request).get_container(container_name)
    return container.get_object(object_name)


def swift_get_object_data(request, container_name, object_name):
    container = swift_api(request).get_container(container_name)
    return container.get_object(object_name).stream()
