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


class GroupTypesTable(tables.TableRegion):
    name = 'group_types'

    CREATE_GROUP_TYPE_FORM_FIELDS = ("name", "group_type_description")

    @tables.bind_table_action('create')
    def create_group_type(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_GROUP_TYPE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_group_type(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class GrouptypesPage(basepage.BaseNavigationPage):
    GROUP_TYPES_TABLE_NAME_COLUMN = 'Name'

    def __init__(self, driver, conf):
        super().__init__(driver, conf)
        self._page_title = "Group Types"

    @property
    def group_types_table(self):
        return GroupTypesTable(self.driver, self.conf)

    def _get_row_with_group_type_name(self, name):
        return self.group_types_table.get_row(
            self.GROUP_TYPES_TABLE_NAME_COLUMN, name)

    def create_group_type(self, group_type_name, description=None):
        group_type_form = self.group_types_table.create_group_type()
        group_type_form.name.text = group_type_name
        if description is not None:
            group_type_form.description.text = description
        group_type_form.submit()

    def delete_group_type(self, name):
        row = self._get_row_with_group_type_name(name)
        row.mark()
        confirm_delete_group_types_form = \
            self.group_types_table.delete_group_type()
        confirm_delete_group_types_form.submit()

    def is_group_type_present(self, name):
        return bool(self._get_row_with_group_type_name(name))

    def is_group_type_deleted(self, name):
        return self.group_types_table.is_row_deleted(
            lambda: self._get_row_with_group_type_name(name))
