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

from django.conf import settings

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class GlanceApiTests(test.APITestCase):
    def test_snapshot_list_detailed(self):
        images = self.images.list()
        filters = {'property-image_type': 'snapshot'}
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.list(page_size=page_size,
                                 limit=limit,
                                 filters=filters,).AndReturn(images)
        self.mox.ReplayAll()

        # No assertions are necessary. Verification is handled by mox.
        api.glance.snapshot_list_detailed(self.request)

    def test_snapshot_list_detailed_pagination(self):
        images = self.images.list()
        filters = {'property-image_type': 'snapshot'}
        page_size = 2
        temp_page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', None)
        settings.API_RESULT_PAGE_SIZE = page_size
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        glanceclient = self.stub_glanceclient()
        glanceclient.images = self.mox.CreateMockAnything()
        glanceclient.images.list(limit=limit,
                                 page_size=page_size,
                                 filters=filters,) \
                                .AndReturn(images[0:page_size])
        self.mox.ReplayAll()

        # No assertions are necessary. Verification is handled by mox.
        api.glance.snapshot_list_detailed(self.request)

        # Restore
        if temp_page_size:
            settings.API_RESULT_PAGE_SIZE = temp_page_size
        else:
            del settings.API_RESULT_PAGE_SIZE
