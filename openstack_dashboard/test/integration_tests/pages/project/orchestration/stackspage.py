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

from openstack_dashboard.test.integration_tests import config
from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class StacksTable(tables.TableRegion):
    name = "stacks"
    SELECT_TEMPLATE_FORM_FIELDS = ("template_source", "template_upload",
                                   "template_data", "template_url",
                                   "environment_source", "environment_upload",
                                   "environment_data")
    LAUNCH_STACK_FORM_FIELDS = ("stack_name", "timeout_mins",
                                "enable_rollback", "password")

    @tables.bind_table_action('launch')
    def select_template(self, launch_button):
        launch_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.SELECT_TEMPLATE_FORM_FIELDS)

    def launch_stack(self):
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.LAUNCH_STACK_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_stack(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class StacksPage(basepage.BaseNavigationPage):
    DEFAULT_TEMPLATE_SOURCE = 'raw'

    CONFIG = config.get_config()
    DEFAULT_PASSWORD = CONFIG.identity.admin_password
    STACKS_TABLE_NAME_COLUMN = 'name'
    STACKS_TABLE_STATUS_COLUMN = 'stack_status'

    def __init__(self, driver, conf):
        super(StacksPage, self).__init__(driver, conf)
        self._page_title = "Stacks"

    @property
    def stacks_table(self):
        return StacksTable(self.driver, self.conf)

    def _get_row_with_stack_name(self, name):
        return self.stacks_table.get_row(self.STACKS_TABLE_NAME_COLUMN, name)

    def create_stack(self, stack_name, template_data,
                     template_source=DEFAULT_TEMPLATE_SOURCE,
                     environment_source=None,
                     environment_upload=None,
                     timeout_mins=None,
                     enable_rollback=None,
                     password=DEFAULT_PASSWORD):
        select_template_form = self.stacks_table.select_template()
        select_template_form.template_source.value = template_source
        select_template_form.template_data.text = template_data
        select_template_form.submit()
        launch_stack_form = self.stacks_table.launch_stack()
        launch_stack_form.stack_name.text = stack_name
        launch_stack_form.password.text = password
        launch_stack_form.submit()

    def delete_stack(self, name):
        row = self._get_row_with_stack_name(name)
        row.mark()
        confirm_delete_stacks_form = self.stacks_table.delete_stack()
        confirm_delete_stacks_form.submit()

    def is_stack_present(self, name):
        return bool(self._get_row_with_stack_name(name))

    def is_stack_create_complete(self, name):
        row = self._get_row_with_stack_name(name)
        return self.stacks_table.wait_cell_status(
            lambda: row and row.cells[self.STACKS_TABLE_STATUS_COLUMN],
            'Create Complete')

    def is_stack_deleted(self, name):
        return self.stacks_table.is_row_deleted(
            lambda: self._get_row_with_stack_name(name))
