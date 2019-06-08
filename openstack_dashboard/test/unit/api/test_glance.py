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

from django.conf import settings
from django.test.utils import override_settings
import mock

from openstack_dashboard import api
from openstack_dashboard.api import base
from openstack_dashboard.test import helpers as test


class GlanceApiTests(test.APIMockTestCase):
    def setUp(self):
        super(GlanceApiTests, self).setUp()
        api.glance.VERSIONS.clear_active_cache()

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_long_url(self, mock_glanceclient):
        servers = self.servers.list() * 100
        api_images = self.images_api.list() * 100
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if hasattr(instance, 'image')]
        expected_images = self.images.list() * 100
        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = iter(api_images)

        images = api.glance.image_list_detailed_by_ids(self.request,
                                                       instances_img_ids)
        self.assertEqual(images, expected_images)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_by_ids(self, mock_glanceclient):
        servers = self.servers.list()
        api_images = self.images_api.list()
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if hasattr(instance, 'image')]
        expected_images = self.images.list()

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = iter(api_images)

        images = api.glance.image_list_detailed_by_ids(self.request,
                                                       instances_img_ids)
        self.assertEqual(images, expected_images)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_no_pagination(self, mock_glanceclient):
        # Verify that all images are returned even with a small page size
        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        filters = {}
        limit = settings.API_RESULT_LIMIT

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = iter(api_images)

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request)

        mock_images_list.assert_called_once_with(page_size=limit,
                                                 limit=limit,
                                                 filters=filters,
                                                 sort_dir='desc',
                                                 sort_key='created_at')
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_sort_options(self, mock_glanceclient):
        # Verify that sort_dir and sort_key work
        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        filters = {}
        limit = settings.API_RESULT_LIMIT
        sort_dir = 'asc'
        sort_key = 'min_disk'

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = iter(api_images)

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            sort_dir=sort_dir,
            sort_key=sort_key)

        mock_images_list.assert_called_once_with(page_size=limit,
                                                 limit=limit,
                                                 filters=filters,
                                                 sort_dir=sort_dir,
                                                 sort_key=sort_key)
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_pagination_more_page_size(self,
                                                           mock_glanceclient):
        # The total snapshot count is over page size, should return
        # page_size images.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = settings.API_RESULT_LIMIT

        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = images_iter

        # Pass back all images, ignoring filters
        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            marker=None,
            filters=filters,
            paginate=True)

        expected_images = expected_images[:page_size]

        mock_images_list.assert_called_once_with(limit=limit,
                                                 page_size=page_size + 1,
                                                 filters=filters,
                                                 sort_dir='desc',
                                                 sort_key='created_at')
        self.assertListEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertFalse(has_prev)
        # Ensure that only the needed number of images are consumed
        # from the iterator (page_size + 1).
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    @override_settings(API_RESULT_PAGE_SIZE=20)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_pagination_less_page_size(self,
                                                           mock_glanceclient):
        # The total image count is less than page size, should return images
        # more, prev should return False.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = settings.API_RESULT_LIMIT

        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = iter(api_images)

        # Pass back all images, ignoring filters
        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            filters=filters,
            paginate=True)

        expected_images = expected_images[:page_size]

        mock_images_list.assert_called_once_with(limit=limit,
                                                 page_size=page_size + 1,
                                                 filters=filters,
                                                 sort_dir='desc',
                                                 sort_key='created_at')
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=10)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_pagination_equal_page_size(self,
                                                            mock_glanceclient):
        # The total image count equals page size, should return
        # page_size images. more, prev should return False
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = settings.API_RESULT_LIMIT

        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = iter(api_images)

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            filters=filters,
            paginate=True)

        expected_images = expected_images[:page_size]

        mock_images_list.assert_called_once_with(limit=limit,
                                                 page_size=page_size + 1,
                                                 filters=filters,
                                                 sort_dir='desc',
                                                 sort_key='created_at')
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)
        self.assertEqual(len(expected_images), len(images))

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_pagination_marker(self, mock_glanceclient):
        # Tests getting a second page with a marker.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = settings.API_RESULT_LIMIT
        marker = 'nonsense'

        api_images = self.images_api.list()[page_size:]
        expected_images = self.images.list()[page_size:]  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = images_iter

        # Pass back all images, ignoring filters
        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            marker=marker,
            filters=filters,
            paginate=True)

        expected_images = expected_images[:page_size]

        mock_images_list.assert_called_once_with(limit=limit,
                                                 page_size=page_size + 1,
                                                 filters=filters,
                                                 marker=marker,
                                                 sort_dir='desc',
                                                 sort_key='created_at')
        self.assertListEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertTrue(has_prev)
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'glanceclient')
    def test_image_list_detailed_pagination_marker_prev(self,
                                                        mock_glanceclient):
        # Tests getting previous page with a marker.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = settings.API_RESULT_LIMIT
        marker = 'nonsense'

        api_images = self.images_api.list()[page_size:]
        expected_images = self.images.list()[page_size:]  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = mock_glanceclient.return_value
        mock_images_list = glanceclient.images.list
        mock_images_list.return_value = images_iter

        # Pass back all images, ignoring filters
        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            marker=marker,
            filters=filters,
            sort_dir='asc',
            paginate=True)

        expected_images = expected_images[:page_size]

        mock_images_list.assert_called_once_with(limit=limit,
                                                 page_size=page_size + 1,
                                                 marker=marker,
                                                 filters=filters,
                                                 sort_dir='asc',
                                                 sort_key='created_at')
        self.assertListEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertTrue(has_prev)
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    @mock.patch.object(api.glance, 'glanceclient')
    def test_get_image_empty_name(self, mock_glanceclient):
        glanceclient = mock_glanceclient.return_value
        mock_images_get = glanceclient.images.get
        mock_images_get.return_value = self.empty_name_image

        image = api.glance.image_get(self.request, 'empty')

        mock_images_get.assert_called_once_with('empty')
        self.assertIsNone(image.name)

    @mock.patch.object(api.glance, 'glanceclient')
    def test_metadefs_namespace_list(self, mock_glanceclient):
        metadata_defs = self.metadata_defs.list()
        limit = settings.API_RESULT_LIMIT

        glanceclient = mock_glanceclient.return_value
        mock_metadefs_list = glanceclient.metadefs_namespace.list
        mock_metadefs_list.return_value = metadata_defs

        defs, more, prev = api.glance.metadefs_namespace_list(self.request)

        mock_metadefs_list.assert_called_once_with(page_size=limit,
                                                   limit=limit,
                                                   filters={},
                                                   sort_dir='asc',
                                                   sort_key='namespace')
        self.assertEqual(len(metadata_defs), len(defs))
        for i in range(len(metadata_defs)):
            self.assertEqual(metadata_defs[i].namespace, defs[i].namespace)
        self.assertFalse(more)
        self.assertFalse(prev)

    @mock.patch.object(api.glance, 'glanceclient')
    def test_metadefs_namespace_list_with_properties_target(self,
                                                            mock_glanceclient):
        metadata_defs = self.metadata_defs.list()
        limit = settings.API_RESULT_LIMIT
        filters = {'resource_types': ['OS::Cinder::Volume'],
                   'properties_target': 'user'}

        glanceclient = mock_glanceclient.return_value
        mock_metadefs_list = glanceclient.metadefs_namespace.list
        mock_metadefs_list.return_value = metadata_defs

        defs = api.glance.metadefs_namespace_list(self.request,
                                                  filters=filters)[0]

        mock_metadefs_list.assert_called_once_with(page_size=limit,
                                                   limit=limit,
                                                   filters=filters,
                                                   sort_dir='asc',
                                                   sort_key='namespace')
        self.assertEqual(1, len(defs))
        self.assertEqual('namespace_4', defs[0].namespace)

    @mock.patch.object(api.glance, 'get_version', return_value=1)
    def test_metadefs_namespace_list_v1(self, mock_version):
        defs, more, prev = api.glance.metadefs_namespace_list(self.request)
        self.assertItemsEqual(defs, [])
        self.assertFalse(more)
        self.assertFalse(prev)

    @mock.patch.object(api.glance, 'get_version', return_value=1)
    def test_metadefs_resource_types_list_v1(self, mock_version):
        res_types = api.glance.metadefs_resource_types_list(self.request)
        self.assertItemsEqual(res_types, [])

    @mock.patch.object(api.glance, 'glanceclient')
    def _test_image_create_external_upload(self, mock_glanceclient,
                                           api_version=2):
        expected_image = self.images.first()
        service = base.get_service_from_catalog(self.service_catalog, 'image')
        base_url = base.get_url_for_service(service, 'RegionOne', 'publicURL')
        if api_version == 1:
            url_template = '%s/v1/images/%s'
        else:
            url_template = '%s/v2/images/%s/file'
        upload_url = url_template % (base_url, expected_image.id)

        glanceclient = mock_glanceclient.return_value
        mock_image_create = glanceclient.images.create
        mock_image_create.return_value = expected_image

        actual_image = api.glance.image_create(self.request, data='sample.iso')

        mock_image_create.assert_called_once()
        self.assertEqual(upload_url, actual_image.upload_url)
        self.assertEqual(self.request.user.token.id, actual_image.token_id)

    @override_settings(OPENSTACK_API_VERSIONS={"image": 1})
    def test_image_create_v1_external_upload(self):
        self._test_image_create_external_upload(api_version=1)

    def test_image_create_v2_external_upload(self):
        self._test_image_create_external_upload()

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_create_image_metadata_docker_v1(self):
        form_data = {
            'name': u'Docker image',
            'description': u'Docker image test',
            'source_type': u'url',
            'image_url': u'/',
            'disk_format': u'docker',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': False,
            'protected': False,
            'is_copying': False
        }
        meta = api.glance.create_image_metadata(form_data)
        self.assertEqual(meta['disk_format'], 'raw')
        self.assertEqual(meta['container_format'], 'docker')
        self.assertIn('properties', meta)
        self.assertNotIn('description', meta)
        self.assertNotIn('architecture', meta)
        self.assertEqual(meta['properties']['description'],
                         form_data['description'])
        self.assertEqual(meta['properties']['architecture'],
                         form_data['architecture'])

    def test_create_image_metadata_docker_v2(self):
        form_data = {
            'name': u'Docker image',
            'description': u'Docker image test',
            'source_type': u'url',
            'image_url': u'/',
            'disk_format': u'docker',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': False,
            'protected': False,
            'is_copying': False
        }
        meta = api.glance.create_image_metadata(form_data)
        self.assertEqual(meta['disk_format'], 'raw')
        self.assertEqual(meta['container_format'], 'docker')
        self.assertNotIn('properties', meta)
        self.assertEqual(meta['description'], form_data['description'])
        self.assertEqual(meta['architecture'], form_data['architecture'])

    def test_create_image_metadata_vhd(self):
        form_data = {
            'name': u'OVF image',
            'description': u'OVF image test',
            'source_type': u'url',
            'image_url': u'/',
            'disk_format': u'vhd',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': False,
            'protected': False,
            'is_copying': False
        }
        meta = api.glance.create_image_metadata(form_data)
        self.assertEqual(meta['disk_format'], 'vhd')
        self.assertEqual(meta['container_format'], 'ovf')
        self.assertNotIn('properties', meta)
        self.assertEqual(meta['description'], form_data['description'])
        self.assertEqual(meta['architecture'], form_data['architecture'])
