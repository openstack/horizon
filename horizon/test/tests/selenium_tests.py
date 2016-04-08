# Copyright 2012 Nebula, Inc.
#
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

from django.test.utils import override_settings

from horizon.test import helpers as test


class BrowserTests(test.SeleniumTestCase):
    def test_jasmine_legacy(self):
        self.selenium.get("%s%s" % (self.live_server_url,
                                    "/jasmine-legacy/"))
        wait = self.ui.WebDriverWait(self.selenium, 30)

        def jasmine_legacy_done(driver):
            failures = driver.find_element_by_class_name("jasmine-bar").text
            return failures

        self.assertTrue('0 failures' in wait.until(jasmine_legacy_done))


@override_settings(
    AUTHENTICATION_BACKENDS=('horizon.test.dummy_auth.backend.DummyBackend',))
class LazyLoadedTabsTests(test.SeleniumTestCase):
    tab_id = 'puppies_tabs__lazy_puppies'
    table_selector = 'div.tab-content > div#{0} > div.table_wrapper'.format(
        tab_id)
    button_selector = 'button#lazy_puppies__action_delete'
    checkbox_selector = 'td.multi_select_column input[type=checkbox]'
    select_all_selector = 'th.multi_select_column input[type=checkbox]'

    def setUp(self):
        super(LazyLoadedTabsTests, self).setUp()
        wait = self.ui.WebDriverWait(self.selenium, 120)
        self.get_element = self.selenium.find_element_by_css_selector
        self.get_elements = self.selenium.find_elements_by_css_selector

        self.log_in()
        self.selenium.get('{0}/dogs/tabs'.format(self.live_server_url))
        self.get_element('a[data-target="#{0}"]'.format(self.tab_id)).click()

        def lazy_tab_loaded(driver):
            return driver.find_element_by_css_selector(self.table_selector)
        wait.until(lazy_tab_loaded)

    def log_in(self):
        self.selenium.get("%s%s" % (self.live_server_url, '/auth/login/'))
        self.fill_field('id_username', 'user')
        self.fill_field('id_password', 'password')
        self.get_element('button[type=submit]').click()

    def fill_field(self, field_id, value):
        element = self.get_element('#' + field_id)
        element.clear()
        element.send_keys(value)

    def has_class(self, element, class_name):
        classes = element.get_attribute('class')
        return class_name in classes.split()

    def test_delete_button_is_disabled_on_empty_selection(self):
        button = self.get_element(self.button_selector)

        self.assertTrue(self.has_class(button, 'disabled'))

    def test_delete_button_is_enabled_on_selection(self):
        self.get_element(self.checkbox_selector).click()
        button = self.get_element(self.button_selector)

        self.assertFalse(self.has_class(button, 'disabled'))

    def test_select_all_checkbox_sets_on_row_checkboxes(self):
        self.get_element(self.select_all_selector).click()
        for checkbox in self.get_elements(self.checkbox_selector):
            self.assertTrue(checkbox.get_attribute('checked'))

    def test_any_unchecked_row_checkbox_unsets_select_all(self):
        select_all = self.get_element(self.select_all_selector)
        select_all.click()
        self.get_element(self.checkbox_selector).click()

        self.assertFalse(select_all.get_attribute('checked'))

    def test_every_checked_row_checkbox_set_select_all(self):
        select_all = self.get_element(self.select_all_selector)
        for checkbox in self.get_elements(self.checkbox_selector):
            checkbox.click()

        self.assertTrue(select_all.get_attribute('checked'))
