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

import new

from cloudfiles import container, storage_object

from .utils import TestDataContainer


def data(TEST):
    TEST.containers = TestDataContainer()
    TEST.objects = TestDataContainer()

    class FakeConnection(object):
        def __init__(self):
            self.cdn_enabled = False

    conn = FakeConnection()

    container_1 = container.Container(conn, name="container_one")
    container_2 = container.Container(conn, name="container_two")
    TEST.containers.add(container_1, container_2)

    object_dict = {"name": "test_object",
                   "content_type": "text/plain",
                   "bytes": 128,
                   "last_modified": None,
                   "hash": "object_hash"}
    obj_dicts = [object_dict]
    for obj_dict in obj_dicts:
        swift_object = storage_object.Object(container_1,
                                             object_record=obj_dict)
        TEST.objects.add(swift_object)

    # Override the list method to return the type of list cloudfiles does.
    def get_object_result_list(self):
        return storage_object.ObjectResults(container_1,
                                            objects=obj_dicts)

    list_method = new.instancemethod(get_object_result_list, TEST.objects)
    TEST.objects.list = list_method
