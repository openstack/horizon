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


class SecuritygroupsPage(basepage.BaseNavigationPage):

    SECURITYGROUPS_TABLE_NAME_COLUMN_INDEX = 0

    _securitygroups_table_locator = (by.By.ID, 'security_groups')

    SECURITYGROUPS_TABLE_NAME = "security_groups"
    SECURITYGROUPS_TABLE_ACTIONS = ("create", "delete")
    SECURITYGROUPS_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "manage_rules",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: (
            "edit_security_group", "delete_security_group")
    }

    CREATE_SECURITYGROUP_FORM_FIELDS = ("name", "description")

    def __init__(self, driver, conf):
        super(SecuritygroupsPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    def _get_row_with_securitygroup_name(self, name):
        return self.securitygroups_table.get_row(
            self.SECURITYGROUPS_TABLE_NAME_COLUMN_INDEX, name)

    @property
    def securitygroups_table(self):
        src_elem = self._get_element(*self._securitygroups_table_locator)
        return tables.ComplexActionTableRegion(
            self.driver, self.conf, src_elem,
            self.SECURITYGROUPS_TABLE_NAME,
            self.SECURITYGROUPS_TABLE_ACTIONS,
            self.SECURITYGROUPS_TABLE_ROW_ACTIONS)

    @property
    def create_securitygroups_form(self):
        return forms.FormRegion(self.driver, self.conf, None,
                                self.CREATE_SECURITYGROUP_FORM_FIELDS)

    @property
    def confirm_delete_securitygroups_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def create_securitygroup(self, name, description=None):
        self.securitygroups_table.create.click()
        self.create_securitygroups_form.name.text = name
        if description is not None:
            self.create_securitygroups_form.description.text = description
        self.create_securitygroups_form.submit.click()
        self.wait_till_popups_disappear()

    def delete_securitygroup(self, name):
        row = self._get_row_with_securitygroup_name(name)
        row.mark()
        self.securitygroups_table.delete.click()
        self.confirm_delete_securitygroups_form.submit.click()
        self.wait_till_popups_disappear()

    def is_securitygroup_present(self, name):
        return bool(self._get_row_with_securitygroup_name(name))
