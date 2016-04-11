# Copyright 2015, Rackspace, US, Inc.
# Copyright 2015, Hewlett-Packard Development Company, L.P.
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

from openstack_dashboard.api.rest import glance
from openstack_dashboard.test import helpers as test


class ImagesRestTestCase(test.TestCase):
    #
    # Version
    #
    @mock.patch.object(glance.api, 'glance')
    def test_version_get(self, gc):
        request = self.mock_rest_request()
        gc.get_version.return_value = '2.0'
        response = glance.Version().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"version": "2.0"})
        gc.get_version.assert_called_once_with()

    @mock.patch.object(glance.api, 'glance')
    def test_image_get_single(self, gc):
        request = self.mock_rest_request()
        gc.image_get.return_value.to_dict.return_value = {'name': '1'}

        response = glance.Image().get(request, "1")
        self.assertStatusCode(response, 200)
        gc.image_get.assert_called_once_with(request, "1")

    @mock.patch.object(glance.api, 'glance')
    def test_image_get_metadata(self, gc):
        request = self.mock_rest_request()
        gc.image_get.return_value.properties = {'a': '1', 'b': '2'}

        response = glance.ImageProperties().get(request, "1")
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"a": "1", "b": "2"})
        gc.image_get.assert_called_once_with(request, "1")

    @mock.patch.object(glance.api, 'glance')
    def test_image_edit_metadata(self, gc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )

        response = glance.ImageProperties().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        gc.image_update_properties.assert_called_once_with(
            request, '1', ['c', 'd'], a='1', b='2'
        )

    @mock.patch.object(glance.api, 'glance')
    def test_image_delete(self, gc):
        request = self.mock_rest_request()
        glance.Image().delete(request, "1")
        gc.image_delete.assert_called_once_with(request, "1")

    @mock.patch.object(glance.api, 'glance')
    def test_image_edit(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "container_format": "aki",
            "visibility": "public", "protected": false,
            "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'is_public': True,
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'properties': {
                        'description': 'description',
                        'architecture': 'testArch',
                        'ramdisk_id': 10,
                        'kernel_id': 'kernel',
                    },
                    'purge_props': False}

        response = glance.Image().patch(request, "1")
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        gc.image_update.assert_called_once_with(request, '1', **metadata)

    @mock.patch.object(glance.api, 'glance')
    def test_image_get_list_detailed(self, gc):
        kwargs = {
            'sort_dir': 'desc',
            'sort_key': 'namespace',
            'marker': 1,
            'paginate': False,
        }
        filters = {'name': 'fedora'}
        request = self.mock_rest_request(
            **{'GET': dict(kwargs, **filters)})
        gc.image_list_detailed.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': 'fedora'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'cirros'}})
        ], False, False)

        response = glance.Images().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "fedora"}, {"name": "cirros"}],
                          "has_more_data": False, "has_prev_data": False})
        gc.image_list_detailed.assert_called_once_with(request,
                                                       filters=filters,
                                                       **kwargs)

    @mock.patch.object(glance.api, 'glance')
    def test_image_create_basic(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "public", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        new = gc.image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'is_public': True,
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'location': 'test.com',
                    'properties': {
                        'description': 'description',
                        'architecture': 'testArch',
                        'ramdisk_id': 10,
                        'kernel_id': 'kernel',
                    }}

        response = glance.Images().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        gc.image_create.assert_called_once_with(request, **metadata)

    @mock.patch.object(glance.api, 'glance')
    def test_image_create_shared(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "shared", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        new = gc.image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'is_public': False,
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'location': 'test.com',
                    'properties': {
                        'description': 'description',
                        'architecture': 'testArch',
                        'ramdisk_id': 10,
                        'kernel_id': 'kernel',
                    }}

        response = glance.Images().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        gc.image_create.assert_called_once_with(request, **metadata)

    @mock.patch.object(glance.api, 'glance')
    def test_image_create_private(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "private", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        new = gc.image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'is_public': False,
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'location': 'test.com',
                    'properties': {
                        'description': 'description',
                        'architecture': 'testArch',
                        'ramdisk_id': 10,
                        'kernel_id': 'kernel',
                    }}

        response = glance.Images().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        gc.image_create.assert_called_once_with(request, **metadata)

    @mock.patch.object(glance.api, 'glance')
    def test_image_create_bad_visibility(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "verybad", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')

        response = glance.Images().post(request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content.decode('utf-8'),
                         '"invalid visibility option: verybad"')

    @mock.patch.object(glance.api, 'glance')
    def test_image_create_required(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "raw", "import_data": true,
            "container_format": "docker",
            "visibility": "public", "protected": false,
            "source_type": "url", "image_url": "test.com" }''')
        new = gc.image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'raw',
                    'container_format': 'docker',
                    'copy_from': 'test.com',
                    'is_public': True,
                    'protected': False,
                    'min_disk': 0,
                    'min_ram': 0,
                    'properties': {}
                    }
        response = glance.Images().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        gc.image_create.assert_called_once_with(request, **metadata)

    @mock.patch.object(glance.api, 'glance')
    def test_image_create_additional_props(self, gc):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "raw", "import_data": true,
            "container_format": "docker",
            "visibility": "public", "protected": false,
            "arbitrary": "property", "another": "prop",
            "source_type": "url", "image_url": "test.com" }''')
        new = gc.image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'raw',
                    'container_format': 'docker',
                    'copy_from': 'test.com',
                    'is_public': True,
                    'protected': False,
                    'min_disk': 0,
                    'min_ram': 0,
                    'properties': {'arbitrary': 'property', 'another': 'prop'}
                    }
        response = glance.Images().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        gc.image_create.assert_called_once_with(request, **metadata)

    @mock.patch.object(glance.api, 'glance')
    def test_namespace_get_list(self, gc):
        request = self.mock_rest_request(**{'GET': {}})
        gc.metadefs_namespace_full_list.return_value = (
            [{'namespace': '1'}, {'namespace': '2'}], False, False
        )

        response = glance.MetadefsNamespaces().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"namespace": "1"}, {"namespace": "2"}],
                          "has_more_data": False, "has_prev_data": False})
        gc.metadefs_namespace_full_list.assert_called_once_with(
            request, filters={}
        )

    @mock.patch.object(glance.api, 'glance')
    def test_namespace_get_list_kwargs_and_filters(self, gc):
        kwargs = {
            'sort_dir': 'desc',
            'sort_key': 'namespace',
            'marker': 1,
            'paginate': False,
        }
        filters = {'resource_types': 'type'}
        request = self.mock_rest_request(
            **{'GET': dict(kwargs, **filters)})
        gc.metadefs_namespace_full_list.return_value = (
            [{'namespace': '1'}, {'namespace': '2'}], False, False
        )

        response = glance.MetadefsNamespaces().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"namespace": "1"}, {"namespace": "2"}],
                          "has_more_data": False, "has_prev_data": False})
        gc.metadefs_namespace_full_list.assert_called_once_with(
            request, filters=filters, **kwargs
        )

    @mock.patch.object(glance.api, 'glance')
    def test_resource_types_get_list(self, gc):
        request = self.mock_rest_request(**{'GET': {}})
        gc.metadefs_resource_types_list.return_value = ([
            {"created_at": "2015-08-21T16:49:43Z",
             "name": "OS::Glance::Image",
             "updated_at": "2015-08-21T16:49:43Z"},
            {"created_at": "2015-08-21T16:49:43Z",
             "name": "OS::Cinder::Volume",
             "updated_at": "2015-08-21T16:49:43Z"}
        ])

        response = glance.MetadefsResourceTypesList().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"items": [
            {"created_at": "2015-08-21T16:49:43Z",
             "name": "OS::Glance::Image",
             "updated_at": "2015-08-21T16:49:43Z"},
            {"created_at": "2015-08-21T16:49:43Z",
             "name": "OS::Cinder::Volume",
             "updated_at": "2015-08-21T16:49:43Z"}
        ]})

        gc.metadefs_resource_types_list.assert_called_once_with(request)
