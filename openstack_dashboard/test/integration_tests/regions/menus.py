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
from selenium.common import exceptions
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

    _first_level_item_selected_locator = (
        by.By.CSS_SELECTOR, 'li.openstack-dashboard.selenium-active > a')
    _second_level_item_selected_locator = (
        by.By.CSS_SELECTOR, 'li.nav-header.selenium-active > a')

    _first_level_item_xpath_template = (
        "//li[contains(concat('', @class, ''), 'openstack-dashboard') "
        "and contains(., '%s')]/a")
    _second_level_item_xpath_template = (
        "//li[contains(concat('', @class, ''), 'nav-header') "
        "and contains(., '%s')]/a")
    _third_level_item_xpath_template = (
        ".//li[contains(concat('', @class, ''), 'openstack-panel') and "
        "contains(., '%s')]/a")

    _parent_item_locator = (by.By.XPATH, '..')
    _menu_list_locator = (by.By.CSS_SELECTOR, 'ul')
    _expanded_menu_class = 'in'
    _transitioning_menu_class = 'collapsing'

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

    def _wait_until_transition_ends(self, item, to_be_expanded=False):
        def predicate(d):
            classes = item.get_attribute('class').split()
            if to_be_expanded:
                status = self._expanded_menu_class in classes
            else:
                status = self._expanded_menu_class not in classes
            return status and self._transitioning_menu_class not in classes
        self._wait_until(predicate)

    def _click_menu_item(self, text, loc_craft_func, get_selected_func=None,
                         src_elem=None):
        """Click on menu item if not selected.

        Menu animation that visualize transition from one selection to
        another take some time - if clicked on item during this animation
        nothing happens, therefore it is necessary to wait for the transition
        to complete first.

        Third-level menus are handled differently from others. First, they do
        not need to collapse other 3rd-level menu item prior to clicking them
        (because 3rd-level menus are atomic). Second, clicking them doesn't
        initiate an animated transition, hence no need to wait until it
        finishes. Also an ambiguity is possible when matching third-level menu
        items, because different dashboards have panels with the same name (for
        example Volumes/Images/Instances both at Project and Admin dashboards).
        To avoid this ambiguity, an argument `src_elem` is used. Whenever
        dashboard or a panel group is clicked, its wrapper is returned to be
        used as `src_elem` in a subsequent call for clicking third-level item.
        This way the set of panel labels being matched is restricted to the
        descendants of that particular dashboard or panel group.
        """
        is_already_within_required_item = False
        selected_item = None
        if get_selected_func is not None:
            selected_item = get_selected_func()
            if selected_item:
                if text != selected_item.text:
                    # In case different item was chosen previously, collapse
                    # it. Otherwise selenium will complain with
                    # MoveTargetOutOfBoundsException
                    selected_item.click()
                    self._wait_until_transition_ends(
                        self._get_menu_list_next_to_menu_title(selected_item))
                else:
                    is_already_within_required_item = True

        if not is_already_within_required_item:
            item = self._get_item(text, loc_craft_func, src_elem)
            item.click()
            if get_selected_func is not None:
                self._wait_until_transition_ends(
                    self._get_menu_list_next_to_menu_title(item),
                    to_be_expanded=True)
            return item
        return selected_item

    def _get_item(self, text, loc_craft_func, src_elem=None):
        item_locator = loc_craft_func(text)
        src_elem = src_elem or self.src_elem
        return src_elem.find_element(*item_locator)

    def _get_menu_list_next_to_menu_title(self, title_item):
        parent_item = title_item.find_element(*self._parent_item_locator)
        return parent_item.find_element(*self._menu_list_locator)

    def click_on_menu_items(self, first_level=None,
                            second_level=None,
                            third_level=None):
        src_elem = None
        if first_level:
            src_elem = self._click_menu_item(
                first_level,
                self._get_first_level_item_locator,
                self.get_first_level_selected_item)
        if second_level:
            src_elem = self._click_menu_item(
                second_level,
                self._get_second_level_item_locator,
                self.get_second_level_selected_item)

        if third_level:
            # NOTE(tsufiev): possible dashboard/panel group label passed as
            # `src_elem` is a sibling of <ul> with all the panels it contains.
            # So to get the panel within specified dashboard/panel group, we
            # need to traverse upwards first. When `src_elem` is not specified
            # (true for Settings pseudo-dashboard), we cannot and should not
            # go upward.
            if src_elem:
                src_elem = src_elem.find_element(*self._parent_item_locator)
            self._click_menu_item(third_level,
                                  self._get_third_level_item_locator,
                                  src_elem=src_elem)


class DropDownMenuRegion(baseregion.BaseRegion):
    """Drop down menu region."""

    _menu_container_locator = (by.By.CSS_SELECTOR, 'ul.dropdown-menu')
    _menu_items_locator = (by.By.CSS_SELECTOR,
                           'ul.dropdown-menu > li > *')
    _menu_first_child_locator = (by.By.CSS_SELECTOR,
                                 'a[data-toggle="dropdown"]')

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
            self._wait_till_element_visible(self._menu_container_locator)


class UserDropDownMenuRegion(DropDownMenuRegion):
    """Drop down menu located in the right side of the topbar,
    contains links to settings and help.
    """
    _menu_first_child_locator = (by.By.CSS_SELECTOR, '*')
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

    _tab_locator = (by.By.CSS_SELECTOR, 'a')
    _default_src_locator = (by.By.CSS_SELECTOR, '.selenium-nav-region')

    def switch_to(self, index=0):
        self._get_elements(*self._tab_locator)[index].click()


class ProjectDropDownRegion(DropDownMenuRegion):

    _menu_first_child_locator = (by.By.CSS_SELECTOR, '*')
    _menu_items_locator = (
        by.By.CSS_SELECTOR, 'ul.context-selection li > a')

    def click_on_project(self, name):
        for item in self.menu_items:
            if item.text == name:
                item.click()
                break
        else:
            raise exceptions.NoSuchElementException(
                "Not found element with text: %s" % name)
