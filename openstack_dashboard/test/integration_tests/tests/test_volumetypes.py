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


class TestAdminVolumeTypes(helpers.AdminTestCase):
    VOLUME_TYPE_NAME = helpers.gen_random_resource_name("volume_type")

    def test_volume_type_create_delete(self):
        """This test case checks create, delete volume type:
            Steps:
            1. Login to Horizon Dashboard as admin user
            2. Navigate to Admin -> System -> Volumes -> Volume Types page
            3. Create new volume type
            4. Check that the volume type is in the list
            5. Check that no Error messages present
            6. Delete the volume type
            7. Check that the volume type is absent in the list
            8. Check that no Error messages present
        """
        volume_types_page = self.home_pg.go_to_system_volumes_volumetypespage()

        volume_types_page.create_volume_type(self.VOLUME_TYPE_NAME)

        self.assertTrue(
            volume_types_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volume_types_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volume_types_page.is_volume_type_present(
            self.VOLUME_TYPE_NAME))

        volume_types_page.delete_volume_type(self.VOLUME_TYPE_NAME)

        self.assertTrue(
            volume_types_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volume_types_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volume_types_page.is_volume_type_deleted(
            self.VOLUME_TYPE_NAME))
