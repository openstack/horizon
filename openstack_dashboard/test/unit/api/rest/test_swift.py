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

from openstack_dashboard import api
from openstack_dashboard.api.rest import swift
from openstack_dashboard.test import helpers as test


class SwiftRestTestCase(test.TestCase):

    #
    # Version
    #
    @test.create_mocks({api.swift: ['swift_get_capabilities']})
    def test_version_get(self):
        request = self.mock_rest_request()
        self.mock_swift_get_capabilities.return_value = {'swift':
                                                         {'version': '1.0'}}
        response = swift.Info().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({'info': {'swift': {'version': '1.0'}}},
                         response.json)
        self.mock_swift_get_capabilities.assert_called_once_with(request)

    #
    # Containers
    #
    @test.create_mocks({api.swift: ['swift_get_containers']})
    def test_containers_get(self):
        request = self.mock_rest_request(GET={})
        self.mock_swift_get_containers.return_value = (self.containers.list(),
                                                       False)
        response = swift.Containers().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(u'container one%\u6346',
                         response.json['items'][0]['name'])
        self.assertFalse(response.json['has_more'])
        self.mock_swift_get_containers.assert_called_once_with(request)

    @test.create_mocks({api.swift: ['swift_get_container']})
    def test_container_get(self):
        request = self.mock_rest_request()
        self.mock_swift_get_container.return_value = self.containers.first()
        response = swift.Container().get(request, u'container one%\u6346')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, self.containers.first().to_dict())
        self.mock_swift_get_container.assert_called_once_with(
            request, u'container one%\u6346')

    @test.create_mocks({api.swift: ['swift_create_container']})
    def test_container_create(self):
        self.mock_swift_create_container.return_value = self.containers.first()
        request = self.mock_rest_request(body='{}')
        response = swift.Container().post(request, 'spam')
        self.assertStatusCode(response, 201)
        self.assertEqual(u'/api/swift/containers/spam',
                         response['location'])
        self.mock_swift_create_container.assert_called_once_with(
            request, 'spam', metadata={}
        )

    @test.create_mocks({api.swift: ['swift_create_container']})
    def test_container_create_is_public(self):
        self.mock_swift_create_container.return_value = self.containers.first()
        request = self.mock_rest_request(body='{"is_public": false}')
        response = swift.Container().post(request, 'spam')
        self.assertStatusCode(response, 201)
        self.assertEqual(u'/api/swift/containers/spam',
                         response['location'])
        self.mock_swift_create_container.assert_called_once_with(
            request, 'spam', metadata={'is_public': False}
        )

    @test.create_mocks({api.swift: ['swift_delete_container']})
    def test_container_delete(self):
        self.mock_swift_delete_container.return_value = True
        request = self.mock_rest_request()
        response = swift.Container().delete(request, u'container one%\u6346')
        self.assertStatusCode(response, 204)
        self.mock_swift_delete_container.assert_called_once_with(
            request, u'container one%\u6346'
        )

    @test.create_mocks({api.swift: ['swift_update_container']})
    def test_container_update(self):
        # is_public of the second container is True
        container = self.containers.list()[1]
        self.mock_swift_update_container.return_value = container
        request = self.mock_rest_request(body='{"is_public": false}')
        response = swift.Container().put(request, container.name)
        self.assertStatusCode(response, 204)
        self.mock_swift_update_container.assert_called_once_with(
            request, container.name, metadata={'is_public': False}
        )

    #
    # Objects
    #
    @test.create_mocks({api.swift: ['swift_get_objects']})
    def test_objects_get(self):
        request = self.mock_rest_request(GET={})
        self.mock_swift_get_objects.return_value = (
            self.objects.list() + self.folder.list(), False
        )
        response = swift.Objects().get(request, u'container one%\u6346')
        self.assertStatusCode(response, 200)
        self.assertEqual(5, len(response.json['items']))
        self.assertEqual(u'test folder%\u6346/test.txt',
                         response.json['items'][3]['path'])
        self.assertEqual('test.txt', response.json['items'][3]['name'])
        self.assertTrue(response.json['items'][3]['is_object'])
        self.assertFalse(response.json['items'][3]['is_subdir'])
        self.assertEqual(u'test folder%\u6346/test.txt',
                         response.json['items'][3]['path'])

        self.assertEqual(u'test folder%\u6346/',
                         response.json['items'][4]['path'])
        self.assertEqual(u'test folder%\u6346',
                         response.json['items'][4]['name'])
        self.assertFalse(response.json['items'][4]['is_object'])
        self.assertTrue(response.json['items'][4]['is_subdir'])

        self.mock_swift_get_objects.assert_called_once_with(
            request,
            u'container one%\u6346',
            prefix=None)

    @test.create_mocks({api.swift: ['swift_get_objects']})
    def test_container_get_path_folder(self):
        request = self.mock_rest_request(GET={'path': u'test folder%\u6346/'})
        self.mock_swift_get_objects.return_value = (self.subfolder.list(),
                                                    False)
        response = swift.Objects().get(request, u'container one%\u6346')
        self.assertStatusCode(response, 200)
        self.assertEqual(1, len(response.json['items']))
        self.assertTrue(response.json['items'][0]['is_object'])
        self.assertFalse(response.json['items'][0]['is_subdir'])
        self.mock_swift_get_objects.assert_called_once_with(
            request,
            u'container one%\u6346', prefix=u'test folder%\u6346/'
        )

    @test.create_mocks({api.swift: ['swift_get_object']})
    def test_object_get(self):
        request = self.mock_rest_request()
        self.mock_swift_get_object.return_value = self.objects.first()
        response = swift.ObjectMetadata().get(request, 'container', 'test.txt')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, self.objects.first().to_dict())
        self.mock_swift_get_object.assert_called_once_with(
            request,
            container_name='container',
            object_name='test.txt',
            with_data=False
        )

    @test.create_mocks({api.swift: ['swift_delete_object']})
    def test_object_delete(self):
        request = self.mock_rest_request()
        self.mock_swift_delete_object.return_value = True
        response = swift.Object().delete(request, 'container', 'test.txt')
        self.assertStatusCode(response, 204)
        self.mock_swift_delete_object.assert_called_once_with(request,
                                                              'container',
                                                              'test.txt')

    @test.create_mocks({api.swift: ['swift_upload_object'],
                        swift: ['UploadObjectForm']})
    def test_object_create(self):
        form_obj = self.mock_UploadObjectForm.return_value
        form_obj.is_valid.return_value = True
        # note file name not used, path name is
        _file = mock.Mock(name=u'NOT object%\u6346')
        form_obj.clean.return_value = {'file': _file}
        request = self.mock_rest_request()
        real_name = u'test_object%\u6346'
        self.mock_swift_upload_object.return_value = self.objects.first()
        response = swift.Object().post(request, 'spam', real_name)
        self.assertStatusCode(response, 201)
        self.assertEqual(
            '=?utf-8?q?/api/swift/containers/spam/object/test_object'
            '=25=E6=8D=86?=',
            response['location']
        )
        self.mock_swift_upload_object.assert_called_once_with(
            request, 'spam', u'test_object%\u6346', _file)

    @test.create_mocks({api.swift: ['swift_create_pseudo_folder'],
                        swift: ['UploadObjectForm']})
    def test_folder_create(self):
        form_obj = self.mock_UploadObjectForm.return_value
        form_obj.is_valid.return_value = True
        form_obj.clean.return_value = {}
        request = self.mock_rest_request()
        self.mock_swift_create_pseudo_folder.return_value = \
            self.folder_alt.first()
        response = swift.Object().post(request, 'spam', u'test_folder%\u6346/')
        self.assertStatusCode(response, 201)
        self.assertEqual(
            response['location'],
            '=?utf-8?q?/api/swift/containers/spam/object/test_folder'
            '=25=E6=8D=86/?='
        )
        self.mock_swift_create_pseudo_folder.assert_called_once_with(
            request, 'spam', u'test_folder%\u6346/')

    @test.create_mocks({api.swift: ['swift_copy_object']})
    def test_object_copy(self):
        request = self.mock_rest_request(
            body='{"dest_container":"eggs", "dest_name":"bacon"}',
        )
        self.mock_swift_copy_object.return_value = self.objects.first()
        response = swift.ObjectCopy().post(request,
                                           'spam',
                                           u'test object%\u6346')
        self.assertStatusCode(response, 201)
        self.assertEqual(
            response['location'],
            '=?utf-8?q?/api/swift/containers/eggs/object/test_object'
            '=25=E6=8D=86?='
        )

        self.mock_swift_copy_object.assert_called_once_with(
            request,
            'spam',
            u'test object%\u6346',
            'eggs',
            'bacon')
        self.assertStatusCode(response, 201)
