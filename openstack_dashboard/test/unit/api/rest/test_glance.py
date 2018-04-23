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

from openstack_dashboard import api
from openstack_dashboard.api.rest import glance
from openstack_dashboard.test import helpers as test


class ImagesRestTestCase(test.ResetImageAPIVersionMixin, test.TestCase):

    def setUp(self):
        super(ImagesRestTestCase, self).setUp()
        api.glance.VERSIONS.clear_active_cache()

    #
    # Version
    #
    @test.create_mocks({api.glance: ['get_version']})
    def test_version_get(self):
        request = self.mock_rest_request()
        self.mock_get_version.return_value = '2.0'
        response = glance.Version().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"version": "2.0"})
        self.mock_get_version.assert_called_once_with()

    @test.create_mocks({api.glance: ['image_get']})
    def test_image_get_single(self):
        request = self.mock_rest_request()
        self.mock_image_get.return_value.to_dict.return_value = {'name': '1'}

        response = glance.Image().get(request, "1")
        self.assertStatusCode(response, 200)
        self.mock_image_get.assert_called_once_with(request, "1")

    @test.create_mocks({api.glance: ['image_get']})
    def test_image_get_metadata(self):
        request = self.mock_rest_request()
        self.mock_image_get.return_value.properties = {'a': '1', 'b': '2'}

        response = glance.ImageProperties().get(request, "1")
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"a": "1", "b": "2"})
        self.mock_image_get.assert_called_once_with(request, "1")

    @test.create_mocks({api.glance: ['image_update_properties']})
    def test_image_edit_metadata(self):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )
        self.mock_image_update_properties.return_value = self.images.first()

        response = glance.ImageProperties().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_image_update_properties.assert_called_once_with(
            request, '1', ['c', 'd'], a='1', b='2'
        )

    @test.create_mocks({api.glance: ['image_delete']})
    def test_image_delete(self):
        request = self.mock_rest_request()
        self.mock_image_delete.return_value = None
        glance.Image().delete(request, "1")
        self.mock_image_delete.assert_called_once_with(request, "1")

    @test.create_mocks({api.glance: ['image_update', 'VERSIONS']})
    def test_image_edit_v1(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "container_format": "aki",
            "visibility": "public", "protected": false,
            "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 1
        self.mock_image_update.return_value = self.images.first()

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'is_public': True,
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'properties': {'description': 'description',
                                   'architecture': 'testArch',
                                   'ramdisk_id': 10,
                                   'kernel_id': 'kernel'}
                    }

        response = glance.Image().patch(request, "1")
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        self.mock_image_update.assert_called_once_with(request, '1',
                                                       **metadata)

    @test.create_mocks({api.glance: ['image_update', 'VERSIONS']})
    def test_image_edit_v2(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "container_format": "aki",
            "visibility": "public", "protected": false,
            "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 2
        self.mock_image_update.return_value = self.images.first()

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'visibility': 'public',
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'description': 'description',
                    'architecture': 'testArch',
                    'ramdisk_id': 10,
                    'kernel_id': 'kernel'
                    }

        response = glance.Image().patch(request, "1")
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        self.mock_image_update.assert_called_once_with(request, '1',
                                                       **metadata)

    @test.create_mocks({api.glance: ['image_list_detailed']})
    def test_image_get_list_detailed(self):
        kwargs = {
            'sort_dir': 'desc',
            'sort_key': 'namespace',
            'marker': 1,
            'paginate': False,
        }
        filters = {'name': 'fedora'}
        request = self.mock_rest_request(
            **{'GET': dict(kwargs, **filters)})
        self.mock_image_list_detailed.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': 'fedora'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'cirros'}})
        ], False, False)

        response = glance.Images().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "fedora"}, {"name": "cirros"}],
                          "has_more_data": False, "has_prev_data": False})
        self.mock_image_list_detailed.assert_called_once_with(request,
                                                              filters=filters,
                                                              **kwargs)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v1_basic(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "public", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        new = self.mock_image_create.return_value
        self.mock_VERSIONS.active = 1
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

        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v2_basic(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "public", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 2
        new = self.mock_image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'visibility': 'public',
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'location': 'test.com',
                    'description': 'description',
                    'architecture': 'testArch',
                    'ramdisk_id': 10,
                    'kernel_id': 'kernel',
                    }

        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v1_shared(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "shared", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 1
        new = self.mock_image_create.return_value
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

        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v2_shared(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "shared", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 2
        new = self.mock_image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'visibility': 'shared',
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'location': 'test.com',
                    'description': 'description',
                    'architecture': 'testArch',
                    'ramdisk_id': 10,
                    'kernel_id': 'kernel',
                    }

        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v1_private(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "private", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 1
        new = self.mock_image_create.return_value
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

        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v2_private(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "private", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 2
        new = self.mock_image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'aki',
                    'container_format': 'aki',
                    'visibility': 'private',
                    'protected': False,
                    'min_disk': 10,
                    'min_ram': 5,
                    'location': 'test.com',
                    'description': 'description',
                    'architecture': 'testArch',
                    'ramdisk_id': 10,
                    'kernel_id': 'kernel',
                    }

        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"name": "testimage"}')
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['VERSIONS']})
    def test_image_create_v1_bad_visibility(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "verybad", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 1

        response = glance.Images().put(request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content.decode('utf-8'),
                         '"invalid visibility option: verybad"')

    @test.create_mocks({api.glance: ['VERSIONS']})
    def test_image_create_v2_bad_visibility(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "aki", "import_data": false,
            "visibility": "verybad", "container_format": "aki",
            "protected": false, "image_url": "test.com",
            "source_type": "url", "architecture": "testArch",
            "description": "description", "kernel": "kernel",
            "min_disk": 10, "min_ram": 5, "ramdisk": 10 }
        ''')
        self.mock_VERSIONS.active = 2

        response = glance.Images().put(request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content.decode('utf-8'),
                         '"invalid visibility option: verybad"')

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v1_required(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "raw", "import_data": true,
            "container_format": "docker",
            "visibility": "public", "protected": false,
            "source_type": "url", "image_url": "test.com" }''')
        self.mock_VERSIONS.active = 1
        new = self.mock_image_create.return_value
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
        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v2_required(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "raw", "import_data": true,
            "container_format": "docker",
            "visibility": "public", "protected": false,
            "source_type": "url", "image_url": "test.com" }''')
        self.mock_VERSIONS.active = 2
        new = self.mock_image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'raw',
                    'container_format': 'docker',
                    'copy_from': 'test.com',
                    'visibility': 'public',
                    'protected': False,
                    'min_disk': 0,
                    'min_ram': 0
                    }
        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v1_additional_props(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "raw", "import_data": true,
            "container_format": "docker",
            "visibility": "public", "protected": false,
            "arbitrary": "property", "another": "prop",
            "source_type": "url", "image_url": "test.com" }''')
        self.mock_VERSIONS.active = 1
        new = self.mock_image_create.return_value
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
        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['image_create', 'VERSIONS']})
    def test_image_create_v2_additional_props(self):
        request = self.mock_rest_request(body='''{"name": "Test",
            "disk_format": "raw", "import_data": true,
            "container_format": "docker",
            "visibility": "public", "protected": false,
            "arbitrary": "property", "another": "prop",
            "source_type": "url", "image_url": "test.com" }''')
        self.mock_VERSIONS.active = 2
        new = self.mock_image_create.return_value
        new.to_dict.return_value = {'name': 'testimage'}
        new.name = 'testimage'

        metadata = {'name': 'Test',
                    'disk_format': 'raw',
                    'container_format': 'docker',
                    'copy_from': 'test.com',
                    'visibility': 'public',
                    'protected': False,
                    'min_disk': 0,
                    'min_ram': 0,
                    'arbitrary': 'property',
                    'another': 'prop'
                    }
        response = glance.Images().put(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/glance/images/testimage')
        self.mock_image_create.assert_called_once_with(request, **metadata)

    @test.create_mocks({api.glance: ['metadefs_namespace_full_list']})
    def test_namespace_get_list(self):
        request = self.mock_rest_request(**{'GET': {}})
        self.mock_metadefs_namespace_full_list.return_value = (
            [{'namespace': '1'}, {'namespace': '2'}], False, False
        )

        response = glance.MetadefsNamespaces().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"namespace": "1"}, {"namespace": "2"}],
                          "has_more_data": False, "has_prev_data": False})
        self.mock_metadefs_namespace_full_list.assert_called_once_with(
            request, filters={}
        )

    @test.create_mocks({api.glance: ['metadefs_namespace_full_list']})
    def test_namespace_get_list_kwargs_and_filters(self):
        kwargs = {
            'sort_dir': 'desc',
            'sort_key': 'namespace',
            'marker': 1,
            'paginate': False,
        }
        filters = {'resource_types': 'type'}
        request = self.mock_rest_request(
            **{'GET': dict(kwargs, **filters)})
        self.mock_metadefs_namespace_full_list.return_value = (
            [{'namespace': '1'}, {'namespace': '2'}], False, False
        )

        response = glance.MetadefsNamespaces().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"namespace": "1"}, {"namespace": "2"}],
                          "has_more_data": False, "has_prev_data": False})
        self.mock_metadefs_namespace_full_list.assert_called_once_with(
            request, filters=filters, **kwargs
        )

    @test.create_mocks({api.glance: ['metadefs_resource_types_list']})
    def test_resource_types_get_list(self):
        request = self.mock_rest_request(**{'GET': {}})
        self.mock_metadefs_resource_types_list.return_value = ([
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

        self.mock_metadefs_resource_types_list.assert_called_once_with(request)
