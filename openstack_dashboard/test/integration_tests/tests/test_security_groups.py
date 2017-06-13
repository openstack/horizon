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

import random

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestSecuritygroup(helpers.TestCase):
    SEC_GROUP_NAME = helpers.gen_random_resource_name("securitygroup")
    RULE_PORT = str(random.randint(9000, 9999))

    @property
    def securitygroup_page(self):
        return self.home_pg.\
            go_to_compute_accessandsecurity_securitygroupspage()

    def _create_securitygroup(self):
        page = self.securitygroup_page
        page.create_securitygroup(self.SEC_GROUP_NAME)
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(page.is_securitygroup_present(self.SEC_GROUP_NAME))

    def _delete_securitygroup(self):
        page = self.securitygroup_page
        page.delete_securitygroup(self.SEC_GROUP_NAME)
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(page.is_securitygroup_present(self.SEC_GROUP_NAME))

    def _add_rule(self):
        page = self.securitygroup_page
        page = page.go_to_manage_rules(self.SEC_GROUP_NAME)
        page.create_rule(self.RULE_PORT)
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertTrue(page.is_port_present(self.RULE_PORT))

    def _delete_rule_by_table_action(self):
        page = self.securitygroup_page
        page = page.go_to_manage_rules(self.SEC_GROUP_NAME)
        page.delete_rules(self.RULE_PORT)
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(page.is_port_present(self.RULE_PORT))

    def _delete_rule_by_row_action(self):
        page = self.securitygroup_page
        page = page.go_to_manage_rules(self.SEC_GROUP_NAME)
        page.delete_rule(self.RULE_PORT)
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(page.is_port_present(self.RULE_PORT))

    def test_securitygroup_create_delete(self):
        """tests the security group creation and deletion functionalities:

        * creates a new security group
        * verifies the security group appears in the security groups table
        * deletes the newly created security group
        * verifies the security group does not appear in the table after
          deletion
        """
        self._create_securitygroup()
        self._delete_securitygroup()

    def test_managerules_create_delete_by_row(self):
        """tests the manage rules creation and deletion functionalities:

        * create a new security group
        * verifies the security group appears in the security groups table
        * creates a new rule
        * verifies the rule appears in the rules table
        * delete the newly created rule
        * verifies the rule does not appear in the table after deletion
        * deletes the newly created security group
        * verifies the security group does not appear in the table after
          deletion
        """
        self._create_securitygroup()
        self._add_rule()
        self._delete_rule_by_row_action()
        self._delete_securitygroup()

    def test_managerules_create_delete_by_table(self):
        """tests the manage rules creation and deletion functionalities:

        * create a new security group
        * verifies the security group appears in the security groups table
        * creates a new rule
        * verifies the rule appears in the rules table
        * delete the newly created rule
        * verifies the rule does not appear in the table after deletion
        * deletes the newly created security group
        * verifies the security group does not appear in the table after
          deletion
        """
        self._create_securitygroup()
        self._add_rule()
        self._delete_rule_by_table_action()
        self._delete_securitygroup()
