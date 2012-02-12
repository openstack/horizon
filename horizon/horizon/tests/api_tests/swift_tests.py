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

import cloudfiles

from horizon import api
from horizon import exceptions
from horizon import test


class SwiftApiTests(test.APITestCase):
    def test_swift_get_containers(self):
        containers = self.containers.list()
        swift_api = self.stub_swiftclient()
        swift_api.get_all_containers(limit=1001,
                                     marker=None).AndReturn(containers)
        self.mox.ReplayAll()

        (conts, more) = api.swift_get_containers(self.request)
        self.assertEqual(len(conts), len(containers))
        self.assertFalse(more)

    def test_swift_create_container(self):
        container = self.containers.first()
        swift_api = self.stub_swiftclient(expected_calls=2)
        # Check for existence, then create
        exc = cloudfiles.errors.NoSuchContainer()
        swift_api.get_container(container.name).AndRaise(exc)
        swift_api.create_container(container.name).AndReturn(container)
        self.mox.ReplayAll()
        # Verification handled by mox, no assertions needed.
        api.swift_create_container(self.request, container.name)

    def test_swift_create_duplicate_container(self):
        container = self.containers.first()
        swift_api = self.stub_swiftclient()
        swift_api.get_container(container.name).AndReturn(container)
        self.mox.ReplayAll()
        # Verification handled by mox, no assertions needed.
        with self.assertRaises(exceptions.AlreadyExists):
            api.swift_create_container(self.request, container.name)

    def test_swift_get_objects(self):
        container = self.containers.first()
        objects = self.objects.list()

        swift_api = self.stub_swiftclient()
        swift_api.get_container(container.name).AndReturn(container)
        self.mox.StubOutWithMock(container, 'get_objects')
        container.get_objects(limit=1001,
                              marker=None,
                              prefix=None).AndReturn(objects)
        self.mox.ReplayAll()

        (objs, more) = api.swift_get_objects(self.request, container.name)
        self.assertEqual(len(objs), len(objects))
        self.assertFalse(more)

    def test_swift_upload_object(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = 'someData'

        swift_api = self.stub_swiftclient()
        swift_api.get_container(container.name).AndReturn(container)
        self.mox.StubOutWithMock(container, 'create_object')
        container.create_object(obj.name).AndReturn(obj)
        self.mox.StubOutWithMock(obj, 'write')
        obj.write(OBJECT_DATA).AndReturn(obj)
        self.mox.ReplayAll()

        ret_val = api.swift_upload_object(self.request,
                                          container.name,
                                          obj.name,
                                          OBJECT_DATA)
        self.assertEqual(ret_val, obj)

    def test_swift_delete_object(self):
        container = self.containers.first()
        obj = self.objects.first()

        swift_api = self.stub_swiftclient()
        swift_api.get_container(container.name).AndReturn(container)
        self.mox.StubOutWithMock(container, 'delete_object')
        container.delete_object(obj.name).AndReturn(obj)
        self.mox.ReplayAll()

        ret_val = api.swift_delete_object(self.request,
                                          container.name,
                                          obj.name)

        self.assertIsNone(ret_val)

    def test_swift_get_object_data(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = 'objectData'

        swift_api = self.stub_swiftclient()
        swift_api.get_container(container.name).AndReturn(container)
        self.mox.StubOutWithMock(container, 'get_object')
        container.get_object(obj.name).AndReturn(obj)
        self.mox.StubOutWithMock(obj, 'stream')
        obj.stream().AndReturn(OBJECT_DATA)
        self.mox.ReplayAll()

        ret_val = api.swift_get_object_data(self.request,
                                            container.name,
                                            obj.name)
        self.assertEqual(ret_val, OBJECT_DATA)

    def test_swift_object_exists(self):
        container = self.containers.first()
        obj = self.objects.first()

        swift_api = self.stub_swiftclient(expected_calls=2)
        self.mox.StubOutWithMock(container, 'get_object')
        swift_api.get_container(container.name).AndReturn(container)
        container.get_object(obj.name).AndReturn(obj)
        swift_api.get_container(container.name).AndReturn(container)
        exc = cloudfiles.errors.NoSuchObject()
        container.get_object(obj.name).AndRaise(exc)
        self.mox.ReplayAll()

        args = self.request, container.name, obj.name
        self.assertTrue(api.swift_object_exists(*args))
        # Again, for a "non-existent" object
        self.assertFalse(api.swift_object_exists(*args))

    def test_swift_copy_object(self):
        container = self.containers.get(name="container_one")
        container_2 = self.containers.get(name="container_two")
        obj = self.objects.first()

        swift_api = self.stub_swiftclient()
        self.mox.StubOutWithMock(api.swift, 'swift_object_exists')
        swift_api.get_container(container.name).AndReturn(container)
        api.swift.swift_object_exists(self.request,
                                      container_2.name,
                                      obj.name).AndReturn(False)
        self.mox.StubOutWithMock(container, 'get_object')
        container.get_object(obj.name).AndReturn(obj)
        self.mox.StubOutWithMock(obj, 'copy_to')
        obj.copy_to(container_2.name, obj.name)
        self.mox.ReplayAll()
        # Verification handled by mox. No assertions needed.
        api.swift_copy_object(self.request,
                              container.name,
                              obj.name,
                              container_2.name,
                              obj.name)
