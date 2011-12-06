# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django import http
from glance import client as glance_client
from mox import IsA

from horizon.tests.api_tests.utils import *


class GlanceApiTests(APITestCase):
    def stub_glance_api(self, count=1):
        self.mox.StubOutWithMock(api.glance, 'glance_api')
        glance_api = self.mox.CreateMock(glance_client.Client)
        glance_api.token = TEST_TOKEN
        for i in range(count):
            api.glance.glance_api(IsA(http.HttpRequest)).AndReturn(glance_api)
        return glance_api

    def test_get_glance_api(self):
        self.mox.StubOutClassWithMocks(glance_client, 'Client')
        client_instance = glance_client.Client(TEST_HOSTNAME, TEST_PORT,
                                                        auth_tok=TEST_TOKEN)
        # Normally ``auth_tok`` is set in ``Client.__init__``, but mox doesn't
        # duplicate that behavior so we set it manually.
        client_instance.auth_tok = TEST_TOKEN

        self.mox.StubOutWithMock(api.glance, 'url_for')
        api.glance.url_for(IsA(http.HttpRequest), 'image').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        ret_val = api.glance.glance_api(self.request)
        self.assertIsNotNone(ret_val)
        self.assertEqual(ret_val.auth_tok, TEST_TOKEN)

    def test_image_create(self):
        IMAGE_FILE = 'someData'
        IMAGE_META = {'metadata': 'foo'}

        glance_api = self.stub_glance_api()
        glance_api.add_image(IMAGE_META, IMAGE_FILE).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.image_create(self.request, IMAGE_META, IMAGE_FILE)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)

    def test_image_delete(self):
        IMAGE_ID = '1'

        glance_api = self.stub_glance_api()
        glance_api.delete_image(IMAGE_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.image_delete(self.request, IMAGE_ID)

        self.assertEqual(ret_val, TEST_RETURN)

    def test_image_get_meta(self):
        IMAGE_ID = '1'

        glance_api = self.stub_glance_api()
        glance_api.get_image_meta(IMAGE_ID).AndReturn([TEST_RETURN])

        self.mox.ReplayAll()

        ret_val = api.image_get_meta(self.request, IMAGE_ID)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, [TEST_RETURN])

    def test_image_list_detailed(self):
        images = (TEST_RETURN, TEST_RETURN + '2')
        glance_api = self.stub_glance_api()
        glance_api.get_images_detailed().AndReturn(images)

        self.mox.ReplayAll()

        ret_val = api.image_list_detailed(self.request)

        self.assertEqual(len(ret_val), len(images))
        for image in ret_val:
            self.assertIsInstance(image, api.Image)
            self.assertIn(image._apidict, images)

    def test_image_update(self):
        IMAGE_ID = '1'
        IMAGE_META = {'metadata': 'foobar'}

        glance_api = self.stub_glance_api(count=2)
        glance_api.update_image(IMAGE_ID, image_meta={}).AndReturn(TEST_RETURN)
        glance_api.update_image(IMAGE_ID,
                                image_meta=IMAGE_META).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.image_update(self.request, IMAGE_ID)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)

        ret_val = api.image_update(self.request,
                                   IMAGE_ID,
                                   image_meta=IMAGE_META)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)


# Wrapper classes that have other attributes or methods need testing
class ImageWrapperTests(test.TestCase):
    dict_with_properties = {
            'properties':
                {'image_state': 'running'},
            'size': 100,
            }
    dict_without_properties = {
            'size': 100,
            }

    def test_get_properties(self):
        image = api.Image(self.dict_with_properties)
        image_props = image.properties
        self.assertIsInstance(image_props, api.ImageProperties)
        self.assertEqual(image_props.image_state, 'running')

    def test_get_other(self):
        image = api.Image(self.dict_with_properties)
        self.assertEqual(image.size, 100)

    def test_get_properties_missing(self):
        image = api.Image(self.dict_without_properties)
        with self.assertRaises(AttributeError):
            image.properties

    def test_get_other_missing(self):
        image = api.Image(self.dict_without_properties)
        with self.assertRaises(AttributeError):
            self.assertNotIn('missing', image._attrs,
                msg="Test assumption broken.  Find new missing attribute")
            image.missing
