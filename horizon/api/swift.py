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

import logging

import cloudfiles
from django.conf import settings
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon.api.base import url_for

from rgwauthAPI import RadosGW as RGW

LOG = logging.getLogger(__name__)


class SwiftAuthentication(object):
    """ Auth container in the format CloudFiles expects. """
    def __init__(self, storage_url, auth_token):
        self.storage_url = storage_url
        self.auth_token = auth_token

    def authenticate(self):
        return (self.storage_url, '', self.auth_token)


def swift_api(request):
    endpoint = url_for(request, 'object-store')
    auth_token = request.session['token']

    use_radosgw_auth = getattr(settings, 'SWIFT_USE_RADOSGW_AUTH', False)
    sync_radosgw_auth = getattr(settings, 'SYNC_KEYSTONE_RADOSGW_AUTH', False)
    if (use_radosgw_auth == True):
        """ Same tenant's users shares same bucket """
        uid,subuser = request.session['tenant_id'],request.session['user_id']

        LOG.debug('Get radosgw auth by user: %s:%s and endpoint %s'                 
				% (uid, subuser, endpoint))
        try:
            rgw = RGW(uid, subuser, endpoint)
            storage_url, auth_token = rgw.authenticate('swift', sync_radosgw_auth)
        except Exception as e:
            # rgwauthAPI now puts error msg in args[0]
            raise exceptions.RadosgwExceptions(str(e.args[0]))

    LOG.debug('Swift connection created using token "%s" and url "%s"'
              % (auth_token, storage_url))
    auth = SwiftAuthentication(storage_url, auth_token)
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
    containers = swift_api(request).get_all_containers(limit=limit + 1,
                                                       marker=marker)
    if(len(containers) > limit):
        return (containers[0:-1], True)
    else:
        return (containers, False)


def swift_create_container(request, name):
    if swift_container_exists(request, name):
        raise exceptions.AlreadyExists(name, 'container')
    return swift_api(request).create_container(name)


def swift_delete_container(request, name):
    swift_api(request).delete_container(name)

def swift_filter_objects(s):
    return s[u'name'].find('/') == -1

def swift_filter_names(s):
    return s.find('/') == -1

def swift_get_objects(request, container_name, prefix=None, marker=None):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    container = swift_api(request).get_container(container_name)
    objects = container.get_objects(prefix=prefix,
                                    marker=marker,
                                    limit=limit + 1)
    # This branch doesn't support to show objects which have
    # '/' in their names now (object is a directory or files in directorys)
    # but ceph rados supports that, so the objects may be upload to 
    # container by s3 api. Therefore, just filter out objects like that.
    objects._objects = filter(swift_filter_objects, objects._objects)
    objects._names = filter(swift_filter_names, objects._names)
    if(len(objects) > limit):
        return (objects[0:-1], True)
    else:
        return (objects, False)


def swift_copy_object(request, orig_container_name, orig_object_name,
                      new_container_name, new_object_name):
    try:
        # FIXME(gabriel): Cloudfiles currently fails at unicode in the
        # copy_to method, so to provide a better experience we check for
        # unicode here and pre-empt with an error message rather than
        # letting the call fail.
        str(orig_container_name)
        str(orig_object_name)
        str(new_container_name)
        str(new_object_name)
    except UnicodeEncodeError:
        raise exceptions.HorizonException(_("Unicode is not currently "
                                            "supported for object copy."))
    container = swift_api(request).get_container(orig_container_name)

    if swift_object_exists(request, new_container_name, new_object_name):
        raise exceptions.AlreadyExists(new_object_name, 'object')

    orig_obj = container.get_object(orig_object_name)
    return orig_obj.copy_to(new_container_name, new_object_name)


def swift_upload_object(request, container_name, object_name, object_file):
    container = swift_api(request).get_container(container_name)
    # radosgw needs to know the size exactly
    obj = cloudfiles.storage_object.Object(container, object_name, 
            object_record = {
                'name': object_name,
                'content_type': object_file.content_type,
                'bytes': object_file._size,
                'last_modified': None,
                'hash': None
            })
    obj.send(object_file)
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
