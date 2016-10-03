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

from openstack_dashboard import api
from openstack_dashboard.api import base
from openstack_dashboard.test import helpers as test


class GlanceApiTests(test.APITestCase):
    def setUp(self):
        super(GlanceApiTests, self).setUp()
        api.glance.VERSIONS.clear_active_cache()

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_no_pagination(self):
        # Verify that all images are returned even with a small page size
        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        filters = {}
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.list(page_size=limit,
                                 limit=limit,
                                 filters=filters,
                                 sort_dir='desc',
                                 sort_key='created_at',) \
            .AndReturn(iter(api_images))
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request)

        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_sort_options(self):
        # Verify that sort_dir and sort_key work
        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        filters = {}
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        sort_dir = 'asc'
        sort_key = 'min_disk'

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.list(page_size=limit,
                                 limit=limit,
                                 filters=filters,
                                 sort_dir=sort_dir,
                                 sort_key=sort_key) \
                           .AndReturn(iter(api_images))
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            sort_dir=sort_dir,
            sort_key=sort_key)
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_pagination_more_page_size(self):
        # The total snapshot count is over page size, should return
        # page_size images.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        # Pass back all images, ignoring filters
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 filters=filters,
                                 sort_dir='desc',
                                 sort_key='created_at',).AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            marker=None,
            filters=filters,
            paginate=True)
        expected_images = expected_images[:page_size]
        self.assertListEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertFalse(has_prev)
        # Ensure that only the needed number of images are consumed
        # from the iterator (page_size + 1).
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    @override_settings(API_RESULT_PAGE_SIZE=20)
    def test_image_list_detailed_pagination_less_page_size(self):
        # The total image count is less than page size, should return images
        # more, prev should return False.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        # Pass back all images, ignoring filters
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 filters=filters,
                                 sort_dir='desc',
                                 sort_key='created_at',).AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            filters=filters,
            paginate=True)
        expected_images = expected_images[:page_size]
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=9)
    def test_image_list_detailed_pagination_equal_page_size(self):
        # The total image count equals page size, should return
        # page_size images. more, prev should return False
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        api_images = self.images_api.list()
        expected_images = self.images.list()  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 filters=filters,
                                 sort_dir='desc',
                                 sort_key='created_at',).AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            filters=filters,
            paginate=True)
        expected_images = expected_images[:page_size]
        self.assertListEqual(images, expected_images)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)
        self.assertEqual(len(expected_images), len(images))

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_pagination_marker(self):
        # Tests getting a second page with a marker.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        marker = 'nonsense'

        api_images = self.images_api.list()[page_size:]
        expected_images = self.images.list()[page_size:]  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        # Pass back all images, ignoring filters
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 filters=filters,
                                 marker=marker,
                                 sort_dir='desc',
                                 sort_key='created_at',) \
            .AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            marker=marker,
            filters=filters,
            paginate=True)
        expected_images = expected_images[:page_size]
        self.assertListEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertTrue(has_prev)
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_pagination_marker_prev(self):
        # Tests getting previous page with a marker.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        marker = 'nonsense'

        api_images = self.images_api.list()[page_size:]
        expected_images = self.images.list()[page_size:]  # Wrapped Images
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        # Pass back all images, ignoring filters
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 marker=marker,
                                 filters=filters,
                                 sort_dir='asc',
                                 sort_key='created_at',) \
            .AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more, has_prev = api.glance.image_list_detailed(
            self.request,
            marker=marker,
            filters=filters,
            sort_dir='asc',
            paginate=True)
        expected_images = expected_images[:page_size]
        self.assertListEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertTrue(has_prev)
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    def test_get_image_empty_name(self):
        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.get('empty').AndReturn(self.empty_name_image)
        self.mox.ReplayAll()
        image = api.glance.image_get(self.request, 'empty')
        self.assertIsNone(image.name)

    def test_metadefs_namespace_list(self):
        metadata_defs = self.metadata_defs.list()
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        glanceclient = self.stub_glanceclient()
        glanceclient.metadefs_namespace = self.mox.CreateMockAnything()
        glanceclient.metadefs_namespace.list(page_size=limit,
                                             limit=limit,
                                             filters={},
                                             sort_dir='asc',
                                             sort_key='namespace',) \
            .AndReturn(metadata_defs)

        self.mox.ReplayAll()

        defs, more, prev = api.glance.metadefs_namespace_list(self.request)
        self.assertEqual(len(metadata_defs), len(defs))
        for i in range(len(metadata_defs)):
            self.assertEqual(metadata_defs[i].namespace, defs[i].namespace)
        self.assertFalse(more)
        self.assertFalse(prev)

    def test_metadefs_namespace_list_with_properties_target(self):
        metadata_defs = self.metadata_defs.list()
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        filters = {'resource_types': ['OS::Cinder::Volume'],
                   'properties_target': 'user'}

        glanceclient = self.stub_glanceclient()
        glanceclient.metadefs_namespace = self.mox.CreateMockAnything()
        glanceclient.metadefs_namespace.list(page_size=limit,
                                             limit=limit,
                                             filters=filters,
                                             sort_dir='asc',
                                             sort_key='namespace', ) \
            .AndReturn(metadata_defs)

        self.mox.ReplayAll()

        defs = api.glance.metadefs_namespace_list(self.request,
                                                  filters=filters)[0]
        self.assertEqual(1, len(defs))
        self.assertEqual('namespace_4', defs[0].namespace)

    @test.create_stubs({api.glance: ('get_version',)})
    def test_metadefs_namespace_list_v1(self):
        api.glance.get_version().AndReturn(1)

        self.mox.ReplayAll()

        defs, more, prev = api.glance.metadefs_namespace_list(self.request)
        self.assertItemsEqual(defs, [])
        self.assertFalse(more)
        self.assertFalse(prev)

    @test.create_stubs({api.glance: ('get_version',)})
    def test_metadefs_resource_types_list_v1(self):
        api.glance.get_version().AndReturn(1)

        self.mox.ReplayAll()

        res_types = api.glance.metadefs_resource_types_list(self.request)
        self.assertItemsEqual(res_types, [])

    def _test_image_create_external_upload(self, api_version=2):
        expected_image = self.images.first()
        service = base.get_service_from_catalog(self.service_catalog, 'image')
        base_url = base.get_url_for_service(service, 'RegionOne', 'publicURL')
        if api_version == 1:
            url_template = '%s/v1/images/%s'
        else:
            url_template = '%s/v2/images/%s/file'
        upload_url = url_template % (base_url, expected_image.id)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.create().AndReturn(expected_image)
        self.mox.ReplayAll()

        actual_image = api.glance.image_create(self.request, data='sample.iso')
        self.assertEqual(upload_url, actual_image.upload_url)
        self.assertEqual(self.request.user.token.id, actual_image.token_id)

    @override_settings(OPENSTACK_API_VERSIONS={"image": 1})
    def test_image_create_v1_external_upload(self):
        self._test_image_create_external_upload(api_version=1)

    def test_image_create_v2_external_upload(self):
        self._test_image_create_external_upload()
