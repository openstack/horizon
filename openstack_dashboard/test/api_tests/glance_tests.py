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

from django.conf import settings  # noqa
from django.test.utils import override_settings  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class GlanceApiTests(test.APITestCase):
    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_no_pagination(self):
        # Verify that all images are returned even with a small page size
        api_images = self.images.list()
        filters = {}
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.list(page_size=limit,
                                 limit=limit,
                                 filters=filters,).AndReturn(iter(api_images))
        self.mox.ReplayAll()

        images, has_more = api.glance.image_list_detailed(self.request)
        self.assertItemsEqual(images, api_images)
        self.assertFalse(has_more)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_pagination(self):
        # The total snapshot count is over page size, should return
        # page_size images.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        api_images = self.images.list()
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        # Pass back all images, ignoring filters
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 filters=filters,).AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more = api.glance.image_list_detailed(self.request,
                                                          marker=None,
                                                          filters=filters,
                                                          paginate=True)
        expected_images = api_images[:page_size]
        self.assertItemsEqual(images, expected_images)
        self.assertTrue(has_more)
        # Ensure that only the needed number of images are consumed
        # from the iterator (page_size + 1).
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_image_list_detailed_pagination_marker(self):
        # Tests getting a second page with a marker.
        filters = {}
        page_size = settings.API_RESULT_PAGE_SIZE
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        marker = 'nonsense'

        api_images = self.images.list()[page_size:]
        images_iter = iter(api_images)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        # Pass back all images, ignoring filters
        glanceclient.images.list(limit=limit,
                                 page_size=page_size + 1,
                                 filters=filters,
                                 marker=marker).AndReturn(images_iter)
        self.mox.ReplayAll()

        images, has_more = api.glance.image_list_detailed(self.request,
                                                          marker=marker,
                                                          filters=filters,
                                                          paginate=True)
        expected_images = api_images[:page_size]
        self.assertItemsEqual(images, expected_images)
        self.assertTrue(has_more)
        self.assertEqual(len(list(images_iter)),
                         len(api_images) - len(expected_images) - 1)
