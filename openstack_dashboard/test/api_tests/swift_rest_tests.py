# Copyright 2016, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock

from openstack_dashboard.api.rest import swift
from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_data import swift_data
from openstack_dashboard.test.test_data.utils import TestData  # noqa


TEST = TestData(swift_data.data)


class SwiftRestTestCase(test.TestCase):
    def setUp(self):
        super(SwiftRestTestCase, self).setUp()
        self._containers = TEST.containers.list()
        self._objects = TEST.objects.list()
        self._folder = TEST.folder.list()
        self._subfolder = TEST.subfolder.list()

    #
    # Version
    #
    @mock.patch.object(swift.api, 'swift')
    def test_version_get(self, nc):
        request = self.mock_rest_request()
        nc.swift_get_capabilities.return_value = {'swift': {'version': '1.0'}}
        response = swift.Info().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {
            'info': {'swift': {'version': '1.0'}}
        })
        nc.swift_get_capabilities.assert_called_once_with(request)

    #
    # Containers
    #
    @mock.patch.object(swift.api, 'swift')
    def test_containers_get(self, nc):
        request = self.mock_rest_request()
        nc.swift_get_containers.return_value = (self._containers, False)
        response = swift.Containers().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json['items'][0]['name'],
                         u'container one%\u6346')
        self.assertEqual(response.json['has_more'], False)
        nc.swift_get_containers.assert_called_once_with(request)

    #
    # Container
    #
    @mock.patch.object(swift.api, 'swift')
    def test_container_get(self, nc):
        request = self.mock_rest_request()
        nc.swift_get_container.return_value = self._containers[0]
        response = swift.Container().get(request, u'container one%\u6346')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, self._containers[0].to_dict())
        nc.swift_get_container.assert_called_once_with(request,
                                                       u'container one%\u6346')

    @mock.patch.object(swift.api, 'swift')
    def test_container_create(self, nc):
        request = self.mock_rest_request(body='{}')
        response = swift.Container().post(request, 'spam')
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         u'/api/swift/containers/spam')
        nc.swift_create_container.assert_called_once_with(
            request, 'spam', metadata={}
        )

    @mock.patch.object(swift.api, 'swift')
    def test_container_create_is_public(self, nc):
        request = self.mock_rest_request(body='{"is_public": false}')
        response = swift.Container().post(request, 'spam')
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         u'/api/swift/containers/spam')
        nc.swift_create_container.assert_called_once_with(
            request, 'spam', metadata={'is_public': False}
        )

    @mock.patch.object(swift.api, 'swift')
    def test_container_delete(self, nc):
        request = self.mock_rest_request()
        response = swift.Container().delete(request, u'container one%\u6346')
        self.assertStatusCode(response, 204)
        nc.swift_delete_container.assert_called_once_with(
            request, u'container one%\u6346'
        )

    @mock.patch.object(swift.api, 'swift')
    def test_container_update(self, nc):
        request = self.mock_rest_request(body='{"is_public": false}')
        response = swift.Container().put(request, 'spam')
        self.assertStatusCode(response, 204)
        nc.swift_update_container.assert_called_once_with(
            request, 'spam', metadata={'is_public': False}
        )

    #
    # Objects
    #
    @mock.patch.object(swift.api, 'swift')
    def test_objects_get(self, nc):
        request = self.mock_rest_request(GET={})
        nc.swift_get_objects.return_value = (self._objects, False)
        response = swift.Objects().get(request, u'container one%\u6346')
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.json['items']), 4)
        self.assertEqual(response.json['items'][3]['path'],
                         u'test folder%\u6346/test.txt')
        self.assertEqual(response.json['items'][3]['name'], 'test.txt')
        self.assertEqual(response.json['items'][3]['is_object'], True)
        self.assertEqual(response.json['items'][3]['is_subdir'], False)
        nc.swift_get_objects.assert_called_once_with(request,
                                                     u'container one%\u6346',
                                                     prefix=None)

    @mock.patch.object(swift.api, 'swift')
    def test_container_get_path_folder(self, nc):
        request = self.mock_rest_request(GET={'path': u'test folder%\u6346/'})
        nc.swift_get_objects.return_value = (self._subfolder, False)
        response = swift.Objects().get(request, u'container one%\u6346')
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.json['items']), 1)
        self.assertEqual(response.json['items'][0]['is_object'], True)
        self.assertEqual(response.json['items'][0]['is_subdir'], False)
        nc.swift_get_objects.assert_called_once_with(
            request,
            u'container one%\u6346', prefix=u'test folder%\u6346/'
        )

    #
    # Object
    #
    @mock.patch.object(swift.api, 'swift')
    def test_object_get(self, nc):
        request = self.mock_rest_request()
        nc.swift_get_object.return_value = self._objects[0]
        response = swift.ObjectMetadata().get(request, 'container', 'test.txt')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, self._objects[0].to_dict())
        nc.swift_get_object.assert_called_once_with(
            request,
            container_name='container',
            object_name='test.txt',
            with_data=False
        )

    @mock.patch.object(swift.api, 'swift')
    def test_object_delete(self, nc):
        request = self.mock_rest_request()
        nc.swift_delete_object.return_value = True
        response = swift.Object().delete(request, 'container', 'test.txt')
        self.assertStatusCode(response, 204)
        nc.swift_delete_object.assert_called_once_with(request,
                                                       'container',
                                                       'test.txt')

    @mock.patch.object(swift, 'UploadObjectForm')
    @mock.patch.object(swift.api, 'swift')
    def test_object_create(self, nc, uf):
        uf.return_value.is_valid.return_value = True
        # note file name not used, path name is
        file = mock.Mock(name=u'NOT object%\u6346')
        uf.return_value.clean.return_value = {'file': file}
        request = self.mock_rest_request()
        real_name = u'test_object%\u6346'
        nc.swift_upload_object.return_value = self._objects[0]
        response = swift.Object().post(request, 'spam', real_name)
        self.assertStatusCode(response, 201)
        self.assertEqual(
            response['location'],
            '=?utf-8?q?/api/swift/containers/spam/object/test_object'
            '=25=E6=8D=86?='
        )
        self.assertTrue(nc.swift_upload_object.called)
        call = nc.swift_upload_object.call_args[0]
        self.assertEqual(call[0:3], (request, 'spam', u'test_object%\u6346'))
        self.assertEqual(call[3], file)

    @mock.patch.object(swift, 'UploadObjectForm')
    @mock.patch.object(swift.api, 'swift')
    def test_folder_create(self, nc, uf):
        uf.return_value.is_valid.return_value = True
        uf.return_value.clean.return_value = {}
        request = self.mock_rest_request()
        nc.swift_create_pseudo_folder.return_value = self._folder[0]
        response = swift.Object().post(request, 'spam', u'test_folder%\u6346/')
        self.assertStatusCode(response, 201)
        self.assertEqual(
            response['location'],
            '=?utf-8?q?/api/swift/containers/spam/object/test_folder'
            '=25=E6=8D=86/?='
        )
        self.assertTrue(nc.swift_create_pseudo_folder.called)
        call = nc.swift_create_pseudo_folder.call_args[0]
        self.assertEqual(call[0:3], (request, 'spam', u'test_folder%\u6346/'))

    @mock.patch.object(swift.api, 'swift')
    def test_object_copy(self, nc):
        request = self.mock_rest_request(
            body='{"dest_container":"eggs", "dest_name":"bacon"}',
        )
        nc.swift_copy_object.return_value = self._objects[0]
        response = swift.ObjectCopy().post(request,
                                           'spam',
                                           u'test object%\u6346')
        self.assertStatusCode(response, 201)
        self.assertEqual(
            response['location'],
            '=?utf-8?q?/api/swift/containers/eggs/object/test_object'
            '=25=E6=8D=86?='
        )

        self.assertTrue(nc.swift_copy_object.called)
        call = nc.swift_copy_object.call_args[0]
        self.assertEqual(call[0:5], (request,
                                     'spam',
                                     u'test object%\u6346',
                                     'eggs',
                                     'bacon'))
        self.assertStatusCode(response, 201)
