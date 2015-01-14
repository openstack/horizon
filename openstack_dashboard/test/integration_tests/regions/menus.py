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


class CannotClickMenuItemException(Exception):
    pass


class NavigationAccordionRegion(baseregion.BaseRegion):
    """Navigation menu located in the left."""
    _project_access_security_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/project/access_and_security/"]')
    _settings_change_password_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/settings/password//"]')
    _project_bar_locator = (by.By.XPATH,
                            ".//*[@id='main_content']//div[contains(text(),"
                            "'Project')]")

    MAX_MENU_ITEM_CLICK_TRIES = 100

    @property
    def project_bar(self):
        return self._get_element(*self._project_bar_locator)

    _first_level_item_selected_locator = (by.By.CSS_SELECTOR, 'dt.active')
    _second_level_item_selected_locator = (by.By.CSS_SELECTOR, 'h4.active')

    _first_level_item_xpath_template = '//dt[contains(text(),\'%s\')]'
    _second_level_item_xpath_template = '//h4[contains(text(),\'%s\')]'
    _third_level_item_xpath_template = '//li/a[text()=\'%s\']'

    def _get_first_level_item_locator(self, text):
        return (by.By.XPATH,
                self._first_level_item_xpath_template % text)

    def _get_second_level_item_locator(self, text):
        return (by.By.XPATH,
                self._second_level_item_xpath_template % text)

    def _get_third_level_item_locator(self, text):
        return (by.By.XPATH,
                self._third_level_item_xpath_template % text)

    def get_first_level_selected_item(self):
        if self._is_element_present(*self._first_level_item_selected_locator):
            return self._get_element(*self._first_level_item_selected_locator)
        else:
            return None

    def get_second_level_selected_item(self):
        if self._is_element_present(*self._second_level_item_selected_locator):
            return self._get_element(*self._second_level_item_selected_locator)
        else:
            return None

    @property
    def access_security(self):
        return self._get_element(*self._project_access_security_locator)

    @property
    def change_password(self):
        return self._get_element(*self._settings_change_password_locator)

    def _click_menu_item(self, text, loc_craft_func, get_selected_func=None):
        """Click on menu item if not selected.

        Menu animation that visualize transition from one selection to
        another take some time - if clicked on item during this animation
        nothing happens, therefore it is necessary to do this in a loop.
        """

        if not get_selected_func:
            self._click_item(text, loc_craft_func)
        else:
            for _ in xrange(self.MAX_MENU_ITEM_CLICK_TRIES):
                selected_item = get_selected_func()
                if selected_item and text == selected_item.text:
                    break

                # In case different item was chosen previously scroll it,
                # because otherwise selenium will complain with
                # MoveTargetOutOfBoundsException
                if selected_item:
                    selected_item.click()
                self._click_item(text, loc_craft_func)
            else:

                # One should never get in here,
                # this suggest that something is wrong
                raise CannotClickMenuItemException()

    def _click_item(self, text, loc_craft_func):
        """Click on item."""
        item_locator = loc_craft_func(text)
        item = self._get_element(*item_locator)
        item.click()

    def click_on_menu_items(self, first_level=None,
                            second_level=None,
                            third_level=None):
        if first_level:
            self._click_menu_item(first_level,
                                  self._get_first_level_item_locator,
                                  self.get_first_level_selected_item)
        if second_level:
            self._click_menu_item(second_level,
                                  self._get_second_level_item_locator,
                                  self.get_second_level_selected_item)

        # it is not checked that third level item is clicked because behaviour
        # of the third menu layer is buggy => always click
        if third_level:
            self._click_menu_item(third_level,
                                  self._get_third_level_item_locator)


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


class TabbedMenuRegion(baseregion.BaseRegion):

    _tab_locator = (by.By.CSS_SELECTOR, 'li')
    _default_src_locator = (by.By.CSS_SELECTOR, 'ul.nav-tabs')

    def switch_to(self, index=0):
        self._get_elements(*self._tab_locator)[index].click()
