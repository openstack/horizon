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
import selenium.common.exceptions as Exceptions
import selenium.webdriver.support.ui as Support
from selenium.webdriver.support import wait
import unittest


class BaseWebObject(unittest.TestCase):
    """Base class for all web objects."""
    def __init__(self, driver, conf):
        self.driver = driver
        self.conf = conf
        self.explicit_wait = self.conf.selenium.explicit_wait

    def _is_element_present(self, *locator):
        try:
            self._get_element(*locator)
            return True
        except Exceptions.NoSuchElementException:
            return False

    def _is_element_visible(self, *locator):
        try:
            return self._get_element(*locator).is_displayed()
        except (Exceptions.NoSuchElementException,
                Exceptions.ElementNotVisibleException):
            return False

    def _is_element_displayed(self, element):
        try:
            return element.is_displayed()
        except Exception:
            return False

    def _is_text_visible(self, element, text):
        try:
            return element.text == text
        except Exception:
            return False

    def _get_element(self, *locator):
        return self.driver.find_element(*locator)

    def _get_elements(self, *locator):
        return self.driver.find_elements(*locator)

    def _fill_field_element(self, data, field_element):
        field_element.clear()
        field_element.send_keys(data)
        return field_element

    def _select_dropdown(self, value, element):
        select = Support.Select(element)
        select.select_by_visible_text(value)

    def _select_dropdown_by_value(self, value, element):
        select = Support.Select(element)
        select.select_by_value(value)

    def _turn_off_implicit_wait(self):
        self.driver.implicitly_wait(0)

    def _turn_on_implicit_wait(self):
        self.driver.implicitly_wait(self.conf.selenium.page_timeout)

    def _wait_until(self, predicate, timeout=None, poll_frequency=0.5):
        """Wait until the value returned by predicate is not False or
        the timeout is elapsed.
        'predicate' takes the driver as argument.
        """
        if not timeout:
            timeout = self.explicit_wait
        wait.WebDriverWait(self.driver, timeout, poll_frequency).until(
            predicate)

    def _wait_till_text_present_in_element(self, element, text, timeout=None):
        self._wait_until(lambda x: self._is_text_visible(element, text),
                         timeout)

    def _wait_till_element_visible(self, element, timeout=None):
        self._wait_until(lambda x: self._is_element_displayed(element),
                         timeout)

    def _wait_till_element_disappears(self, element, timeout=None):
        self._wait_until(lambda x: self._is_element_displayed(element),
                         timeout)
