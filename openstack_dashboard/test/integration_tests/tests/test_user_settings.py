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


class TestUserSettings(helpers.TestCase):

    def verify_user_settings_change(self, changed_settings):
        language = self.settings_page.modal.language_selection.\
            get_attribute("value")
        timezone = self.settings_page.modal.timezone_selection.\
            get_attribute("value")
        pagesize = self.settings_page.modal.pagesize.\
            get_attribute("value")

        user_settings = (("Language", changed_settings["language"], language),
                         ("Timezone", changed_settings["timezone"], timezone),
                         ("Pagesize", changed_settings["pagesize"], pagesize))

        for (setting, expected, observed) in user_settings:
            self.assertEqual(expected, observed,
                             "expected %s: %s, instead found: %s"
                             % (setting, expected, observed))

    def test_user_settings_change(self):
        """tests the user's settings options:
        * changes the system's language
        * changes the timezone
        * changes the number of items per page (page size)
        * verifies all changes were successfully executed
        """
        self.settings_page = self.home_pg.go_to_settings_page()

        self.settings_page.change_language("es")
        self.settings_page.change_timezone("Asia/Jerusalem")
        self.settings_page.change_pagesize("30")

        changed_settings = {"language": "es", "timezone": "Asia/Jerusalem",
                            "pagesize": "30"}
        self.verify_user_settings_change(changed_settings)

        self.settings_page.return_to_default_settings()
        self.verify_user_settings_change(self.settings_page.DEFAULT_SETTINGS)
