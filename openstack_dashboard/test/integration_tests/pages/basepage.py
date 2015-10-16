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

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import navigation
from openstack_dashboard.test.integration_tests.pages import pageobject
from openstack_dashboard.test.integration_tests.regions import bars
from openstack_dashboard.test.integration_tests.regions import menus
from openstack_dashboard.test.integration_tests.regions import messages


class BasePage(pageobject.PageObject):
    """Base class for all dashboard page objects."""

    _heading_locator = (by.By.CSS_SELECTOR, 'div.page-header > h2')
    _error_msg_locator = (by.By.CSS_SELECTOR, 'div.alert-danger.alert')
    _spinner_locator = (by.By.CSS_SELECTOR, 'div.modal-backdrop')
    _message_locator = (by.By.CSS_SELECTOR, 'div.alert-success')

    @property
    def heading(self):
        return self._get_element(*self._heading_locator)

    @property
    def topbar(self):
        return bars.TopBarRegion(self.driver, self.conf)

    @property
    def is_logged_in(self):
        return self.topbar.is_logged_in

    @property
    def navaccordion(self):
        return menus.NavigationAccordionRegion(self.driver, self.conf)

    @property
    def error_message(self):
        src_elem = self._get_element(*self._error_msg_locator)
        return messages.ErrorMessageRegion(self.driver, self.conf, src_elem)

    def is_error_message_present(self):
        return self._is_element_present(*self._error_msg_locator)

    def go_to_login_page(self):
        self.driver.get(self.login_url)

    def go_to_home_page(self):
        self.topbar.brand.click()

    def log_out(self):
        self.topbar.user_dropdown_menu.click_on_logout()
        return self.go_to_login_page()

    def go_to_help_page(self):
        self.topbar.user_dropdown_menu.click_on_help()

    def wait_till_element_disappears(self, element_getter):
        try:
            self._turn_off_implicit_wait()
            self._wait_till_element_disappears(element_getter())
        except NoSuchElementException:
            # NOTE(mpavlase): This is valid state. When request completes
            # even before Selenium get a chance to get the spinner element,
            # it will raise the NoSuchElementException exception.
            pass
        finally:
            self._turn_on_implicit_wait()

    def wait_till_spinner_disappears(self):
        getter = lambda: self._get_element(*self._spinner_locator)
        self.wait_till_element_disappears(getter)

    def wait_till_message_disappears(self):
        getter = lambda: self._get_element(*self._message_locator)
        self.wait_till_element_disappears(getter)

    def wait_till_popups_disappear(self):
        self.wait_till_spinner_disappears()
        self.wait_till_message_disappears()

    def change_project(self, name):
        self.topbar.user_dropdown_project.click_on_project(name)


class BaseNavigationPage(BasePage, navigation.Navigation):
    pass
