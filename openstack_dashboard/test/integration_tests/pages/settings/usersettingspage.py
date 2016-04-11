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

from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.pages.settings import \
    changepasswordpage
from openstack_dashboard.test.integration_tests.regions import forms


class UsersettingsPage(basepage.BaseNavigationPage):
    DEFAULT_LANGUAGE = "en"
    DEFAULT_TIMEZONE = "UTC"
    DEFAULT_PAGESIZE = "20"
    DEFAULT_LOGLINES = "35"
    DEFAULT_SETTINGS = {
        "language": DEFAULT_LANGUAGE,
        "timezone": DEFAULT_TIMEZONE,
        "pagesize": DEFAULT_PAGESIZE,
        "loglines": DEFAULT_LOGLINES
    }

    SETTINGS_FORM_FIELDS = (
        "language", "timezone", "pagesize", "instance_log_length")

    _settings_form_locator = (by.By.ID, 'user_settings_modal')
    _change_password_tab_locator = (by.By.CSS_SELECTOR,
                                    'a[href*="/settings/password/"]')

    def __init__(self, driver, conf):
        super(UsersettingsPage, self).__init__(driver, conf)
        self._page_title = "User Settings"

    @property
    def settings_form(self):
        src_elem = self._get_element(*self._settings_form_locator)
        return forms.FormRegion(
            self.driver, self.conf, src_elem=src_elem,
            field_mappings=self.SETTINGS_FORM_FIELDS)

    @property
    def changepassword(self):
        return changepasswordpage.ChangePasswordPage(self.driver, self.conf)

    @property
    def change_password_tab(self):
        return self._get_element(*self._change_password_tab_locator)

    def change_language(self, lang=DEFAULT_LANGUAGE):
        self.settings_form.language.value = lang
        self.settings_form.submit()

    def change_timezone(self, timezone=DEFAULT_TIMEZONE):
        self.settings_form.timezone.value = timezone
        self.settings_form.submit()

    def change_pagesize(self, size=DEFAULT_PAGESIZE):
        self.settings_form.pagesize.value = size
        self.settings_form.submit()

    def change_loglines(self, lines=DEFAULT_LOGLINES):
        self.settings_form.instance_log_length.value = lines
        self.settings_form.submit()

    def return_to_default_settings(self):
        self.change_language()
        self.change_timezone()
        self.change_pagesize()
        self.change_loglines()

    def go_to_change_password_page(self):
        self.change_password_tab.click()
        return changepasswordpage.ChangePasswordPage(self.driver, self.conf)
