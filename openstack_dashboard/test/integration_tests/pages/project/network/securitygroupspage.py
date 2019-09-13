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
from openstack_dashboard.test.integration_tests.pages.project.network.\
    security_groups.managerulespage import ManageRulesPage


class SecurityGroupsTable(tables.TableRegion):
    name = "security_groups"
    CREATE_SECURITYGROUP_FORM_FIELDS = ("name", "description")

    @tables.bind_table_action('create')
    def create_group(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver,
            self.conf,
            field_mappings=self.CREATE_SECURITYGROUP_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_group(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf, None)

    @tables.bind_row_action('manage_rules')
    def manage_rules(self, manage_rules_button, row):
        manage_rules_button.click()
        return ManageRulesPage(self.driver, self.conf)


class SecuritygroupsPage(basepage.BaseNavigationPage):

    SECURITYGROUPS_TABLE_NAME_COLUMN = 'Name'

    def __init__(self, driver, conf):
        super(SecuritygroupsPage, self).__init__(driver, conf)
        self._page_title = "Security Groups"

    def _get_row_with_securitygroup_name(self, name):
        return self.securitygroups_table.get_row(
            self.SECURITYGROUPS_TABLE_NAME_COLUMN, name)

    @property
    def securitygroups_table(self):
        return SecurityGroupsTable(self.driver, self.conf)

    def create_securitygroup(self, name, description=None):
        create_securitygroups_form = self.securitygroups_table.create_group()
        create_securitygroups_form.name.text = name
        if description is not None:
            create_securitygroups_form.description.text = description
        create_securitygroups_form.submit()
        if 'Manage Security Group Rules' in self.driver.title:
            return ManageRulesPage(self.driver, self.conf)

    def delete_securitygroup(self, name):
        row = self._get_row_with_securitygroup_name(name)
        row.mark()
        modal_confirmation_form = self.securitygroups_table.delete_group()
        modal_confirmation_form.submit()

    def is_securitygroup_present(self, name):
        return bool(self._get_row_with_securitygroup_name(name))

    def go_to_manage_rules(self, name):
        row = self._get_row_with_securitygroup_name(name)
        return self.securitygroups_table.manage_rules(row)
