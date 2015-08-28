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


class FlavorsPage(basepage.BaseNavigationPage):
    DEFAULT_ID = "auto"
    FLAVORS_TABLE_NAME_COLUMN_INDEX = 0

    _flavors_table_locator = (by.By.ID, 'flavors')

    FLAVORS_TABLE_NAME = "flavors"
    FLAVORS_TABLE_ACTIONS = ("create", "delete")
    FLAVORS_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "edit_flavor",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: (
            "modify_access", "update_metadata", "delete_flavor")
    }

    CREATE_FLAVOR_FORM_FIELDS = (("name", "flavor_id", "vcpus", "memory_mb",
                                  "disk_gb", "eph_gb", "swap_mb"),
                                 ("all_projects", "selected_projects"))

    def __init__(self, driver, conf):
        super(FlavorsPage, self).__init__(driver, conf)
        self._page_title = "Flavors"

    def _get_row_with_flavor_name(self, name):
        return self.flavors_table.get_row(
            self.FLAVORS_TABLE_NAME_COLUMN_INDEX, name)

    @property
    def flavors_table(self):
        src_elem = self._get_element(*self._flavors_table_locator)
        return tables.ComplexActionTableRegion(self.driver,
                                               self.conf, src_elem,
                                               self.FLAVORS_TABLE_NAME,
                                               self.FLAVORS_TABLE_ACTIONS,
                                               self.FLAVORS_TABLE_ROW_ACTIONS)

    @property
    def create_flavor_form(self):
        return forms.TabbedFormRegion(self.driver, self.conf, None,
                                      self.CREATE_FLAVOR_FORM_FIELDS)

    @property
    def confirm_delete_flavors_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def create_flavor(self, name, id_=DEFAULT_ID, vcpus=None, ram=None,
                      root_disk=None, ephemeral_disk=None, swap_disk=None):
        self.flavors_table.create.click()
        self.create_flavor_form.name.text = name
        if id_ is not None:
            self.create_flavor_form.flavor_id.text = id_
        self.create_flavor_form.vcpus.value = vcpus
        self.create_flavor_form.memory_mb.value = ram
        self.create_flavor_form.disk_gb.value = root_disk
        self.create_flavor_form.eph_gb.value = ephemeral_disk
        self.create_flavor_form.swap_mb.value = swap_disk
        self.create_flavor_form.submit.click()
        self.wait_till_popups_disappear()

    def delete_flavor(self, name):
        row = self._get_row_with_flavor_name(name)
        row.mark()
        self.flavors_table.delete.click()
        self.confirm_delete_flavors_form.submit.click()
        self.wait_till_popups_disappear()

    def is_flavor_present(self, name):
        return bool(self._get_row_with_flavor_name(name))
