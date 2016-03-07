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
import time

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestVolumes(helpers.TestCase):
    VOLUME_NAME = helpers.gen_random_resource_name("volume")

    @property
    def volumes_page(self):
        return self.home_pg.go_to_compute_volumes_volumespage()

    def test_volume_create_edit_delete(self):
        """This test case checks create, edit, delete volume functionality:
            Steps:
            1. Login to Horizon Dashboard
            2. Navigate to Project -> Compute -> Volumes page
            3. Create new volume
            4. Check that the volume is in the list
            5. Check that no Error messages present
            6. Edit the volume
            7. Check that the volume is still in the list
            8. Check that no Error messages present
            9. Delete the volume via proper page (depends on user)
            10. Check that the volume is absent in the list
            11. Check that no Error messages present
        """
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        volumes_page.create_volume(self.VOLUME_NAME)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_present(self.VOLUME_NAME))
        self.assertTrue(volumes_page.is_volume_status(self.VOLUME_NAME,
                                                      'Available'))

        new_name = "edited_" + self.VOLUME_NAME
        volumes_page.edit_volume(self.VOLUME_NAME, new_name, "description")
        self.VOLUME_NAME = new_name
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_present(self.VOLUME_NAME))
        self.assertTrue(volumes_page.is_volume_status(self.VOLUME_NAME,
                                                      'Available'))

        volumes_page = self.volumes_page
        volumes_page.delete_volume(self.VOLUME_NAME)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_deleted(self.VOLUME_NAME))
        # NOTE(tsufiev): A short regression test on bug 1553314: we try to
        # re-open 'Create Volume' button after the volume was deleted. If the
        # regression occurs, the form won't appear (because link is going to be
        # invalid in this case). Give JavaScript callbacks an additional second
        # to do all the job and possibly cause the regression.
        if not isinstance(self, helpers.AdminTestCase):
            time.sleep(1)
            form = volumes_page.volumes_table.create_volume()
            form.cancel()

    def test_volumes_pagination(self):
        """This test checks volumes pagination
            Steps:
            1) Login to Horizon Dashboard
            2) Go to Project -> Compute -> Volumes -> Volumes tab and create
            three volumes
            3) Navigate to user settings page
            4) Change 'Items Per Page' value to 1
            5) Go to Project -> Compute -> Volumes -> Volumes tab or
            Admin -> System -> Volumes -> Volumes tab (depends on user)
            6) Check that only 'Next' link is available, only one volume is
            available (and it has correct name)
            7) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one volume is available (and it has correct name)
            8) Click 'Next' and check that only 'Prev' link is available,
            only one volume is visible (and it has correct name)
            9) Click 'Prev' and check result (should be the same as for step7)
            10) Click 'Prev' and check result (should be the same as for step6)
            11) Go to user settings page and restore 'Items Per Page'
            12) Delete created volumes
        """
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        count = 3
        items_per_page = 1
        volumes_names = ["{0}_{1}".format(self.VOLUME_NAME, i) for i in
                         range(count)]
        for volume_name in volumes_names:
            volumes_page.create_volume(volume_name)
            volumes_page.find_message_and_dismiss(messages.INFO)
            self.assertTrue(volumes_page.is_volume_present(volume_name))

        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': items_per_page,
                                 'Names': [volumes_names[2]]}
        second_page_definition = {'Next': True, 'Prev': True,
                                  'Count': items_per_page,
                                  'Names': [volumes_names[1]]}
        third_page_definition = {'Next': False, 'Prev': True,
                                 'Count': items_per_page,
                                 'Names': [volumes_names[0]]}
        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(items_per_page)
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        volumes_page = self.volumes_page
        volumes_page.volumes_table.assert_definition(first_page_definition)

        volumes_page.volumes_table.turn_next_page()
        volumes_page.volumes_table.assert_definition(second_page_definition)

        volumes_page.volumes_table.turn_next_page()
        volumes_page.volumes_table.assert_definition(third_page_definition)

        volumes_page.volumes_table.turn_prev_page()
        volumes_page.volumes_table.assert_definition(second_page_definition)

        volumes_page.volumes_table.turn_prev_page()
        volumes_page.volumes_table.assert_definition(first_page_definition)

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize()
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        volumes_page = self.volumes_page
        for volume_name in volumes_names:
            volumes_page.delete_volume(volume_name)
            volumes_page.find_message_and_dismiss(messages.SUCCESS)
            self.assertTrue(volumes_page.is_volume_deleted(volume_name))


class TestAdminVolumes(helpers.AdminTestCase, TestVolumes):
    VOLUME_NAME = helpers.gen_random_resource_name("volume")

    @property
    def volumes_page(self):
        return self.home_pg.go_to_system_volumes_volumespage()
