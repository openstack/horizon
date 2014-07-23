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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.pages import pageobject


class ChangePasswordPage(basepage.BasePage):

        @property
        def modal(self):
            return ChangePasswordPage.ChangePasswordModal(self.driver,
                                                          self.conf)

        def change_password(self, current, new):
            self.fill_field_element(
                current, self.modal.current_password)
            self.fill_field_element(
                new, self.modal.new_password)
            self.fill_field_element(
                new, self.modal.confirm_new_password)
            self.modal.click_on_change_button()

        def reset_to_default_password(self, current):
            if self.topbar.user.text == self.conf.identity.admin_username:
                return self.change_password(current,
                                            self.conf.identity.admin_password)
            else:
                return self.change_password(current,
                                            self.conf.identity.password)

        class ChangePasswordModal(pageobject.PageObject):
            _current_password_locator = (by.By.CSS_SELECTOR,
                                         'input#id_current_password')
            _new_password_locator = (by.By.CSS_SELECTOR,
                                     'input#id_new_password')
            _confirm_new_password_locator = (by.By.CSS_SELECTOR,
                                             'input#id_confirm_password')
            _change_submit_button_locator = (by.By.CSS_SELECTOR,
                                             'div.modal-footer button.btn')

            @property
            def current_password(self):
                return self.get_element(*self._current_password_locator)

            @property
            def new_password(self):
                return self.get_element(*self._new_password_locator)

            @property
            def confirm_new_password(self):
                return self.get_element(*self._confirm_new_password_locator)

            @property
            def change_button(self):
                return self.get_element(*self._change_submit_button_locator)

            def click_on_change_button(self):
                self.change_button.click()
