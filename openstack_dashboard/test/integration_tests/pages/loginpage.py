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

from openstack_dashboard.test.integration_tests.pages.admin.system import \
    overviewpage as system_overviewpage
from openstack_dashboard.test.integration_tests.pages import pageobject
from openstack_dashboard.test.integration_tests.pages.project.compute import \
    overviewpage as compute_overviewpage


class LoginPage(pageobject.PageObject):
    _login_username_field_locator = (by.By.ID, 'id_username')
    _login_password_field_locator = (by.By.ID, 'id_password')
    _login_submit_button_locator = (by.By.CSS_SELECTOR,
                                    'div.panel-footer button.btn')
    _login_logout_reason_locator = (by.By.ID, 'logout_reason')

    def __init__(self, driver, conf):
        super(LoginPage, self).__init__(driver, conf)
        self._page_title = "Login"

    def is_login_page(self):
        return (self.is_the_current_page() and
                self._is_element_visible(*self._login_submit_button_locator))

    @property
    def username(self):
        return self._get_element(*self._login_username_field_locator)

    @property
    def password(self):
        return self._get_element(*self._login_password_field_locator)

    @property
    def login_button(self):
        return self._get_element(*self._login_submit_button_locator)

    def _click_on_login_button(self):
        self.login_button.click()

    def _press_enter_on_login_button(self):
        self.login_button.send_keys(keys.Keys.RETURN)

    def is_logout_reason_displayed(self):
        return self._get_element(*self._login_logout_reason_locator)

    def login(self, user=None, password=None):
        return self.login_with_mouse_click(user, password)

    def login_with_mouse_click(self, user, password):
        return self._do_login(user, password, self._click_on_login_button)

    def login_with_enter_key(self, user, password):
        return self._do_login(user, password,
                              self._press_enter_on_login_button)

    def _do_login(self, user, password, login_method):
        if user == self.conf.identity.admin_username:
            if password is None:
                password = self.conf.identity.admin_password
            return self.login_as_admin(password, login_method)
        else:
            if password is None:
                password = self.conf.identity.password
            if user is None:
                user = self.conf.identity.username
            return self.login_as_user(user, password, login_method)

    def login_as_admin(self, password, login_method):
        self.username.send_keys(self.conf.identity.admin_username)
        self.password.send_keys(password)
        login_method()
        return system_overviewpage.OverviewPage(self.driver, self.conf)

    def login_as_user(self, user, password, login_method):
        self.username.send_keys(user)
        self.password.send_keys(password)
        login_method()
        return compute_overviewpage.OverviewPage(self.driver, self.conf)
