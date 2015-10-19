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


class TestVolumes(helpers.TestCase):
    VOLUME_NAME = helpers.gen_random_resource_name("volume")

    def test_volume_create_edit_delete(self):
        """This test case checks create, edit, delete volume functionality
            executed by non-admin user::
            Steps:
            1. Login to Horizon Dashboard as horizon user
            2. Navigate to Project -> Compute -> Volumes page
            3. Create new volume
            4. Check that the volume is in the list
            5. Check that no Error messages present
            6. Edit the volume
            7. Check that the volume is still in the list
            8. Check that no Error messages present
            9. Delete the volume
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

        volumes_page.delete_volume(self.VOLUME_NAME)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_deleted(self.VOLUME_NAME))


class TestAdminVolumes(helpers.AdminTestCase):
    VOLUME_NAME = helpers.gen_random_resource_name("volume")

    def test_volume_create_edit_delete_through_admin(self):
        """This test case checks create, edit, delete volume functionality
            executed by admin user:
            Steps:
            1. Login to Horizon Dashboard as admin user
            2. Navigate to Project -> Compute -> Volumes page
            3. Create new volume
            4. Check that the volume is in the list
            5. Check that no Error messages present
            6. Edit the volume
            7. Check that the volume is still in the list
            8. Check that no Error messages present
            9. Go to Admin/System/Volumes page
            10. Delete the volume
            11. Check that the volume is absent in the list
            12. Check that no Error messages present
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

        volumes_admin_page = self.home_pg.go_to_system_volumes_volumespage()

        volumes_admin_page.delete_volume(self.VOLUME_NAME)
        self.assertTrue(
            volumes_admin_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_admin_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_admin_page.is_volume_deleted(self.VOLUME_NAME))
