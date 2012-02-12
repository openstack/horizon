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

from horizon import api
from horizon import test


class GlanceApiTests(test.APITestCase):
    def test_get_glanceclient(self):
        """ Verify the client connection method does what we expect. """
        # Replace the original client which is stubbed out in setUp()
        api.glance.glanceclient = self._original_glanceclient

        client = api.glance.glanceclient(self.request)
        self.assertEqual(client.auth_tok, self.tokens.first().id)

    def test_image_get_meta(self):
        """ Verify "get" returns our custom Image class. """
        image = self.images.get(id='1')

        glanceclient = self.stub_glanceclient()
        glanceclient.get_image_meta(image.id).AndReturn(image)
        self.mox.ReplayAll()

        ret_val = api.image_get_meta(self.request, image.id)
        self.assertIsInstance(ret_val, api.glance.Image)
        self.assertEqual(ret_val._apidict, image)

    def test_image_list_detailed(self):
        """ Verify "list" returns our custom Image class. """
        images = self.images.list()

        glanceclient = self.stub_glanceclient()
        glanceclient.get_images_detailed().AndReturn(images)
        self.mox.ReplayAll()

        ret_val = api.image_list_detailed(self.request)
        for image in ret_val:
            self.assertIsInstance(image, api.glance.Image)
            self.assertIn(image._apidict, images)


class ImageWrapperTests(test.TestCase):
    """ Tests for wrapper classes since they have extra logic attached. """
    WITHOUT_PROPERTIES = {'size': 100}
    WITH_PROPERTIES = {'properties': {'image_state': 'running'},
                       'size': 100}

    def test_get_properties(self):
        image = api.Image(self.WITH_PROPERTIES)
        image_props = image.properties
        self.assertIsInstance(image_props, api.ImageProperties)
        self.assertEqual(image_props.image_state, 'running')

    def test_get_other(self):
        image = api.Image(self.WITH_PROPERTIES)
        self.assertEqual(image.size, 100)

    def test_get_properties_missing(self):
        image = api.Image(self.WITHOUT_PROPERTIES)
        with self.assertRaises(AttributeError):
            image.properties

    def test_get_other_missing(self):
        image = api.Image(self.WITHOUT_PROPERTIES)
        with self.assertRaises(AttributeError):
            self.assertNotIn('missing', image._attrs,
                msg="Test assumption broken.  Find new missing attribute")
            image.missing
