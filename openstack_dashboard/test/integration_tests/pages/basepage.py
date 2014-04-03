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

from openstack_dashboard.test.integration_tests.pages import pageobject


class BasePage(pageobject.PageObject):
    """Base class for all dashboard page objects."""
    @property
    def top_bar(self):
        return BasePage.TopBarRegion(self.driver, self.conf)

    @property
    def is_logged_in(self):
        return self.top_bar.is_logged_in

    def go_to_login_page(self):
        self.driver.get(self.login_url)

    def log_out(self):
        self.top_bar.logout_link.click()
        return self.go_to_login_page()

    class TopBarRegion(pageobject.PageObject):
        _user_indicator_locator = (by.By.CSS_SELECTOR, "#user_info")
        _user_dropdown_menu_locator = (by.By.CSS_SELECTOR,
                                       "#profile_editor_switcher >"
                                       " a.dropdown-toggle")
        _settings_link_locator = (by.By.CSS_SELECTOR,
                                  "a[href*='/settings/']")
        _help_link_locator = (by.By.CSS_SELECTOR,
                              "ul#editor_list li:nth-of-type(3) > a")
        _logout_link_locator = (by.By.CSS_SELECTOR,
                                "a[href*='/auth/logout/']")

        @property
        def logout_link(self):
            return self.get_element(*self._logout_link_locator)

        @property
        def user_dropdown_menu(self):
            return self.get_element(*self._user_dropdown_menu_locator)

        @property
        def settings_link(self):
            return self.get_element(*self._settings_link_locator)

        @property
        def help_link(self):
            return self.get_element(*self._help_link_locator)

        @property
        def is_logout_visible(self):
            return self.is_element_visible(*self._logout_link_locator)

        @property
        def is_logged_in(self):
            return self.is_element_visible(*self._user_indicator_locator)
