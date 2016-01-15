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
from openstack_dashboard.test.integration_tests.regions import messages


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
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(images_page.is_image_present(self.IMAGE_NAME))
        self.assertTrue(images_page.is_image_active(self.IMAGE_NAME))

        images_page.delete_image(self.IMAGE_NAME)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(images_page.is_image_present(self.IMAGE_NAME))

    def test_images_pagination(self):
        """This test checks images pagination
            Steps:
            1) Login to Horizon Dashboard as horizon user
            2) Navigate to user settings page
            3) Change 'Items Per Page' value to 1
            4) Go to Project -> Compute -> Images page
            5) Check that only 'Next' link is available, only one image is
            available (and it has correct name)
            6) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one image is available (and it has correct name)
            7) Click 'Next' and check that only 'Prev' link is available,
            only one image is visible (and it has correct name)
            8) Click 'Prev' and check results (should be the same as for step6)
            9) Click 'Prev' and check results (should be the same as for step5)
            10) Go to user settings page and restore 'Items Per Page'
        """
        default_image_list = self.CONFIG.image.images_list
        items_per_page = 1
        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': items_per_page,
                                 'Names': [default_image_list[0]]}
        second_page_definition = {'Next': True, 'Prev': True,
                                  'Count': items_per_page,
                                  'Names': [default_image_list[1]]}
        third_page_definition = {'Next': False, 'Prev': True,
                                 'Count': items_per_page,
                                 'Names': [default_image_list[2]]}

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(items_per_page)
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        images_page = self.home_pg.go_to_compute_imagespage()
        images_page.images_table.assert_definition(first_page_definition)

        images_page.images_table.turn_next_page()
        images_page.images_table.assert_definition(second_page_definition)

        images_page.images_table.turn_next_page()
        images_page.images_table.assert_definition(third_page_definition)

        images_page.images_table.turn_prev_page()
        images_page.images_table.assert_definition(second_page_definition)

        images_page.images_table.turn_prev_page()
        images_page.images_table.assert_definition(first_page_definition)

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize()
        settings_page.find_message_and_dismiss(messages.SUCCESS)


class TestImageAdmin(helpers.AdminTestCase):
    IMAGE_NAME = helpers.gen_random_resource_name("image")

    def test_image_create_delete_under_admin(self):
        """tests the image creation and deletion functionalities under Admin:
        * creates a new image from horizon.conf http_image
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """

        images_page = self.home_pg.go_to_system_imagespage()

        images_page.create_image(self.IMAGE_NAME)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(images_page.is_image_present(self.IMAGE_NAME))
        self.assertTrue(images_page.is_image_active(self.IMAGE_NAME))

        images_page.delete_image(self.IMAGE_NAME)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(images_page.is_image_present(self.IMAGE_NAME))

    def test_images_pagination_under_admin(self):
        """This test checks images pagination under admin user
            Steps:
            1) Login to Horizon Dashboard as admin user
            2) Navigate to user settings page
            3) Change 'Items Per Page' value to 1
            4) Go to Admin -> System -> Images page
            5) Check that only 'Next' link is available, only one image is
            available (and it has correct name)
            6) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one image is available (and it has correct name)
            7) Click 'Next' and check that only 'Prev' link is available,
            only one image is visible (and it has correct name)
            8) Click 'Prev' and check results (should be the same as for step6)
            9) Click 'Prev' and check results (should be the same as for step5)
            10) Go to user settings page and restore 'Items Per Page'
        """
        default_image_list = self.CONFIG.image.images_list
        items_per_page = 1
        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': items_per_page,
                                 'Names': [default_image_list[0]]}
        second_page_definition = {'Next': True, 'Prev': True,
                                  'Count': items_per_page,
                                  'Names': [default_image_list[1]]}
        third_page_definition = {'Next': False, 'Prev': True,
                                 'Count': items_per_page,
                                 'Names': [default_image_list[2]]}

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(items_per_page)
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        images_page = self.home_pg.go_to_system_imagespage()
        images_page.images_table.assert_definition(first_page_definition)

        images_page.images_table.turn_next_page()
        images_page.images_table.assert_definition(second_page_definition)

        images_page.images_table.turn_next_page()
        images_page.images_table.assert_definition(third_page_definition)

        images_page.images_table.turn_prev_page()
        images_page.images_table.assert_definition(second_page_definition)

        images_page.images_table.turn_prev_page()
        images_page.images_table.assert_definition(first_page_definition)

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize()
        settings_page.find_message_and_dismiss(messages.SUCCESS)
