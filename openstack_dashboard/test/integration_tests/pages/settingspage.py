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
from openstack_dashboard.test.integration_tests.pages import changepasswordpage
from openstack_dashboard.test.integration_tests.pages import pageobject


class SettingsPage(basepage.BasePage):
    DEFAULT_LANGUAGE = "en"
    DEFAULT_TIMEZONE = "UTC"
    DEFAULT_PAGESIZE = "20"
    DEFAULT_SETTINGS = {
        "language": DEFAULT_LANGUAGE,
        "timezone": DEFAULT_TIMEZONE,
        "pagesize": DEFAULT_PAGESIZE
    }

    _change_password_tab_locator = (by.By.CSS_SELECTOR,
                                    'a[href*="/settings/password/"]')

    def __init__(self, driver, conf):
        super(SettingsPage, self).__init__(driver, conf)
        self._page_title = "User Settings"

    @property
    def modal(self):
        return SettingsPage.UserSettingsModal(self.driver, self.conf)

    @property
    def changepassword(self):
        return changepasswordpage.ChangePasswordPage(self.driver, self.conf)

    @property
    def change_password_tab(self):
        return self.get_element(*self._change_password_tab_locator)

    def change_language(self, lang=DEFAULT_LANGUAGE):
        self.select_dropdown_by_value(lang,
                                      self.modal.language_selection)
        self.modal.click_on_save_button()

    def change_timezone(self, timezone=DEFAULT_TIMEZONE):
        self.select_dropdown_by_value(timezone,
                                      self.modal.timezone_selection)
        self.modal.click_on_save_button()

    def change_pagesize(self, size=DEFAULT_PAGESIZE):
        self.fill_field_element(size, self.modal.pagesize)
        self.modal.click_on_save_button()

    def return_to_default_settings(self):
        self.change_language()
        self.change_timezone()
        self.change_pagesize()

    def go_to_change_password_page(self):
        self.change_password_tab.click()
        return changepasswordpage.ChangePasswordPage(self.driver, self.conf)

    class UserSettingsModal(pageobject.PageObject):
        _language_selection_locator = (by.By.CSS_SELECTOR,
                                       'select#id_language')
        _timezone_selection_locator = (by.By.CSS_SELECTOR,
                                       'select#id_timezone')
        _items_per_page_input_locator = (by.By.CSS_SELECTOR,
                                         'input#id_pagesize')
        _save_submit_button_locator = (by.By.CSS_SELECTOR,
                                       'div.modal-footer button.btn')

        @property
        def language_selection(self):
            return self.get_element(*self._language_selection_locator)

        @property
        def timezone_selection(self):
            return self.get_element(*self._timezone_selection_locator)

        @property
        def pagesize(self):
            return self.get_element(*self._items_per_page_input_locator)

        @property
        def save_button(self):
            return self.get_element(*self._save_submit_button_locator)

        def click_on_save_button(self):
            self.save_button.click()
