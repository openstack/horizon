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

    def _reset_password(self):
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()
        passwordchange_page.reset_to_default_password(NEW_PASSWORD)

    def _login(self):
        self.login_pg.login()
        self.assertTrue(self.home_pg.is_logged_in,
                        "Failed to login with default password")

    def test_password_change(self):
        """Changes the password, verifies it was indeed changed and resets to
        default password.
        """
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()

        try:
            passwordchange_page.change_password(self.TEST_PASSWORD,
                                                NEW_PASSWORD)

            self.home_pg = self.login_pg.login(user=self.TEST_USER_NAME,
                                               password=NEW_PASSWORD)
            self.assertTrue(self.home_pg.is_logged_in,
                            "Failed to login with new password")
        finally:
            self._reset_password()
            self._login()

    def test_show_message_after_logout(self):
        """Ensure an informational message is shown on the login page after the
        user is logged out.
        """
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()

        try:
            passwordchange_page.change_password(self.TEST_PASSWORD,
                                                NEW_PASSWORD)
            self.assertTrue(
                self.login_pg.is_logout_reason_displayed(),
                "The logout reason message was not found on the login page")
        finally:
            self.login_pg.login(user=self.TEST_USER_NAME,
                                password=NEW_PASSWORD)
            self._reset_password()
            self._login()
