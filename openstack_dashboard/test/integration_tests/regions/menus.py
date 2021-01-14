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
import time

from selenium.common import exceptions
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.regions import baseregion


class NavigationAccordionRegion(baseregion.BaseRegion):
    """Navigation menu located in the left."""
    _project_security_groups_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/project/security_groups/"]')
    _project_key_pairs_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/project/key_pairs/"]')
    _settings_change_password_locator = (
        by.By.CSS_SELECTOR, 'a[href*="/settings/password//"]')
    _project_bar_locator = (by.By.XPATH,
                            ".//*[@id='main_content']//div[contains(text(),"
                            "'Project')]")

    @property
    def project_bar(self):
        return self._get_element(*self._project_bar_locator)

    _first_level_item_selected_locator = (
        by.By.CSS_SELECTOR, '.panel.openstack-dashboard > a:not(.collapsed)')
    _second_level_item_selected_locator = (
        by.By.CSS_SELECTOR, '.panel.openstack-panel-group > a:not(.collapsed)')

    _first_level_item_xpath_template = (
        "//li[contains(concat('', @class, ''), 'panel openstack-dashboard') "
        "and contains(., '%s')]/a")
    _second_level_item_xpath_template = (
        "//ul[contains(@class, 'in')]//li[contains(@class, "
        "'panel openstack-panel-group') and contains(., '%s')]/a")
    _third_level_item_xpath_template = (
        "//ul[contains(@class, 'in')]//a[contains(concat('', @class, ''),"
        "'list-group-item openstack-panel') and contains(., '%s')]")

    _parent_item_locator = (by.By.XPATH, '..')
    _menu_list_locator = (by.By.CSS_SELECTOR, 'a')
    _expanded_menu_class = ""
    _transitioning_menu_class = 'collapsing'
    _form_body_locator = (by.By.CSS_SELECTOR, 'body')

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
    def get_form_body(self):
        return self._get_element(*self._form_body_locator)

    @property
    def security_groups(self):
        return self._get_element(*self._project_security_groups_locator)

    @property
    def key_pairs(self):
        return self._get_element(*self._project_key_pairs_locator)

    @property
    def change_password(self):
        return self._get_element(*self._settings_change_password_locator)

    def _wait_until_transition_ends(self, item, to_be_expanded=False):
        def predicate(d):
            classes = item.get_attribute('class')
            if to_be_expanded:
                status = self._expanded_menu_class == classes
            else:
                status = self._expanded_menu_class is not classes
            return status and self._transitioning_menu_class not in classes
        self._wait_until(predicate)

    def _wait_until_modal_dialog_close(self):
        def predicate(d):
            classes = self.get_form_body.get_attribute('class')
            return classes and "modal-open" not in classes
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
        self._wait_until_modal_dialog_close()
        if get_selected_func is not None:
            selected_item = get_selected_func()
            if selected_item:
                if text != selected_item.text and selected_item.text:
                    # In case different item was chosen previously, collapse
                    # it. Otherwise selenium will complain with
                    # MoveTargetOutOfBoundsException
                    selected_item.click()
                    time.sleep(1)
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
    _dropdown_locator = (by.By.CSS_SELECTOR, '.dropdown > a')
    _active_cls = 'dropdown-toggle'

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
            dropdown = self._get_element(*self._dropdown_locator)

            # NOTE(tsufiev): there is an issue with clicking dropdowns too fast
            # after page has been loaded - the Bootstrap constructors haven't
            # completed yet, so the dropdown never opens in that case. Avoid
            # this by waiting for a specific class to appear, which is set in
            # horizon.selenium.js for dropdowns after a timeout passes
            def predicate(d):
                classes = dropdown.get_attribute('class').split()
                return self._active_cls in classes
            self._wait_until(predicate)

            dropdown.click()
            self._wait_till_element_visible(self._menu_container_locator)


class UserDropDownMenuRegion(DropDownMenuRegion):
    """Drop down menu located in the right side of the topbar.

    This menu contains links to settings and help.
    """
    _settings_link_locator = (by.By.CSS_SELECTOR,
                              'a[href*="/settings/"]')
    _help_link_locator = (by.By.CSS_SELECTOR,
                          'ul#editor_list li:nth-of-type(2) > a')
    _logout_link_locator = (by.By.CSS_SELECTOR,
                            'a[href*="/auth/logout/"]')

    def _theme_picker_locator(self, theme_name):
        return (by.By.CSS_SELECTOR,
                '.theme-picker-item[data-theme="%s"]' % theme_name)

    @property
    def settings_link(self):
        return self._get_element(*self._settings_link_locator)

    @property
    def help_link(self):
        return self._get_element(*self._help_link_locator)

    @property
    def logout_link(self):
        return self._get_element(*self._logout_link_locator)

    def theme_picker_link(self, theme_name):
        return self._get_element(*self._theme_picker_locator(theme_name))

    def click_on_settings(self):
        self.open()
        self.settings_link.click()

    def click_on_help(self):
        self.open()
        self.help_link.click()

    def choose_theme(self, theme_name):
        self.open()
        self.theme_picker_link(theme_name).click()

    def click_on_logout(self):
        self.open()
        self.logout_link.click()


class TabbedMenuRegion(baseregion.BaseRegion):

    _tab_locator = (by.By.CSS_SELECTOR, 'li > a')
    _default_src_locator = (by.By.CSS_SELECTOR, 'div > .nav.nav-pills')

    def switch_to(self, index=0):
        self._get_elements(*self._tab_locator)[index].click()


