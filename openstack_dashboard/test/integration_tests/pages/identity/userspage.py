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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class UsersTable(tables.TableRegion):
    name = 'users'
    CREATE_USER_FORM_FIELDS = ("name", "email", "password",
                               "confirm_password", "project", "role_id")

    @tables.bind_table_action('create')
    def create_user(self, create_button):
        create_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.CREATE_USER_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_user(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class UsersPage(basepage.BaseNavigationPage):

    USERS_TABLE_NAME_COLUMN = 'name'

    def __init__(self, driver, conf):
        super(UsersPage, self).__init__(driver, conf)
        self._page_title = "Users"

    def _get_row_with_user_name(self, name):
        return self.users_table.get_row(self.USERS_TABLE_NAME_COLUMN, name)

    @property
    def users_table(self):
        return UsersTable(self.driver, self.conf)

    def create_user(self, name, password,
                    project, role, email=None):
        create_user_form = self.users_table.create_user()
        create_user_form.name.text = name
        if email is not None:
            create_user_form.email.text = email
        create_user_form.password.text = password
        create_user_form.confirm_password.text = password
        create_user_form.project.text = project
        create_user_form.role_id.text = role
        create_user_form.submit()

    def delete_user(self, name):
        row = self._get_row_with_user_name(name)
        row.mark()
        confirm_delete_users_form = self.users_table.delete_user()
        confirm_delete_users_form.submit()

    def is_user_present(self, name):
        return bool(self._get_row_with_user_name(name))
