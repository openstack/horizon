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


class TestDashboardHelp(helpers.TestCase):
    def test_dashboard_help_redirection(self):
        """Verifies Help link redirects to the right URL."""

        self.home_pg.go_to_help_page()
        self.home_pg._wait_until(lambda _: self.home_pg.is_nth_window_opened(2)
                                 )
        self.home_pg.switch_window()
        self.home_pg.is_help_page()

        self.assertIn(self.CONFIG.dashboard.help_url,
                      self.home_pg.get_url_current_page(),
                      "help link did not redirect to the right URL")

        self.home_pg.close_window()
        self.home_pg.switch_window()


class TestThemePicker(helpers.TestCase):
    DEFAULT_THEME = 'default'
    MATERIAL_THEME = 'material'

    def test_switch_to_material_theme(self):
        """Verifies that material theme is available and switchable to."""
        self.home_pg.choose_theme(self.MATERIAL_THEME)
        self.assertTrue(self.home_pg.topbar.is_material_theme_enabled)
        self.home_pg.choose_theme(self.DEFAULT_THEME)
        self.assertFalse(self.home_pg.topbar.is_material_theme_enabled)


class TestPasswordChange(helpers.TestCase):
    NEW_PASSWORD = "123"

    def _reset_password(self):
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()
        # Per unique_last_password policy, we need to do unique password reset
        # before resetting default password.
        unique_last_password_count = int(
            self.CONFIG.identity.unique_last_password_count)
        old_password = int(self.NEW_PASSWORD)
        for x in range(1, unique_last_password_count):
            new_password = old_password + 1
            passwordchange_page = self.home_pg.\
                go_to_settings_changepasswordpage()
            passwordchange_page.change_password(
                str(old_password), str(new_password))
            self.home_pg = self.login_pg.login(
                user=self.TEST_USER_NAME, password=new_password)
            old_password = new_password
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()
        passwordchange_page.reset_to_default_password(old_password)

    def _login(self):
        self.login_pg.login()
        self.assertTrue(self.home_pg.is_logged_in,
                        "Failed to login with default password")

    def test_password_change(self):
        # Changes the password, verifies it was indeed changed and
        # resets to default password.
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()

        try:
            passwordchange_page.change_password(self.TEST_PASSWORD,
                                                self.NEW_PASSWORD)

            self.home_pg = self.login_pg.login(
                user=self.TEST_USER_NAME, password=self.NEW_PASSWORD)
            self.assertTrue(self.home_pg.is_logged_in,
                            "Failed to login with new password")
        finally:
            self._reset_password()
            self._login()

    def test_show_message_after_logout(self):
        # Ensure an informational message is shown on the login page
        # after the user is logged out.
        passwordchange_page = self.home_pg.go_to_settings_changepasswordpage()

        try:
            passwordchange_page.change_password(self.TEST_PASSWORD,
                                                self.NEW_PASSWORD)
            self.assertTrue(
                self.login_pg.is_logout_reason_displayed(),
                "The logout reason message was not found on the login page")
        finally:
            self.login_pg.login(
                user=self.TEST_USER_NAME, password=self.NEW_PASSWORD)
            self._reset_password()
            self._login()


class TestUserSettings(helpers.TestCase):
    def verify_user_settings_change(self, settings_page, changed_settings):
        language = settings_page.settings_form.language.value
        timezone = settings_page.settings_form.timezone.value
        pagesize = settings_page.settings_form.pagesize.value
        loglines = settings_page.settings_form.instance_log_length.value

        user_settings = (("Language", changed_settings["language"], language),
                         ("Timezone", changed_settings["timezone"], timezone),
                         ("Pagesize", changed_settings["pagesize"],
                          pagesize), ("Loglines", changed_settings["loglines"],
                                      loglines))

        for (setting, expected, observed) in user_settings:
            self.assertEqual(
                expected, observed, "expected %s: %s, instead found: %s" %
                (setting, expected, observed))

    def test_user_settings_change(self):
        """tests the user's settings options:

        * changes the system's language
        * changes the timezone
        * changes the number of items per page (page size)
        * changes the number of log lines to be shown per instance
        * verifies all changes were successfully executed
        """
        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_language("es")
        self.assertTrue(
            settings_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            settings_page.find_message_and_dismiss(messages.ERROR))

        settings_page.change_timezone("Asia/Jerusalem")
        self.assertTrue(
            settings_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            settings_page.find_message_and_dismiss(messages.ERROR))

        settings_page.change_pagesize("30")
        self.assertTrue(
            settings_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            settings_page.find_message_and_dismiss(messages.ERROR))

        settings_page.change_loglines("50")
        self.assertTrue(
            settings_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            settings_page.find_message_and_dismiss(messages.ERROR))

        changed_settings = {
            "language": "es",
            "timezone": "Asia/Jerusalem",
            "pagesize": "30",
            "loglines": "50"
        }
        self.verify_user_settings_change(settings_page, changed_settings)

        settings_page.return_to_default_settings()
        self.verify_user_settings_change(settings_page,
                                         settings_page.DEFAULT_SETTINGS)