class WizardMenuRegion(baseregion.BaseRegion):

    _step_locator = (by.By.CSS_SELECTOR, 'li > a')
    _default_src_locator = (by.By.CSS_SELECTOR, 'div > .nav.nav-pills')

    def switch_to(self, index=0):
        self._get_elements(*self._step_locator)[index].click()


class ProjectDropDownRegion(DropDownMenuRegion):
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


class MembershipMenuRegion(baseregion.BaseRegion):
    _available_members_locator = (
        by.By.CSS_SELECTOR, 'ul.available_members > ul.btn-group')

    _allocated_members_locator = (
        by.By.CSS_SELECTOR, 'ul.members > ul.btn-group')

    _add_remove_member_sublocator = (
        by.By.CSS_SELECTOR, 'li > a[href="#add_remove"]')

    _member_name_sublocator = (
        by.By.CSS_SELECTOR, 'li.member > span.display_name')

    _member_roles_widget_sublocator = (by.By.CSS_SELECTOR, 'li.role_options')

    _member_roles_widget_open_subsublocator = (by.By.CSS_SELECTOR, 'a.btn')

    _member_roles_widget_roles_subsublocator = (
        by.By.CSS_SELECTOR, 'ul.role_dropdown > li')

    def _get_member_name(self, element):
        return element.find_element(*self._member_name_sublocator).text

    @property
    def available_members(self):
        return {self._get_member_name(el): el for el in
                self._get_elements(*self._available_members_locator)}

    @property
    def allocated_members(self):
        return {self._get_member_name(el): el for el in
                self._get_elements(*self._allocated_members_locator)}

    def allocate_member(self, name, available_members=None):
        # NOTE(tsufiev): available_members here (and allocated_members below)
        # are meant to be used for performance optimization to reduce the
        # amount of calls to selenium by reusing still valid element reference
        if available_members is None:
            available_members = self.available_members

        available_members[name].find_element(
            *self._add_remove_member_sublocator).click()

    def deallocate_member(self, name, allocated_members=None):
        if allocated_members is None:
            allocated_members = self.allocated_members

        allocated_members[name].find_element(
            *self._add_remove_member_sublocator).click()

    def _get_member_roles_widget(self, name, allocated_members=None):
        if allocated_members is None:
            allocated_members = self.allocated_members

        return allocated_members[name].find_element(
            *self._member_roles_widget_sublocator)

    def _get_member_all_roles(self, name, allocated_members=None):
        roles_widget = self._get_member_roles_widget(name, allocated_members)
        return roles_widget.find_elements(
            *self._member_roles_widget_roles_subsublocator)

    @staticmethod
    def _is_role_selected(role):
        return 'selected' == role.get_attribute('class')

    def get_member_available_roles(self, name, allocated_members=None,
                                   strip=True):
        roles = self._get_member_all_roles(name, allocated_members)
        return [(role.text.strip() if strip else role)
                for role in roles if not self._is_role_selected(role)]

    def get_member_allocated_roles(self, name, allocated_members=None,
                                   strip=True):
        self.open_member_roles_dropdown(name, allocated_members)
        roles = self._get_member_all_roles(name, allocated_members)
        return [(role.text.strip() if strip else role)
                for role in roles if self._is_role_selected(role)]

    def open_member_roles_dropdown(self, name, allocated_members=None):
        widget = self._get_member_roles_widget(name, allocated_members)
        button = widget.find_element(
            *self._member_roles_widget_open_subsublocator)
        button.click()

    def _switch_member_roles(self, name, roles2toggle, method,
                             allocated_members=None):
        self.open_member_roles_dropdown(name, allocated_members)
        roles = method(name, allocated_members, False)
        roles2toggle = set(roles2toggle)
        for role in roles:
            role_name = role.text.strip()
            if role_name in roles2toggle:
                role.click()
                roles2toggle.remove(role_name)
            if not roles2toggle:
                break

    def allocate_member_roles(self, name, roles2add, allocated_members=None):
        self._switch_member_roles(
            name, roles2add, self.get_member_available_roles,
            allocated_members=allocated_members)

    def deallocate_member_roles(self, name, roles2remove,
                                allocated_members=None):
        self._switch_member_roles(
            name, roles2remove, self.get_member_allocated_roles,
            allocated_members=allocated_members)


class InstanceAvailableResourceMenuRegion(baseregion.BaseRegion):
    _available_table_locator = (
        by.By.CSS_SELECTOR,
        'div.step:not(.ng-hide) div.transfer-available table')
    _available_table_row_locator = (by.By.CSS_SELECTOR,
                                    "tbody > tr.ng-scope:not(.detail-row)")
    _available_table_column_locator = (by.By.TAG_NAME, "td")
    _action_column_btn_locator = (by.By.CSS_SELECTOR,
                                  "td.actions_column button")

    def transfer_available_resource(self, resource_name):
        available_table = self._get_element(*self._available_table_locator)
        rows = available_table.find_elements(
            *self._available_table_row_locator)
        for row in rows:
            cols = row.find_elements(*self._available_table_column_locator)
            if len(cols) > 1 and self._get_column_text(cols) in resource_name:
                row_selector_btn = row.find_element(
                    *self._action_column_btn_locator)
                row_selector_btn.click()
                break

    def _get_column_text(self, cols):
        return cols[2].text.strip()


class InstanceFlavorMenuRegion(InstanceAvailableResourceMenuRegion):
    _action_column_btn_locator = (by.By.CSS_SELECTOR, "td.action-col button")

    def _get_column_text(self, cols):
        return cols[1].text.strip()
