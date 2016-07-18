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
from openstack_dashboard.test.integration_tests.regions import menus
from openstack_dashboard.test.integration_tests.regions import tables

from selenium.webdriver.common import by


class FlavorsTable(tables.TableRegion):
    name = "flavors"

    CREATE_FLAVOR_FORM_FIELDS = (("name", "flavor_id", "vcpus", "memory_mb",
                                  "disk_gb", "eph_gb",
                                  "swap_mb",
                                  "rxtx_factor"),
                                 {"members": menus.MembershipMenuRegion})

    UPDATE_FLAVOR_FORM_FIELDS = (("name", "vcpus", "memory_mb",
                                  "disk_gb", "eph_gb", "swap_mb",
                                  "rxtx_factor"),
                                 {"members": menus.MembershipMenuRegion})

    @tables.bind_table_action('create')
    def create_flavor(self, create_button):
        create_button.click()
        return forms.TabbedFormRegion(
            self.driver,
            self.conf,
            field_mappings=self.CREATE_FLAVOR_FORM_FIELDS
        )

    @tables.bind_row_action('update')
    def update_flavor_info(self, edit_button, row):
        edit_button.click()
        return forms.TabbedFormRegion(
            self.driver,
            self.conf,
            field_mappings=self.UPDATE_FLAVOR_FORM_FIELDS
        )

    @tables.bind_row_action('projects')
    def update_flavor_access(self, update_button, row):
        update_button.click()
        return forms.TabbedFormRegion(
            self.driver,
            self.conf,
            field_mappings=self.UPDATE_FLAVOR_FORM_FIELDS,
            default_tab=1
        )

    @tables.bind_row_action('delete')
    def delete_by_row(self, delete_button, row):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class FlavorsPage(basepage.BaseNavigationPage):
    DEFAULT_ID = "auto"
    FLAVORS_TABLE_NAME_COLUMN = 'name'
    FLAVORS_TABLE_VCPUS_COLUMN = 'vcpus'
    FLAVORS_TABLE_RAM_COLUMN = 'ram'
    FLAVORS_TABLE_DISK_COLUMN = 'disk'
    FLAVORS_TABLE_PUBLIC_COLUMN = 'public'

    def __init__(self, driver, conf):
        super(FlavorsPage, self).__init__(driver, conf)
        self._page_title = "Flavors"

    @property
    def flavors_table(self):
        return FlavorsTable(self.driver, self.conf)

    def _get_flavor_row(self, name):
        return self.flavors_table.get_row(self.FLAVORS_TABLE_NAME_COLUMN, name)

    def create_flavor(self, name, id_=DEFAULT_ID, vcpus=None, ram=None,
                      root_disk=None, ephemeral_disk=None, swap_disk=None):
        create_flavor_form = self.flavors_table.create_flavor()
        create_flavor_form.name.text = name
        if id_ is not None:
            create_flavor_form.flavor_id.text = id_
        create_flavor_form.vcpus.value = vcpus
        create_flavor_form.memory_mb.value = ram
        create_flavor_form.disk_gb.value = root_disk
        create_flavor_form.eph_gb.value = ephemeral_disk
        create_flavor_form.swap_mb.value = swap_disk
        create_flavor_form.submit()

    def is_flavor_present(self, name):
        return bool(self._get_flavor_row(name))

    def update_flavor_info(self, name, add_up):
        row = self._get_flavor_row(name)
        update_flavor_form = self.flavors_table.update_flavor_info(row)

        update_flavor_form.name.text = "edited-" + name
        update_flavor_form.vcpus.value = \
            int(update_flavor_form.vcpus.value) + add_up
        update_flavor_form.memory_mb.value =\
            int(update_flavor_form.memory_mb.value) + add_up
        update_flavor_form.disk_gb.value =\
            int(update_flavor_form.disk_gb.value) + add_up

        update_flavor_form.submit()

    def update_flavor_access(self, name, project_name, allocate=True):
        row = self._get_flavor_row(name)
        update_flavor_form = self.flavors_table.update_flavor_access(row)

        if allocate:
            update_flavor_form.members.allocate_member(project_name)
        else:
            update_flavor_form.members.deallocate_member(project_name)

        update_flavor_form.submit()

    def delete_flavor_by_row(self, name):
        row = self._get_flavor_row(name)
        delete_form = self.flavors_table.delete_by_row(row)
        delete_form.submit()

    def get_flavor_vcpus(self, name):
        row = self._get_flavor_row(name)
        return row.cells[self.FLAVORS_TABLE_VCPUS_COLUMN].text

    def get_flavor_ram(self, name):
        row = self._get_flavor_row(name)
        return row.cells[self.FLAVORS_TABLE_RAM_COLUMN].text

    def get_flavor_disk(self, name):
        row = self._get_flavor_row(name)
        return row.cells[self.FLAVORS_TABLE_DISK_COLUMN].text

    def is_flavor_public(self, name):
        row = self._get_flavor_row(name)
        return row.cells[self.FLAVORS_TABLE_PUBLIC_COLUMN].text == "Yes"


class FlavorsPageNG(FlavorsPage):
    _resource_page_header_locator = (by.By.CSS_SELECTOR,
                                     'hz-resource-panel hz-page-header h1')

    @property
    def header(self):
        return self._get_element(*self._resource_page_header_locator)
