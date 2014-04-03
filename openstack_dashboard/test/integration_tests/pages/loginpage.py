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
from selenium.webdriver.common import keys

from openstack_dashboard.test.integration_tests.pages import adminpage
from openstack_dashboard.test.integration_tests.pages import pageobject
from openstack_dashboard.test.integration_tests.pages import projectpage


class LoginPage(pageobject.PageObject):

    _login_username_field_locator = (by.By.CSS_SELECTOR, '#id_username')
    _login_password_field_locator = (by.By.CSS_SELECTOR, '#id_password')
    _login_submit_button_locator = (by.By.CSS_SELECTOR,
                                    'div.modal-footer button.btn')

    def __init__(self, driver, conf):
        super(LoginPage, self).__init__(driver, conf)
        self._page_title = "Login"

    def is_login_page(self):
        return self.is_the_current_page and \
            self.is_element_visible(*self._login_submit_button_locator)

    @property
    def username(self):
        return self.get_element(*self._login_username_field_locator)

    @property
    def password(self):
        return self.get_element(*self._login_password_field_locator)

    @property
    def login_button(self):
        return self.get_element(*self._login_submit_button_locator)

    def _click_on_login_button(self):
        self.login_button.click()

    def _press_enter_on_login_button(self):
        self.login_button.send_keys(keys.Keys.RETURN)

    def login(self, *args, **kwargs):
        return self.login_with_mouse_click(*args, **kwargs)

    def login_with_mouse_click(self, *args, **kwargs):
        return self._do_login(self._click_on_login_button, *args, **kwargs)

    def login_with_enter_key(self, *args, **kwargs):
        return self._do_login(self._press_enter_on_login_button,
                              *args, **kwargs)

    def _do_login(self, login_method, user='user'):
        if user != 'user':
            return self.login_as_admin(login_method)
        else:
            return self.login_as_user(login_method)

    def login_as_admin(self, login_method):
        self.username.send_keys(self.conf.identity.admin_username)
        self.password.send_keys(self.conf.identity.admin_password)
        login_method()
        return adminpage.AdminPage(self.driver, self.conf)

    def login_as_user(self, login_method):
        self.username.send_keys(self.conf.identity.username)
        self.password.send_keys(self.conf.identity.password)
        login_method()
        return projectpage.ProjectPage(self.driver, self.conf)
