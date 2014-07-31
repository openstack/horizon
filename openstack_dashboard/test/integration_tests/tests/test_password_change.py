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

NEW_PASSWORD = "123"


class TestPasswordChange(helpers.TestCase):

    def test_password_change(self):
        """Changes the password, verifies it was indeed changed and resets to
        default password.
        """

        settings_page = self.home_pg.go_to_settings_page()
        passwordchange_page = settings_page.go_to_change_password_page()

        try:
            passwordchange_page.change_password(self.conf.identity.password,
                                                NEW_PASSWORD)

            self.home_pg = self.login_pg.login(
                user=self.conf.identity.username, password=NEW_PASSWORD)
            self.assertTrue(self.home_pg.is_logged_in,
                            "Failed to login with new password")
            settings_page = self.home_pg.go_to_settings_page()
            passwordchange_page = settings_page.go_to_change_password_page()
        finally:
            passwordchange_page.reset_to_default_password(NEW_PASSWORD)
            self.login_pg.login()
            self.assertTrue(self.home_pg.is_logged_in,
                            "Failed to login with default password")
