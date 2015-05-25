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

from mox import IsA  # noqa

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class SwiftApiTests(test.APITestCase):
    def test_swift_get_containers(self):
        containers = self.containers.list()
        cont_data = [c._apidict for c in containers]
        swift_api = self.stub_swiftclient()
        swift_api.get_account(limit=1001,
                              marker=None,
                              full_listing=True).AndReturn([{}, cont_data])
        self.mox.ReplayAll()

        (conts, more) = api.swift.swift_get_containers(self.request)
        self.assertEqual(len(containers), len(conts))
        self.assertFalse(more)

    def test_swift_get_container_with_data(self):
        container = self.containers.first()
        objects = self.objects.list()
        swift_api = self.stub_swiftclient()
        swift_api.get_object(container.name, "") \
            .AndReturn((container, objects))
        self.mox.ReplayAll()

        cont = api.swift.swift_get_container(self.request, container.name)
        self.assertEqual(container.name, cont.name)
        self.assertEqual(len(objects), len(cont.data))

    def test_swift_get_container_without_data(self):
        container = self.containers.first()
        swift_api = self.stub_swiftclient()
        swift_api.head_container(container.name).AndReturn(container)
        self.mox.ReplayAll()

        cont = api.swift.swift_get_container(self.request,
                                             container.name,
                                             with_data=False)
        self.assertEqual(cont.name, container.name)
        self.assertIsNone(cont.data)

    def test_swift_create_duplicate_container(self):
        metadata = {'is_public': False}
        container = self.containers.first()
        headers = api.swift._metadata_to_header(metadata=(metadata))
        swift_api = self.stub_swiftclient()
        # Check for existence, then create
        exc = self.exceptions.swift
        swift_api.head_container(container.name).AndRaise(exc)
        swift_api.put_container(container.name, headers=headers) \
            .AndReturn(container)
        self.mox.ReplayAll()
        # Verification handled by mox, no assertions needed.
        api.swift.swift_create_container(self.request,
                                         container.name,
                                         metadata=(metadata))

    def test_swift_create_container(self):
        metadata = {'is_public': True}
        container = self.containers.first()
        swift_api = self.stub_swiftclient()
        swift_api.head_container(container.name).AndReturn(container)
        self.mox.ReplayAll()
        # Verification handled by mox, no assertions needed.
        with self.assertRaises(exceptions.AlreadyExists):
            api.swift.swift_create_container(self.request,
                                             container.name,
                                             metadata=(metadata))

    def test_swift_update_container(self):
        metadata = {'is_public': True}
        container = self.containers.first()
        swift_api = self.stub_swiftclient()
        headers = api.swift._metadata_to_header(metadata=(metadata))
        swift_api.post_container(container.name, headers=headers)\
            .AndReturn(container)
        self.mox.ReplayAll()
        # Verification handled by mox, no assertions needed.
        api.swift.swift_update_container(self.request,
                                         container.name,
                                         metadata=(metadata))

    def test_swift_get_objects(self):
        container = self.containers.first()
        objects = self.objects.list()

        swift_api = self.stub_swiftclient()
        swift_api.get_container(container.name,
                                limit=1001,
                                marker=None,
                                prefix=None,
                                delimiter='/',
                                full_listing=True).AndReturn([{}, objects])
        self.mox.ReplayAll()

        (objs, more) = api.swift.swift_get_objects(self.request,
                                                   container.name)
        self.assertEqual(len(objects), len(objs))
        self.assertFalse(more)

    def test_swift_get_object_with_data_non_chunked(self):
        container = self.containers.first()
        object = self.objects.first()

        swift_api = self.stub_swiftclient()
        swift_api.get_object(
            container.name, object.name, resp_chunk_size=None
        ).AndReturn([object, object.data])

        self.mox.ReplayAll()

        obj = api.swift.swift_get_object(self.request, container.name,
                                         object.name, resp_chunk_size=None)
        self.assertEqual(object.name, obj.name)

    def test_swift_get_object_with_data_chunked(self):
        container = self.containers.first()
        object = self.objects.first()

        swift_api = self.stub_swiftclient()
        swift_api.get_object(
            container.name, object.name, resp_chunk_size=api.swift.CHUNK_SIZE
        ).AndReturn([object, object.data])

        self.mox.ReplayAll()

        obj = api.swift.swift_get_object(
            self.request, container.name, object.name)
        self.assertEqual(object.name, obj.name)

    def test_swift_get_object_without_data(self):
        container = self.containers.first()
        object = self.objects.first()

        swift_api = self.stub_swiftclient()
        swift_api.head_object(container.name, object.name) \
            .AndReturn(object)

        self.mox.ReplayAll()

        obj = api.swift.swift_get_object(self.request,
                                         container.name,
                                         object.name,
                                         with_data=False)
        self.assertEqual(object.name, obj.name)
        self.assertIsNone(obj.data)

    def test_swift_upload_object(self):
        container = self.containers.first()
        obj = self.objects.first()
        fake_name = 'fake_object.jpg'

        class FakeFile(object):
            def __init__(self):
                self.name = fake_name
                self.data = obj.data
                self.size = len(obj.data)

        headers = {'X-Object-Meta-Orig-Filename': fake_name}

        swift_api = self.stub_swiftclient()
        test_file = FakeFile()
        swift_api.put_object(container.name,
                             obj.name,
                             IsA(FakeFile),
                             content_length=test_file.size,
                             headers=headers)
        self.mox.ReplayAll()

        api.swift.swift_upload_object(self.request,
                                      container.name,
                                      obj.name,
                                      test_file)

    def test_swift_upload_object_without_file(self):
        container = self.containers.first()
        obj = self.objects.first()

        swift_api = self.stub_swiftclient()
        swift_api.put_object(container.name,
                             obj.name,
                             None,
                             content_length=0,
                             headers={})
        self.mox.ReplayAll()

        response = api.swift.swift_upload_object(self.request,
                                                 container.name,
                                                 obj.name,
                                                 None)
        self.assertEqual(0, response['bytes'])

    def test_swift_object_exists(self):
        container = self.containers.first()
        obj = self.objects.first()

        swift_api = self.stub_swiftclient()
        swift_api.head_object(container.name, obj.name).AndReturn(container)

        exc = self.exceptions.swift
        swift_api.head_object(container.name, obj.name).AndRaise(exc)
        self.mox.ReplayAll()

        args = self.request, container.name, obj.name
        self.assertTrue(api.swift.swift_object_exists(*args))
        # Again, for a "non-existent" object
        self.assertFalse(api.swift.swift_object_exists(*args))
