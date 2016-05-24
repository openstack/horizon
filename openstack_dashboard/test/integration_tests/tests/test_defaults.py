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


class TestDefaults(helpers.AdminTestCase):

    def setUp(self):
        super(TestDefaults, self).setUp()
        self.defaults_page = self.home_pg.go_to_system_defaultspage()
        self.add_up = random.randint(1, 10)

    def test_update_defaults(self):
        """Tests the Update Default Quotas functionality:
        1) Login as Admin and go to Admin > System > Defaults
        2) Updates default Quotas by adding a random number between 1 and 10
        3) Verifies that the updated values are present in the
           Quota Defaults table
        """
        default_quota_values = self.defaults_page.quota_values
        self.defaults_page.update_defaults(self.add_up)

        self.assertTrue(
            self.defaults_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.defaults_page.find_message_and_dismiss(messages.ERROR))

        self.assertTrue(len(default_quota_values) > 0)

        for quota_name in default_quota_values:
            self.assertTrue(
                self.defaults_page.is_quota_a_match(
                    quota_name,
                    default_quota_values[quota_name] + self.add_up
                ))
