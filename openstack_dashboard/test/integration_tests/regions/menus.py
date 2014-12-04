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

from openstack_dashboard.test.integration_tests.regions import baseregion


class NavigationAccordionRegion(baseregion.BaseRegion):
    """Navigation menu located in the left."""
    _project_access_security_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/project/access_and_security/"]')
    _settings_change_password_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/settings/password//"]')
    _project_bar_locator = (by.By.XPATH,
                            ".//*[@id='main_content']//div[contains(text(),"
                            "'Project')]")

    @property
    def project_bar(self):
        return self._get_element(*self._project_bar_locator)

    @property
    def access_security(self):
        return self._get_element(*self._project_access_security_locator)

    @property
    def change_password(self):
        return self._get_element(*self._settings_change_password_locator)


class DropDownMenuRegion(baseregion.BaseRegion):
    """Drop down menu region."""

    _menu_items_locator = (by.By.CSS_SELECTOR, 'ul.dropdown-menu > li > *')
    _menu_first_child_locator = (by.By.CSS_SELECTOR, '*')

    @property
    def menu_items(self):
        self.open()
        menu_items = self._get_elements(*self._menu_items_locator)
        return menu_items

    def is_open(self):
        """Returns True if drop down menu is open, otherwise False."""
        return "open" in self.src_elem.get_attribute('class')

    def open(self):
        """Opens menu by clicking on the first child of the source element."""
        if self.is_open() is False:
            self._get_element(*self._menu_first_child_locator).click()


class UserDropDownMenuRegion(DropDownMenuRegion):
    """Drop down menu located in the right side of the topbar,
    contains links to settings and help.
    """
    _settings_link_locator = (by.By.CSS_SELECTOR,
                              'a[href*="/settings/"]')
    _help_link_locator = (by.By.CSS_SELECTOR,
                          'ul#editor_list li:nth-of-type(2) > a')
    _logout_link_locator = (by.By.CSS_SELECTOR,
                            'a[href*="/auth/logout/"]')

    @property
    def settings_link(self):
        return self._get_element(*self._settings_link_locator)

    @property
    def help_link(self):
        return self._get_element(*self._help_link_locator)

    @property
    def logout_link(self):
        return self._get_element(*self._logout_link_locator)

    def click_on_settings(self):
        self.open()
        self.settings_link.click()

    def click_on_help(self):
        self.open()
        self.help_link.click()

    def click_on_logout(self):
        self.open()
        self.logout_link.click()
