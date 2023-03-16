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


class TestAdminGroupTypes(helpers.AdminTestCase):
    GROUP_TYPE_NAME = helpers.gen_random_resource_name("group_type")

    def test_group_type_create_delete(self):
        """This test case checks create, delete group type:

        Steps:
        1. Login to Horizon Dashboard as admin user
        2. Navigate to Admin -> Volume -> Group Types page
        3. Create new group type
        4. Check that the group type is in the list
        5. Check that no Error messages present
        6. Delete the group type
        7. Check that the group type is absent in the list
        8. Check that no Error messages present
        """
        group_types_page = self.home_pg.go_to_admin_volume_grouptypespage()
        group_types_page.create_group_type(self.GROUP_TYPE_NAME)
        self.assertEqual(
            group_types_page.find_messages_and_dismiss(), {messages.SUCCESS})
        self.assertTrue(group_types_page.is_group_type_present(
            self.GROUP_TYPE_NAME))
        group_types_page.delete_group_type(self.GROUP_TYPE_NAME)
        self.assertEqual(
            group_types_page.find_messages_and_dismiss(), {messages.SUCCESS})
        self.assertTrue(group_types_page.is_group_type_deleted(
            self.GROUP_TYPE_NAME))
