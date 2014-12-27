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

from openstack_dashboard.test.integration_tests import helpers


class TestImage(helpers.TestCase):
    IMAGE_NAME = helpers.gen_random_resource_name("image")

    def test_image_create_delete(self):
        """tests the image creation and deletion functionalities:
        * creates a new image from horizon.conf http_image
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """

        images_page = self.home_pg.go_to_compute_imagespage()

        images_page.create_image(self.IMAGE_NAME)
        self.assertTrue(images_page.is_image_present(self.IMAGE_NAME))
        self.assertTrue(images_page.is_image_active(self.IMAGE_NAME))

        images_page.delete_image(self.IMAGE_NAME)
        self.assertFalse(images_page.is_image_present(self.IMAGE_NAME))
