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
from oslo_utils import timeutils

from django.utils import http as utils_http

from openstack_dashboard.api import swift
from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.containers = utils.TestDataContainer()
    TEST.objects = utils.TestDataContainer()
    TEST.folder = utils.TestDataContainer()

    # '%' can break URL if not properly url-quoted
    # ' ' (space) can break 'Content-Disposition' if not properly
    # double-quoted

    container_dict_1 = {"name": u"container one%\u6346",
                        "container_object_count": 2,
                        "container_bytes_used": 256,
                        "timestamp": timeutils.isotime(),
                        "is_public": False,
                        "public_url": ""}
    container_1 = swift.Container(container_dict_1)
    container_2_name = u"container_two\u6346"
    container_dict_2 = {"name": container_2_name,
                        "container_object_count": 4,
                        "container_bytes_used": 1024,
                        "timestamp": timeutils.isotime(),
                        "is_public": True,
                        "public_url":
                            "http://public.swift.example.com:8080/" +
                            "v1/project_id/%s" % utils_http.urlquote(
                                container_2_name)}
    container_2 = swift.Container(container_dict_2)
    container_dict_3 = {"name": u"container,three%\u6346",
                        "container_object_count": 2,
                        "container_bytes_used": 256,
                        "timestamp": timeutils.isotime(),
                        "is_public": False,
                        "public_url": ""}
    container_3 = swift.Container(container_dict_3)
    TEST.containers.add(container_1, container_2, container_3)

    object_dict = {"name": u"test object%\u6346",
                   "content_type": u"text/plain",
                   "bytes": 128,
                   "timestamp": timeutils.isotime(),
                   "last_modified": None,
                   "hash": u"object_hash"}
    object_dict_2 = {"name": u"test_object_two\u6346",
                     "content_type": u"text/plain",
                     "bytes": 128,
                     "timestamp": timeutils.isotime(),
                     "last_modified": None,
                     "hash": u"object_hash_2"}
    object_dict_3 = {"name": u"test,object_three%\u6346",
                     "content_type": u"text/plain",
                     "bytes": 128,
                     "timestamp": timeutils.isotime(),
                     "last_modified": None,
                     "hash": u"object_hash"}
    object_dict_4 = {"name": u"test.txt",
                     "content_type": u"text/plain",
                     "bytes": 128,
                     "timestamp": timeutils.isotime(),
                     "last_modified": None,
                     "hash": u"object_hash"}
    obj_dicts = [object_dict, object_dict_2, object_dict_3, object_dict_4]
    obj_data = b"Fake Data"

    for obj_dict in obj_dicts:
        swift_object = swift.StorageObject(obj_dict,
                                           container_1.name,
                                           data=obj_data)
        TEST.objects.add(swift_object)

    folder_dict = {"name": u"test folder%\u6346",
                   "content_type": u"text/plain",
                   "bytes": 128,
                   "timestamp": timeutils.isotime(),
                   "_table_data_type": u"subfolders",
                   "last_modified": None,
                   "hash": u"object_hash"}

    TEST.folder.add(swift.PseudoFolder(folder_dict, container_1.name))
