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

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages

from openstack_dashboard.test.integration_tests.pages.project.\
    compute.instancespage import InstancesPage
from openstack_dashboard.test.integration_tests.pages.project.\
    volumes.volumespage import VolumesPage


class TestImagesBasicAngular(helpers.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.IMAGE_NAME = helpers.gen_random_resource_name("image")

    @property
    def images_page(self):
        return self.home_pg.go_to_project_compute_imagespage()

    def test_basic_image_browse(self):
        images_page = self.images_page
        self.assertEqual(images_page.header.text, 'Images')

    def image_create(self, local_file=None, **kwargs):
        images_page = self.images_page
        if local_file:
            images_page.create_image(self.IMAGE_NAME,
                                     image_file=local_file,
                                     **kwargs)
        else:
            images_page.create_image(self.IMAGE_NAME,
                                     image_source_type='url',
                                     **kwargs)
        self.assertEqual(
            images_page.find_messages_and_dismiss(), {messages.SUCCESS})
        self.assertTrue(images_page.is_image_present(self.IMAGE_NAME))
        self.assertTrue(images_page.is_image_active(self.IMAGE_NAME))
        return images_page

    def image_delete(self, image_name):
        images_page = self.images_page
        images_page.delete_image(image_name)
        self.assertEqual(
            images_page.find_messages_and_dismiss(), {messages.SUCCESS})
        self.assertFalse(images_page.is_image_present(self.IMAGE_NAME))

    def test_image_create_delete_from_local_file(self):
        """tests the image creation and deletion functionalities:

        * creates a new image from a generated file
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """
        with helpers.gen_temporary_file() as file_name:
            self.image_create(local_file=file_name)
            self.image_delete(self.IMAGE_NAME)

    # Run when Glance configuration and policies allow setting locations.
    @pytest.mark.skip(reason="IMAGES_ALLOW_LOCATION = False")
    def test_image_create_delete_from_url(self):
        """tests the image creation and deletion functionalities:

        * creates a new image from horizon.conf http_image
        * verifies the image appears in the images table as active
        * deletes the newly created image
        * verifies the image does not appear in the table after deletion
        """
        self.image_create()
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

        images_page = self.images_page

        # delete any old images except default ones
        images_page.wait_until_image_present(default_image_list[0])
        image_list = images_page.images_table.get_column_data(
            name_column='Name')
        garbage = [i for i in image_list if i not in default_image_list]
        if garbage:
            images_page.delete_images(garbage)
            self.assertEqual(
                images_page.find_messages_and_dismiss(), {messages.SUCCESS})

        items_per_page = 1
        images_count = 2
        images_names = ["{0}_{1}".format(self.IMAGE_NAME, item)
                        for item in range(images_count)]
        for image_name in images_names:
            with helpers.gen_temporary_file() as file_name:
                images_page.create_image(image_name, image_file=file_name)
            self.assertEqual(
                images_page.find_messages_and_dismiss(), {messages.SUCCESS})
            self.assertTrue(images_page.is_image_present(image_name))

        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': items_per_page,
                                 'Names': [default_image_list[0]]}
        second_page_definition = {'Next': True, 'Prev': True,
                                  'Count': items_per_page,
                                  'Names': [images_names[0]]}
        third_page_definition = {'Next': False, 'Prev': True,
                                 'Count': items_per_page,
                                 'Names': [images_names[1]]}

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(items_per_page)
        settings_page.find_messages_and_dismiss()

        images_page = self.images_page
        if not images_page.is_image_present(default_image_list[0]):
            images_page.wait_until_image_present(default_image_list[0])
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
        settings_page.find_messages_and_dismiss()

        images_page = self.images_page
        images_page.wait_until_image_present(default_image_list[0])
        images_page.delete_images(images_names)
        self.assertEqual(
            images_page.find_messages_and_dismiss(), {messages.SUCCESS})


class TestImagesAdminAngular(helpers.AdminTestCase, TestImagesBasicAngular):
    """Login as admin user"""

    @property
    def images_page(self):
        return self.home_pg.go_to_admin_compute_imagespage()

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
            self.assertEqual(
                images_page.find_messages_and_dismiss(), {messages.SUCCESS})

            # Check that Delete action is not available in the action list.
            # The below action will generate exception since the bind fails.
            # But only ValueError with message below is expected here.
            message = "Could not bind method 'delete_image_via_row_action' " \
                      "to action control 'Delete Image'"
            with self.assertRaisesRegex(ValueError, message):
                images_page.delete_image_via_row_action(self.IMAGE_NAME)

            # Edit image to make it not protected again and delete it.
            images_page = self.images_page

            images_page.edit_image(self.IMAGE_NAME, protected=False)
            self.assertEqual(
                images_page.find_messages_and_dismiss(), {messages.SUCCESS})
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
            self.assertEqual(
                images_page.find_messages_and_dismiss(), {messages.SUCCESS})

            results = images_page.check_image_details(self.IMAGE_NAME,
                                                      {'Description':
                                                       new_description_text})
            self.assertSequenceTrue(results)

            # Just go back to the images page and toggle edit again
            images_page = self.images_page
            images_page.edit_image(self.IMAGE_NAME,
                                   new_name=new_image_name)
            self.assertEqual(
                images_page.find_messages_and_dismiss(), {messages.SUCCESS})

            results = images_page.check_image_details(new_image_name,
                                                      {'Name':
                                                       new_image_name})
            self.assertSequenceTrue(results)
            self.image_delete(new_image_name)

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
        default_image_list = self.CONFIG.image.images_list
        images_page = self.images_page

        images_page.filter(default_image_list[0])
        self.assertTrue(images_page.is_image_present(default_image_list[0]))
        for image in default_image_list[1:]:
            self.assertFalse(images_page.is_image_present(image))

        images_page = self.images_page
        nonexistent_image_name = "{0}_test".format(self.IMAGE_NAME)
        images_page.filter(nonexistent_image_name)
        self.assertEqual(images_page.images_table.rows, [])

        images_page.filter('')


class TestImagesAdvancedAngular(helpers.TestCase):

    @property
    def images_page(self):
        return self.home_pg.go_to_project_compute_imagespage()

    def volumes_page(self):
        self.home_pg.go_to_project_volumes_volumespage()
        return VolumesPage(self.driver, self.CONFIG)

    def instances_page(self):
        self.home_pg.go_to_project_compute_instancespage()
        return InstancesPage(self.driver, self.CONFIG)

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

        images_page.create_volume_from_image(
            source_image, volume_name=target_volume)
        self.assertEqual(
            images_page.find_messages_and_dismiss(), {messages.INFO})

        volumes_page = self.volumes_page()

        self.assertTrue(volumes_page.is_volume_present(target_volume))
        self.assertTrue(volumes_page.is_volume_status(target_volume,
                                                      'Available'))
        volumes_page.delete_volume(target_volume)
        volumes_page.find_messages_and_dismiss()

        volumes_page = self.volumes_page()
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

        images_page.launch_instance_from_image(source_image, target_instance)
        self.assertEqual(
            images_page.find_messages_and_dismiss(), {messages.INFO})

        instances_page = self.instances_page()
        self.assertTrue(instances_page.is_instance_active(target_instance))
        instances_page = self.instances_page()
        actual_image_name = instances_page.get_image_name(target_instance)
        self.assertEqual(source_image, actual_image_name)

        instances_page.delete_instance(target_instance)
        self.assertEqual(
            instances_page.find_messages_and_dismiss(), {messages.INFO})
        self.assertTrue(instances_page.is_instance_deleted(target_instance))
