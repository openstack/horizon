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

import mock

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


@mock.patch('swiftclient.client.Connection')
class SwiftApiTests(test.APIMockTestCase):
    def test_swift_get_containers(self, mock_swiftclient):
        containers = self.containers.list()
        cont_data = [c._apidict for c in containers]
        swift_api = mock_swiftclient.return_value
        swift_api.get_account.return_value = [{}, cont_data]

        (conts, more) = api.swift.swift_get_containers(self.request)

        self.assertEqual(len(containers), len(conts))
        self.assertFalse(more)
        swift_api.get_account.assert_called_once_with(
            limit=1001, marker=None, prefix=None, full_listing=True)

    def test_swift_get_container_with_data(self, mock_swiftclient):
        container = self.containers.first()
        objects = self.objects.list()
        swift_api = mock_swiftclient.return_value
        swift_api.get_object.return_value = (container, objects)

        cont = api.swift.swift_get_container(self.request, container.name)

        self.assertEqual(container.name, cont.name)
        self.assertEqual(len(objects), len(cont.data))
        swift_api.get_object.assert_called_once_with(container.name, "")

    def test_swift_get_container_without_data(self, mock_swiftclient):
        container = self.containers.first()
        swift_api = mock_swiftclient.return_value
        swift_api.head_container.return_value = container

        cont = api.swift.swift_get_container(self.request,
                                             container.name,
                                             with_data=False)

        self.assertEqual(cont.name, container.name)
        self.assertIsNone(cont.data)
        swift_api.head_container.assert_called_once_with(container.name)

    def test_swift_create_duplicate_container(self, mock_swiftclient):
        metadata = {'is_public': False}
        container = self.containers.first()
        headers = api.swift._metadata_to_header(metadata=(metadata))
        swift_api = mock_swiftclient.return_value
        # Check for existence, then create
        swift_api.head_container.side_effect = self.exceptions.swift
        swift_api.put_container.return_value = container

        api.swift.swift_create_container(self.request,
                                         container.name,
                                         metadata=(metadata))

        swift_api.head_container.assert_called_once_with(container.name)
        swift_api.put_container.assert_called_once_with(container.name,
                                                        headers=headers)

    def test_swift_create_container(self, mock_swiftclient):
        metadata = {'is_public': True}
        container = self.containers.first()
        swift_api = mock_swiftclient.return_value
        swift_api.head_container.return_value = container

        with self.assertRaises(exceptions.AlreadyExists):
            api.swift.swift_create_container(self.request,
                                             container.name,
                                             metadata=(metadata))

        swift_api.head_container.assert_called_once_with(container.name)

    def test_swift_update_container(self, mock_swiftclient):
        metadata = {'is_public': True}
        container = self.containers.first()
        swift_api = mock_swiftclient.return_value
        headers = api.swift._metadata_to_header(metadata=(metadata))
        swift_api.post_container.return_value = container

        api.swift.swift_update_container(self.request,
                                         container.name,
                                         metadata=(metadata))

        swift_api.post_container.assert_called_once_with(container.name,
                                                         headers=headers)

    def test_swift_get_objects(self, mock_swiftclient):
        container = self.containers.first()
        objects = self.objects.list()

        swift_api = mock_swiftclient.return_value
        swift_api.get_container.return_value = [{}, objects]

        (objs, more) = api.swift.swift_get_objects(self.request,
                                                   container.name)

        self.assertEqual(len(objects), len(objs))
        self.assertFalse(more)
        swift_api.get_container.assert_called_once_with(
            container.name,
            limit=1001,
            marker=None,
            prefix=None,
            delimiter='/',
            full_listing=True)

    def test_swift_get_object_with_data_non_chunked(self, mock_swiftclient):
        container = self.containers.first()
        object = self.objects.first()

        swift_api = mock_swiftclient.return_value
        swift_api.get_object.return_value = [object, object.data]

        obj = api.swift.swift_get_object(self.request, container.name,
                                         object.name, resp_chunk_size=None)

        self.assertEqual(object.name, obj.name)
        swift_api.get_object.assert_called_once_with(
            container.name, object.name, resp_chunk_size=None)

    def test_swift_get_object_with_data_chunked(self, mock_swiftclient):
        container = self.containers.first()
        object = self.objects.first()

        swift_api = mock_swiftclient.return_value
        swift_api.get_object.return_value = [object, object.data]

        obj = api.swift.swift_get_object(
            self.request, container.name, object.name)

        self.assertEqual(object.name, obj.name)
        swift_api.get_object.assert_called_once_with(
            container.name, object.name, resp_chunk_size=api.swift.CHUNK_SIZE)

    def test_swift_get_object_without_data(self, mock_swiftclient):
        container = self.containers.first()
        object = self.objects.first()

        swift_api = mock_swiftclient.return_value
        swift_api.head_object.return_value = object

        obj = api.swift.swift_get_object(self.request,
                                         container.name,
                                         object.name,
                                         with_data=False)

        self.assertEqual(object.name, obj.name)
        self.assertIsNone(obj.data)
        swift_api.head_object.assert_called_once_with(container.name,
                                                      object.name)

    def test_swift_create_pseudo_folder(self, mock_swiftclient):
        container = self.containers.first()
        folder = self.folder.first()
        swift_api = mock_swiftclient.return_value
        exc = self.exceptions.swift
        swift_api.head_object.side_effect = exc
        swift_api.put_object.return_value = folder

        api.swift.swift_create_pseudo_folder(self.request,
                                             container.name,
                                             folder.name)

        swift_api.head_object.assert_called_once_with(container.name,
                                                      folder.name)
        swift_api.put_object.assert_called_once_with(container.name,
                                                     folder.name,
                                                     None,
                                                     headers={})

    def test_swift_create_duplicate_folder(self, mock_swiftclient):
        container = self.containers.first()
        folder = self.folder.first()
        swift_api = mock_swiftclient.return_value
        swift_api.head_object.return_value = folder

        with self.assertRaises(exceptions.AlreadyExists):
            api.swift.swift_create_pseudo_folder(self.request,
                                                 container.name,
                                                 folder.name)

        swift_api.head_object.assert_called_once_with(container.name,
                                                      folder.name)

    def test_swift_upload_object(self, mock_swiftclient):
        container = self.containers.first()
        obj = self.objects.first()
        fake_name = 'fake_object.jpg'

        class FakeFile(object):
            def __init__(self):
                self.name = fake_name
                self.data = obj.data
                self.size = len(obj.data)

        headers = {'X-Object-Meta-Orig-Filename': fake_name}

        swift_api = mock_swiftclient.return_value
        test_file = FakeFile()
        swift_api.put_object.return_value = None

        api.swift.swift_upload_object(self.request,
                                      container.name,
                                      obj.name,
                                      test_file)

        swift_api.put_object.assert_called_once_with(
            container.name,
            obj.name,
            test.IsA(FakeFile),
            content_length=test_file.size,
            headers=headers)

    def test_swift_upload_object_without_file(self, mock_swiftclient):
        container = self.containers.first()
        obj = self.objects.first()

        swift_api = mock_swiftclient.return_value
        swift_api.put_object.return_value = None

        response = api.swift.swift_upload_object(self.request,
                                                 container.name,
                                                 obj.name,
                                                 None)

        self.assertEqual(0, response['bytes'])
        swift_api.put_object.assert_called_once_with(
            container.name,
            obj.name,
            None,
            content_length=0,
            headers={})

    def test_swift_object_exists(self, mock_swiftclient):
        container = self.containers.first()
        obj = self.objects.first()

        swift_api = mock_swiftclient.return_value
        swift_api.head_object.side_effect = [container, self.exceptions.swift]

        args = self.request, container.name, obj.name

        self.assertTrue(api.swift.swift_object_exists(*args))
        # Again, for a "non-existent" object
        self.assertFalse(api.swift.swift_object_exists(*args))

        self.assertEqual(2, swift_api.head_object.call_count)
        swift_api.head_object.assert_has_calls([
            mock.call(container.name, obj.name),
            mock.call(container.name, obj.name),
        ])
