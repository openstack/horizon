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

    _heading_locator = (by.By.CSS_SELECTOR, "div.page-header > h2")

    @property
    def heading(self):
        return self.get_element(*self._heading_locator)

    @property
    def topbar(self):
        return BasePage.TopBarRegion(self.driver, self.conf)

    @property
    def is_logged_in(self):
        return self.topbar.is_logged_in

    @property
    def navaccordion(self):
        return BasePage.NavigationAccordionRegion(self.driver, self.conf)

    def go_to_login_page(self):
        self.driver.get(self.login_url)

    def go_to_home_page(self):
        self.topbar.brand.click()

    def log_out(self):
        self.topbar.logout_link.click()
        return self.go_to_login_page()

    def go_to_help_page(self):
        self.topbar.user_dropdown_menu.click()
        self.topbar.help_link.click()

    class TopBarRegion(pageobject.PageObject):
        _user_indicator_locator = (by.By.CSS_SELECTOR,
                                   '#profile_editor_switcher > '
                                   'a.dropdown-toggle > div')
        _user_dropdown_menu_locator = (by.By.CSS_SELECTOR,
                                       '#profile_editor_switcher >'
                                       ' a.dropdown-toggle')
        _settings_link_locator = (by.By.CSS_SELECTOR,
                                  'a[href*="/settings/"]')
        _help_link_locator = (by.By.CSS_SELECTOR,
                              'ul#editor_list li:nth-of-type(3) > a')
        _logout_link_locator = (by.By.CSS_SELECTOR,
                                'a[href*="/auth/logout/"]')
        _openstack_brand_locator = (by.By.CSS_SELECTOR, 'a[href*="/home/"]')

        @property
        def user(self):
            return self.get_element(*self._user_indicator_locator)

        @property
        def brand(self):
            return self.get_element(*self._openstack_brand_locator)

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

    class NavigationAccordionRegion(pageobject.PageObject):
        # TODO(sunlim): change Xpath to CSS
        _project_bar_locator = (
            by.By.XPATH,
            ".//*[@id='main_content']//div[contains(text(),'Project')]")

        _project_access_security_locator = (
            by.By.CSS_SELECTOR, 'a[href*="/project/access_and_security/"]')

        @property
        def project_bar(self):
            return self.get_element(*self._project_bar_locator)

        def _click_on_project_bar(self):
            self.project_bar.click()

        @property
        def access_security(self):
            return self.get_element(*self._project_access_security_locator)

        def _click_on_access_security(self):
            self.access_security.click()
