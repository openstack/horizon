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


class TestFlavors(helpers.AdminTestCase):
    FLAVOR_NAME = helpers.gen_random_resource_name("flavor")

    def test_flavor_create(self):
        """tests the flavor creation and deletion functionalities:
        * creates a new flavor
        * verifies the flavor appears in the flavors table
        * deletes the newly created flavor
        * verifies the flavor does not appear in the table after deletion
        """

        flavors_page = self.home_pg.go_to_system_flavorspage()

        flavors_page.create_flavor(name=self.FLAVOR_NAME, vcpus=1, ram=1024,
                                   root_disk=20, ephemeral_disk=0,
                                   swap_disk=0)
        self.assertTrue(
            flavors_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(flavors_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(flavors_page.is_flavor_present(self.FLAVOR_NAME))

        flavors_page.delete_flavor(self.FLAVOR_NAME)
        self.assertTrue(
            flavors_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(flavors_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(flavors_page.is_flavor_present(self.FLAVOR_NAME))
