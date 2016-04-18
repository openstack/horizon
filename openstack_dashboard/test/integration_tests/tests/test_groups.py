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


class TestGroup(helpers.AdminTestCase):
    """Checks if the user is able to create/delete/edit groups"""

    def setUp(self):
        super(TestGroup, self).setUp()
        self.groups_page = self.home_pg.go_to_identity_groupspage()

    @property
    def group_name(self):
        return helpers.gen_random_resource_name("group")

    @property
    def group_description(self):
        return helpers.gen_random_resource_name('description')

    def _test_create_group(self, group_name, group_desc=None):
        self.groups_page.create_group(name=group_name, description=group_desc)
        self.assertTrue(
            self.groups_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.groups_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(self.groups_page.is_group_present(group_name))

    def _test_delete_group(self, group_name):
        self.groups_page.delete_group(name=group_name)
        self.assertTrue(
            self.groups_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.groups_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(self.groups_page.is_group_present(group_name))

    def test_create_delete_group(self):
        """Tests ability to create and delete a group"""
        group_name = self.group_name
        self._test_create_group(group_name)
        self._test_delete_group(group_name)

    def test_edit_group(self):
        """Tests ability to edit group name and description"""
        group_name = self.group_name
        self._test_create_group(group_name)
        new_group_name = self.group_name
        new_group_desc = self.group_description
        self.groups_page.edit_group(group_name, new_group_name, new_group_desc)
        self.assertTrue(
            self.groups_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.groups_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(self.groups_page.is_group_present(new_group_name))
        self._test_delete_group(new_group_name)
