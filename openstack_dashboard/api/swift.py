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

import swiftclient

from django.conf import settings
from django.utils.translation import ugettext as _

from horizon import exceptions

from openstack_dashboard.api.base import url_for, APIDictWrapper


LOG = logging.getLogger(__name__)
FOLDER_DELIMITER = "/"


class Container(APIDictWrapper):
    pass


class StorageObject(APIDictWrapper):
    def __init__(self, apidict, container_name, orig_name=None, data=None):
        super(StorageObject, self).__init__(apidict)
        self.container_name = container_name
        self.orig_name = orig_name
        self.data = data


class PseudoFolder(APIDictWrapper):
    """
    Wrapper to smooth out discrepencies between swift "subdir" items
    and swift pseudo-folder objects.
    """

    def __init__(self, apidict, container_name):
        super(PseudoFolder, self).__init__(apidict)
        self.container_name = container_name

    def _has_content_type(self):
        content_type = self._apidict.get("content_type", None)
        return content_type == "application/directory"

    @property
    def name(self):
        if self._has_content_type():
            return self._apidict['name']
        return self.subdir.rstrip(FOLDER_DELIMITER)

    @property
    def bytes(self):
        if self._has_content_type():
            return self._apidict['bytes']
        return None

    @property
    def content_type(self):
        return "application/directory"


def _objectify(items, container_name):
    """ Splits a listing of objects into their appropriate wrapper classes. """
    objects = {}
    subdir_markers = []

    # Deal with objects and object pseudo-folders first, save subdirs for later
    for item in items:
        if item.get("content_type", None) == "application/directory":
            objects[item['name']] = PseudoFolder(item, container_name)
        elif item.get("subdir", None) is not None:
            subdir_markers.append(PseudoFolder(item, container_name))
        else:
            objects[item['name']] = StorageObject(item, container_name)
    # Revisit subdirs to see if we have any non-duplicates
    for item in subdir_markers:
        if item.name not in objects.keys():
            objects[item.name] = item
    return objects.values()


def swift_api(request):
    endpoint = url_for(request, 'object-store')
    LOG.debug('Swift connection created using token "%s" and url "%s"'
              % (request.user.token.id, endpoint))
    return swiftclient.client.Connection(None,
                                         request.user.username,
                                         None,
                                         preauthtoken=request.user.token.id,
                                         preauthurl=endpoint,
                                         auth_version="2.0")


def swift_container_exists(request, container_name):
    try:
        swift_api(request).head_container(container_name)
        return True
    except swiftclient.client.ClientException:
        return False


def swift_object_exists(request, container_name, object_name):
    try:
        swift_api(request).head_object(container_name, object_name)
        return True
    except swiftclient.client.ClientException:
        return False


def swift_get_containers(request, marker=None):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    headers, containers = swift_api(request).get_account(limit=limit + 1,
                                                         marker=marker,
                                                         full_listing=True)
    container_objs = [Container(c) for c in containers]
    if(len(container_objs) > limit):
        return (container_objs[0:-1], True)
    else:
        return (container_objs, False)


def swift_create_container(request, name):
    if swift_container_exists(request, name):
        raise exceptions.AlreadyExists(name, 'container')
    swift_api(request).put_container(name)
    return Container({'name': name})


def swift_delete_container(request, name):
    swift_api(request).delete_container(name)
    return True


def swift_get_objects(request, container_name, prefix=None, marker=None,
                      limit=None):
    limit = limit or getattr(settings, 'API_RESULT_LIMIT', 1000)
    kwargs = dict(prefix=prefix,
                  marker=marker,
                  limit=limit + 1,
                  delimiter=FOLDER_DELIMITER,
                  full_listing=True)
    headers, objects = swift_api(request).get_container(container_name,
                                                          **kwargs)
    object_objs = _objectify(objects, container_name)

    if(len(object_objs) > limit):
        return (object_objs[0:-1], True)
    else:
        return (object_objs, False)


def swift_filter_objects(request, filter_string, container_name, prefix=None,
                         marker=None):
    # FIXME(kewu): Swift currently has no real filtering API, thus the marker
    # parameter here won't actually help the pagination. For now I am just
    # getting the largest number of objects from a container and filtering
    # based on those objects.
    limit = 9999
    objects = swift_get_objects(request,
                                container_name,
                                prefix=prefix,
                                marker=marker,
                                limit=limit)
    filter_string_list = filter_string.lower().strip().split(' ')

    def matches_filter(obj):
        for q in filter_string_list:
            return wildcard_search(obj.name.lower(), q)

    return filter(matches_filter, objects[0])


def wildcard_search(string, q):
    q_list = q.split('*')
    if all(map(lambda x: x == '', q_list)):
        return True
    elif q_list[0] not in string:
        return False
    else:
        if q_list[0] == '':
            tail = string
        else:
            head, delimiter, tail = string.partition(q_list[0])
        return wildcard_search(tail, '*'.join(q_list[1:]))


def swift_copy_object(request, orig_container_name, orig_object_name,
                      new_container_name, new_object_name):
    try:
        # FIXME(gabriel): The swift currently fails at unicode in the
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

    if swift_object_exists(request, new_container_name, new_object_name):
        raise exceptions.AlreadyExists(new_object_name, 'object')

    headers = {"X-Copy-From": FOLDER_DELIMITER.join([orig_container_name,
                                                     orig_object_name])}
    return swift_api(request).put_object(new_container_name,
                                         new_object_name,
                                         None,
                                         headers=headers)


def swift_create_subfolder(request, container_name, folder_name):
    headers = {'content-type': 'application/directory',
               'content-length': 0}
    etag = swift_api(request).put_object(container_name,
                                         folder_name,
                                         None,
                                         headers=headers)
    obj_info = {'subdir': folder_name, 'etag': etag}
    return PseudoFolder(obj_info, container_name)


def swift_upload_object(request, container_name, object_name, object_file):
    headers = {}
    headers['X-Object-Meta-Orig-Filename'] = object_file.name
    etag = swift_api(request).put_object(container_name,
                                         object_name,
                                         object_file,
                                         headers=headers)
    obj_info = {'name': object_name, 'bytes': object_file.size, 'etag': etag}
    return StorageObject(obj_info, container_name)


def swift_delete_object(request, container_name, object_name):
    swift_api(request).delete_object(container_name, object_name)
    return True


def swift_get_object(request, container_name, object_name):
    headers, data = swift_api(request).get_object(container_name, object_name)
    orig_name = headers.get("x-object-meta-orig-filename")
    obj_info = {'name': object_name, 'bytes': len(data)}
    return StorageObject(obj_info,
                         container_name,
                         orig_name=orig_name,
                         data=data)
