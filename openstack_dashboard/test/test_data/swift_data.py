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

from openstack_dashboard.api import swift
from openstack_dashboard.openstack.common import timeutils

from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.containers = utils.TestDataContainer()
    TEST.objects = utils.TestDataContainer()

    container_dict_1 = {"name": u"container_one\u6346",
                        "container_object_count": 2,
                        "container_bytes_used": 256,
                        "timestamp": timeutils.isotime()}
    container_1 = swift.Container(container_dict_1)
    container_dict_2 = {"name": u"container_two\u6346",
                        "container_object_count": 4,
                        "container_bytes_used": 1024,
                        "timestamp": timeutils.isotime()}
    container_2 = swift.Container(container_dict_2)
    TEST.containers.add(container_1, container_2)

    object_dict = {"name": u"test_object\u6346",
                   "content_type": u"text/plain",
                   "bytes": 128,
                   "timestamp": timeutils.isotime(),
                   "last_modified": None,
                   "hash": u"object_hash"}
    obj_dicts = [object_dict]
    obj_data = "Fake Data"

    for obj_dict in obj_dicts:
        swift_object = swift.StorageObject(obj_dict,
                                           container_1.name,
                                           data=obj_data)
        TEST.objects.add(swift_object)
