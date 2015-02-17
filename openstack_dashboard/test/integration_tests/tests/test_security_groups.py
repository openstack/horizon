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


class TestSecuritygroup(helpers.TestCase):
    SECURITYGROUP_NAME = helpers.gen_random_resource_name("securitygroup")

    def test_securitygroup_create_delete(self):
        """tests the security group creation and deletion functionalities:
        * creates a new security group
        * verifies the security group appears in the security groups table
        * deletes the newly created security group
        * verifies the security group does not appear in the table after
        deletion
        """

        securitygroups_page = \
            self.home_pg.go_to_compute_accessandsecurity_securitygroupspage()

        securitygroups_page.create_securitygroup(self.SECURITYGROUP_NAME)
        self.assertTrue(securitygroups_page.is_securitygroup_present(
            self.SECURITYGROUP_NAME))

        securitygroups_page.delete_securitygroup(self.SECURITYGROUP_NAME)
        self.assertFalse(securitygroups_page.is_securitygroup_present(
            self.SECURITYGROUP_NAME))
