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


class GroupsTable(tables.TableRegion):

    name = "groups"

    @property
    def form_fields(self):
        return ("name", "description")

    @tables.bind_table_action('create')
    def create_group(self, create_button):
        create_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.form_fields)

    @tables.bind_table_action('delete')
    def delete_group(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('edit')
    def edit_group(self, edit_button, row):
        edit_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.form_fields)


class GroupsPage(basepage.BaseNavigationPage):

    def __init__(self, driver, conf):
        super(GroupsPage, self).__init__(driver, conf)
        self._page_title = 'Groups'

    @property
    def table_name_column(self):
        return "Name"

    @property
    def groups_table(self):
        return GroupsTable(self.driver, self.conf)

    def _get_row_with_group_name(self, name):
        return self.groups_table.get_row(self.table_name_column, name)

    def create_group(self, name, description=None):
        create_form = self.groups_table.create_group()
        create_form.name.text = name
        if description is not None:
            create_form.description.text = description
        create_form.submit()

    def delete_group(self, name):
        row = self._get_row_with_group_name(name)
        row.mark()
        confirm_delete_form = self.groups_table.delete_group()
        confirm_delete_form.submit()

    def edit_group(self, name, new_name=None, new_description=None):
        row = self._get_row_with_group_name(name)
        edit_form = self.groups_table.edit_group(row)
        if new_name is not None:
            edit_form.name.text = new_name
        if new_description is not None:
            edit_form.description.text = new_description
        edit_form.submit()

    def is_group_present(self, name):
        return bool(self._get_row_with_group_name(name))
