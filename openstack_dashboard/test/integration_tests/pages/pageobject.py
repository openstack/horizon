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

#TODO(dkorn): add handle_popup method

import selenium.common.exceptions as Exceptions
import selenium.webdriver.support.ui as Support


class PageObject(object):
    """Base class for page objects."""
    def __init__(self, driver, conf):
        """Constructor"""
        self.driver = driver
        self.conf = conf
        self.login_url = self.conf.dashboard.login_url
        self._page_title = None

    @property
    def page_title(self):
        return self.driver.title

    def is_the_current_page(self):
        if self._page_title not in self.page_title:
            raise AssertionError(
                "Expected page title: %s. Actual page title: %s"
                % (self._page_title, self.page_title))
        return True

    def get_url_current_page(self):
        return self.driver.current_url()

    def close_window(self):
        return self.driver.close()

    def go_to_login_page(self):
        self.driver.get(self.login_url)
        self.is_the_current_page()

    def is_element_present(self, *locator):
        try:
            self.driver.find_element(*locator)
            return True
        except Exceptions.NoSuchElementException:
            return False

    def is_element_visible(self, *locator):
        try:
            return self.driver.find_element(*locator).is_displayed()
        except (Exceptions.NoSuchElementException,
                Exceptions.ElementNotVisibleException):
            return False

    def return_to_previous_page(self):
        self.driver.back()

    def get_element(self, *element):
        return self.driver.find_element(*element)

    def fill_field_element(self, data, field_element):
        field_element.clear()
        field_element.send_keys(data)
        return field_element

    def fill_field_by_locator(self, data, *locator):
        field_element = self.get_element(*locator)
        self.fill_field_element(data, field_element)
        return field_element

    def select_dropdown(self, value, *element):
        select = Support.Select(self.driver.find_element(*element))
        select.select_by_visible_text(value)

    def select_dropdown_by_value(self, value, *element):
        select = Support.Select(self.driver.find_element(*element))
        select.select_by_value(value)
