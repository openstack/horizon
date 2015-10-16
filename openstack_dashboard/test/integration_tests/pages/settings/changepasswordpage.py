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
from openstack_dashboard.test.integration_tests.regions import forms


class ChangepasswordPage(basepage.BaseNavigationPage):

        _password_form_locator = (by.By.ID, 'change_password_modal')

        CHANGE_PASSWORD_FORM_FIELDS = ("current_password", "new_password",
                                       "confirm_password")

        @property
        def password_form(self):
            src_elem = self._get_element(*self._password_form_locator)
            return forms.FormRegion(self.driver, self.conf, src_elem,
                                    self.CHANGE_PASSWORD_FORM_FIELDS)

        def change_password(self, current, new):
            self.password_form.current_password.text = current
            self.password_form.new_password.text = new
            self.password_form.confirm_password.text = new
            self.password_form.submit.click()
            self.wait_till_popups_disappear()

        def reset_to_default_password(self, current):
            if self.topbar.user.text == self.conf.identity.admin_username:
                return self.change_password(current,
                                            self.conf.identity.admin_password)
            else:
                return self.change_password(current,
                                            self.conf.identity.password)
