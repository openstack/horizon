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
import pytest

from openstack_dashboard.test.integration_tests import decorators
from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


@decorators.config_option_required('image.panel_type', 'legacy',
                                   message="Angular Panels not tested")
class TestImagesLegacy(helpers.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.IMAGE_NAME = helpers.gen_random_resource_name("image")

    @property
    def images_page(self):
        return self.home_pg.go_to_project_compute_imagespage()


@decorators.config_option_required('image.panel_type', 'angular',
                                   message="Legacy Panels not tested")
class TestImagesAngular(helpers.TestCase):
    @property
    def images_page(self):
        # FIXME(tsufiev): had to return angularized version of Images Page
        # object with the horrendous hack below because it's not so easy to
        # wire into the Navigation machinery and tell it to return an '*NG'
        # version of ImagesPage class if one adds '_ng' suffix to
        # 'go_to_compute_imagespage()' method. Yet that's how it should work
        # (or rewrite Navigation module completely).
        from openstack_dashboard.test.integration_tests.pages.project.\
            compute.imagespage import ImagesPageNG
        self.home_pg.go_to_project_compute_imagespage()
        return ImagesPageNG(self.driver, self.CONFIG)

    def test_basic_image_browse(self):
        images_page = self.images_page
        self.assertEqual(images_page.header.text, 'Images')


class TestImagesBasic(TestImagesLegacy):
    """Login as demo user"""
    def image_create(self, local_file=None, **kwargs):
        images_page = self.images_page
        if local_file:
            images_page.create_image(self.IMAGE_NAME,
                                     image_file=local_file,
                                     **kwargs)
        else:
            images_page.create_image(self.IMAGE_NAME, **kwargs)
        self.assertTrue(images_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(images_page.is_image_present(self.IMAGE_NAME))
        self.assertTrue(images_page.is_image_active(self.IMAGE_NAME))
        return images_page

    def image_delete(self, image_name):
        images_page = self.images_page
        images_page.delete_image(image_name)
        self.assertTrue(images_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(images_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(images_page.is_image_present(self.IMAGE_NAME))

    @pytest.mark.skip(reason="Bug 1595335")
    def test_image_create_delete(self):
        """tests the image creation and deletion functionalities:

        * creates a new image from horizon.conf http_image
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """
        self.image_create()
        self.image_delete(self.IMAGE_NAME)

    def test_image_create_delete_from_local_file(self):
        """tests the image creation and deletion functionalities:

        * downloads image from horizon.conf stated in http_image
        * creates the image from the downloaded file
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """
        with helpers.gen_temporary_file() as file_name:
            self.image_create(local_file=file_name)
            self.image_delete(self.IMAGE_NAME)

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

        images_page = self.images_page
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

    def test_update_image_metadata(self):
        """Test update image metadata

        * logs in as admin user
        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * invokes action 'Update Metadata' for the image
        * adds custom filed 'metadata'
        * adds value 'image' for the custom filed 'metadata'
        * gets the actual description of the image
        * verifies that custom filed is present in the image description
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        new_metadata = {'metadata1': helpers.gen_random_resource_name("value"),
                        'metadata2': helpers.gen_random_resource_name("value")}

        with helpers.gen_temporary_file() as file_name:
            # TODO(tsufiev): had to add non-empty description to an image,
            # because description is now considered a metadata and we want
            # the metadata in a newly created image to be valid
            images_page = self.image_create(local_file=file_name,
                                            description='test description')
            images_page.add_custom_metadata(self.IMAGE_NAME, new_metadata)
            results = images_page.check_image_details(self.IMAGE_NAME,
                                                      new_metadata)
            self.image_delete(self.IMAGE_NAME)
            self.assertSequenceTrue(results)

    def test_remove_protected_image(self):
        """tests that protected image is not deletable

        * logs in as admin user
        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * marks 'Protected' checkbox
        * verifies that edit action was successful
        * verifies that delete action is not available in the list
        * tries to delete the image
        * verifies that exception is generated for the protected image
        * unmarks 'Protected' checkbox
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        with helpers.gen_temporary_file() as file_name:
            images_page = self.image_create(local_file=file_name)
            images_page.edit_image(self.IMAGE_NAME, protected=True)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))

            # Check that Delete action is not available in the action list.
            # The below action will generate exception since the bind fails.
            # But only ValueError with message below is expected here.
            with self.assertRaisesRegex(ValueError, 'Could not bind method'):
                images_page.delete_image_via_row_action(self.IMAGE_NAME)

            # Try to delete image. That should not be possible now.
            images_page.delete_image(self.IMAGE_NAME)
            self.assertFalse(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.ERROR))
            self.assertTrue(images_page.is_image_present(self.IMAGE_NAME))

            images_page.edit_image(self.IMAGE_NAME, protected=False)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.image_delete(self.IMAGE_NAME)

    def test_edit_image_description_and_name(self):
        """tests that image description is editable

        * creates image from locally downloaded file
        * verifies the image appears in the images table as active
        * toggle edit action and adds some description
        * verifies that edit action was successful
        * verifies that new description is seen on image details page
        * toggle edit action and changes image name
        * verifies that edit action was successful
        * verifies that image with new name is seen on the page
        * deletes the image
        * verifies the image does not appear in the table after deletion
        """
        new_description_text = helpers.gen_random_resource_name("description")
        new_image_name = helpers.gen_random_resource_name("image")
        with helpers.gen_temporary_file() as file_name:
            images_page = self.image_create(local_file=file_name)
            images_page.edit_image(self.IMAGE_NAME,
                                   description=new_description_text)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertFalse(
                images_page.find_message_and_dismiss(messages.ERROR))

            results = images_page.check_image_details(self.IMAGE_NAME,
                                                      {'Description':
                                                       new_description_text})
            self.assertSequenceTrue(results)

            # Just go back to the images page and toggle edit again
            images_page = self.images_page
            images_page.edit_image(self.IMAGE_NAME,
                                   new_name=new_image_name)
            self.assertTrue(
                images_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertFalse(
                images_page.find_message_and_dismiss(messages.ERROR))

            results = images_page.check_image_details(new_image_name,
                                                      {'Name':
                                                       new_image_name})
            self.assertSequenceTrue(results)

            self.image_delete(new_image_name)


class TestImagesAdvanced(TestImagesLegacy):
    """Login as demo user"""
    def test_create_volume_from_image(self):
        """This test case checks create volume from image functionality:

        Steps:
        1. Login to Horizon Dashboard as regular user
        2. Navigate to Project -> Compute -> Images
        3. Create new volume from image
        4. Check that volume is created with expected name
        5. Check that volume status is Available
        """
        images_page = self.images_page
        source_image = self.CONFIG.image.images_list[0]
        target_volume = "created_from_{0}".format(source_image)

        volumes_page = images_page.create_volume_from_image(
            source_image, volume_name=target_volume)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_present(target_volume))
        self.assertTrue(volumes_page.is_volume_status(target_volume,
                                                      'Available'))
        volumes_page.delete_volume(target_volume)
        volumes_page.find_message_and_dismiss(messages.SUCCESS)
        volumes_page.find_message_and_dismiss(messages.ERROR)
        self.assertTrue(volumes_page.is_volume_deleted(target_volume))

    def test_launch_instance_from_image(self):
        """This test case checks launch instance from image functionality:

        Steps:
        1. Login to Horizon Dashboard as regular user
        2. Navigate to Project -> Compute -> Images
        3. Launch new instance from image
        4. Check that instance is create
        5. Check that status of newly created instance is Active
        6. Check that image_name in correct in instances table
        """
        images_page = self.images_page
        source_image = self.CONFIG.image.images_list[0]
        target_instance = "created_from_{0}".format(source_image)
        instances_page = images_page.launch_instance_from_image(
            source_image, target_instance)
        self.assertTrue(
            instances_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            instances_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(instances_page.is_instance_active(target_instance))
        actual_image_name = instances_page.get_image_name(target_instance)
        self.assertEqual(source_image, actual_image_name)

        instances_page.delete_instance(target_instance)
        self.assertTrue(
            instances_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            instances_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(instances_page.is_instance_deleted(target_instance))


class TestImagesAdmin(helpers.AdminTestCase, TestImagesLegacy):
    """Login as admin user"""
    @property
    def images_page(self):
        return self.home_pg.go_to_admin_compute_imagespage()

    @pytest.mark.skip(reason="Bug 1774697")
    def test_image_create_delete(self):
        super().test_image_create_delete()

    def test_filter_images(self):
        """This test checks filtering of images

        Steps:
        1) Login to Horizon dashboard as admin user
        2) Go to Admin -> Compute -> Images
        3) Use filter by Image Name
        4) Check that filtered table has one image only (which name is
           equal to filter value)
        5) Check that no other images in the table
        6) Clear filter and set nonexistent image name. Check that 0 rows
           are displayed
        """
        images_list = self.CONFIG.image.images_list
        images_page = self.images_page

        images_page.images_table.filter(images_list[0])
        self.assertTrue(images_page.is_image_present(images_list[0]))
        for image in images_list[1:]:
            self.assertFalse(images_page.is_image_present(image))

        nonexistent_image_name = "{0}_test".format(self.IMAGE_NAME)
        images_page.images_table.filter(nonexistent_image_name)
        self.assertEqual(images_page.images_table.rows, [])

        images_page.images_table.filter('')
