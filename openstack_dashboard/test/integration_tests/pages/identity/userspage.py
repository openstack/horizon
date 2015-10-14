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
from openstack_dashboard.test.integration_tests.regions import tables


class UsersPage(basepage.BaseNavigationPage):

    _users_table_locator = (by.By.CSS_SELECTOR, 'table#users')

    USERS_TABLE_NAME_COLUMN_INDEX = 0

    USERS_TABLE_ACTIONS = ("create_user", "delete_users")

    USERS_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "edit_user",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: ("disable_user",
                                                          "delete_user")
    }

    CREATE_USER_FORM_FIELDS = ("name", "email", "password",
                               "confirm_password", "project", "role_id")

    def __init__(self, driver, conf):
        super(UsersPage, self).__init__(driver, conf)
        self._page_title = "Users"

    def _get_row_with_user_name(self, name):
        return self.users_table.get_row(
            self.USERS_TABLE_NAME_COLUMN_INDEX, name)

    @property
    def users_table(self):
        src_elem = self._get_element(*self._users_table_locator)
        return tables.ComplexActionTableRegion(self.driver,
                                               self.conf, src_elem,
                                               self.USERS_TABLE_ACTIONS,
                                               self.USERS_TABLE_ROW_ACTIONS
                                               )

    @property
    def create_user_form(self):
        return forms.FormRegion(self.driver, self.conf, None,
                                self.CREATE_USER_FORM_FIELDS)

    @property
    def confirm_delete_users_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def create_user(self, name, password,
                    project, role, email=None):
        self.users_table.create_user.click()
        self.create_user_form.name.text = name
        if email is not None:
            self.create_user_form.email.text = email
        self.create_user_form.password.text = password
        self.create_user_form.confirm_password.text = password
        self.create_user_form.project.text = project
        self.create_user_form.role_id.text = role
        self.create_user_form.submit.click()
        self.wait_till_popups_disappear()

    def delete_user(self, name):
        row = self._get_row_with_user_name(name)
        row.mark()
        self.users_table.delete_users.click()
        self.confirm_delete_users_form.submit.click()
        self.wait_till_popups_disappear()

    def is_user_present(self, name):
        return bool(self._get_row_with_user_name(name))
