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

from __future__ import absolute_import

import cloudfiles
from django import http
from mox import IsA

from horizon.tests.api_tests.utils import *


class SwiftApiTests(APITestCase):
    def setUp(self):
        super(SwiftApiTests, self).setUp()
        self.request = http.HttpRequest()
        self.request.session = dict()
        self.request.session['token'] = TEST_TOKEN

    def stub_swift_api(self, count=1):
        self.mox.StubOutWithMock(api.swift, 'swift_api')
        swift_api = self.mox.CreateMock(cloudfiles.connection.Connection)
        for i in range(count):
            api.swift.swift_api(IsA(http.HttpRequest)).AndReturn(swift_api)
        return swift_api

    def test_swift_get_containers(self):
        containers = (TEST_RETURN, TEST_RETURN + '2')

        swift_api = self.stub_swift_api()

        swift_api.get_all_containers(limit=1001,
                                     marker=None).AndReturn(containers)

        self.mox.ReplayAll()

        (conts, more) = api.swift_get_containers(self.request)

        self.assertEqual(len(conts), len(containers))
        self.assertFalse(more)

        for container in conts:
            self.assertIsInstance(container, api.Container)
            self.assertIn(container._apiresource, containers)

    def test_swift_create_container(self):
        NAME = 'containerName'

        swift_api = self.stub_swift_api()
        self.mox.StubOutWithMock(api.swift, 'swift_container_exists')

        api.swift.swift_container_exists(self.request,
                                   NAME).AndReturn(False)
        swift_api.create_container(NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_create_container(self.request, NAME)

        self.assertIsInstance(ret_val, api.Container)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

    def test_swift_delete_container(self):
        NAME = 'containerName'

        swift_api = self.stub_swift_api()

        swift_api.delete_container(NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_delete_container(self.request, NAME)

        self.assertIsNone(ret_val)

    def test_swift_get_objects(self):
        NAME = 'containerName'

        swift_objects = (TEST_RETURN, TEST_RETURN + '2')
        container = self.mox.CreateMock(cloudfiles.container.Container)
        container.get_objects(limit=1001,
                              marker=None,
                              prefix=None).AndReturn(swift_objects)

        swift_api = self.stub_swift_api()

        swift_api.get_container(NAME).AndReturn(container)

        self.mox.ReplayAll()

        (objects, more) = api.swift_get_objects(self.request, NAME)

        self.assertEqual(len(objects), len(swift_objects))
        self.assertFalse(more)

        for swift_object in objects:
            self.assertIsInstance(swift_object, api.SwiftObject)
            self.assertIn(swift_object._apiresource, swift_objects)

    def test_swift_get_objects_with_prefix(self):
        NAME = 'containerName'
        PREFIX = 'prefacedWith'

        swift_objects = (TEST_RETURN, TEST_RETURN + '2')
        container = self.mox.CreateMock(cloudfiles.container.Container)
        container.get_objects(limit=1001,
                              marker=None,
                              prefix=PREFIX).AndReturn(swift_objects)

        swift_api = self.stub_swift_api()

        swift_api.get_container(NAME).AndReturn(container)

        self.mox.ReplayAll()

        (objects, more) = api.swift_get_objects(self.request,
                                        NAME,
                                        prefix=PREFIX)

        self.assertEqual(len(objects), len(swift_objects))
        self.assertFalse(more)

        for swift_object in objects:
            self.assertIsInstance(swift_object, api.SwiftObject)
            self.assertIn(swift_object._apiresource, swift_objects)

    def test_swift_upload_object(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'
        OBJECT_DATA = 'someData'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        swift_object = self.mox.CreateMock(cloudfiles.storage_object.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.create_object(OBJECT_NAME).AndReturn(swift_object)
        swift_object.write(OBJECT_DATA).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_upload_object(self.request,
                                          CONTAINER_NAME,
                                          OBJECT_NAME,
                                          OBJECT_DATA)

        self.assertEqual(ret_val, swift_object)

    def test_swift_delete_object(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.delete_object(OBJECT_NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_delete_object(self.request,
                                          CONTAINER_NAME,
                                          OBJECT_NAME)

        self.assertIsNone(ret_val)

    def test_swift_get_object_data(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'
        OBJECT_DATA = 'objectData'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        swift_object = self.mox.CreateMock(cloudfiles.storage_object.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.get_object(OBJECT_NAME).AndReturn(swift_object)
        swift_object.stream().AndReturn(OBJECT_DATA)

        self.mox.ReplayAll()

        ret_val = api.swift_get_object_data(self.request,
                                            CONTAINER_NAME,
                                            OBJECT_NAME)

        self.assertEqual(ret_val, OBJECT_DATA)

    def test_swift_object_exists(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        swift_object = self.mox.CreateMock(cloudfiles.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.get_object(OBJECT_NAME).AndReturn(swift_object)

        self.mox.ReplayAll()

        ret_val = api.swift_object_exists(self.request,
                                          CONTAINER_NAME,
                                          OBJECT_NAME)
        self.assertTrue(ret_val)

    def test_swift_copy_object(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        self.mox.StubOutWithMock(api.swift, 'swift_object_exists')

        swift_object = self.mox.CreateMock(cloudfiles.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        api.swift.swift_object_exists(self.request,
                                CONTAINER_NAME,
                                OBJECT_NAME).AndReturn(False)

        container.get_object(OBJECT_NAME).AndReturn(swift_object)
        swift_object.copy_to(CONTAINER_NAME, OBJECT_NAME)

        self.mox.ReplayAll()

        ret_val = api.swift_copy_object(self.request, CONTAINER_NAME,
                                        OBJECT_NAME, CONTAINER_NAME,
                                        OBJECT_NAME)

        self.assertIsNone(ret_val)
