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


class InterfacesTable(tables.TableRegion):
    name = "interfaces"
    CREATE_INTERFACE_FORM_FIELDS = ("subnet_id", "ip_address")

    @tables.bind_table_action('create')
    def create_interface(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver,
            self.conf,
            field_mappings=self.CREATE_INTERFACE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_interface(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('delete')
    def delete_interface_by_row_action(self, delete_button, row):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class RouterInterfacesPage(basepage.BaseNavigationPage):

    INTERFACES_TABLE_STATUS_COLUMN = 'Status'
    INTERFACES_TABLE_NAME_COLUMN = 'Name'
    INTERFACES_TABLE_FIXED_IPS_COLUMN = 'Fixed IPs'
    DEFAULT_IPv4_ADDRESS = '10.100.0.1'
    _interface_subnet_selector = (by.By.CSS_SELECTOR, 'div > .themable-select')
    _breadcrumb_routers_locator = (
        by.By.CSS_SELECTOR,
        'ol.breadcrumb>li>' + 'a[href*="/project/routers"]')

    def __init__(self, driver, conf, router_name):
        super().__init__(driver, conf)
        self._page_title = router_name

    def _get_row_with_interface_name(self, name):
        return self.interfaces_table.get_row(self.INTERFACES_TABLE_NAME_COLUMN,
                                             name)

    def _get_row_with_ip_address(self):
        return self.interfaces_table.get_row(
            self.INTERFACES_TABLE_FIXED_IPS_COLUMN, self.DEFAULT_IPv4_ADDRESS)

    @property
    def subnet_selector(self):
        src_elem = self._get_element(*self._interface_subnet_selector)
        return forms.ThemableSelectFormFieldRegion(
            self.driver,
            self.conf,
            src_elem=src_elem,
            strict_options_match=False)

    @property
    def interfaces_table(self):
        return InterfacesTable(self.driver, self.conf)

    @property
    def interface_name(self):
        row = self._get_row_with_ip_address()
        return row.cells[self.INTERFACES_TABLE_NAME_COLUMN].text

    def switch_to_routers_page(self):
        self._get_element(*self._breadcrumb_routers_locator).click()

    def create_interface(self, subnet):
        interface_form = self.interfaces_table.create_interface()
        self.subnet_selector.text = subnet
        interface_form.ip_address.text = self.DEFAULT_IPv4_ADDRESS
        interface_form.submit()

    def delete_interface(self, interface_name):
        row = self._get_row_with_interface_name(interface_name)
        row.mark()
        confirm_delete_interface_form = self.interfaces_table.\
            delete_interface()
        confirm_delete_interface_form.submit()

    def delete_interface_by_row_action(self, interface_name):
        row = self._get_row_with_interface_name(interface_name)
        confirm_delete_interface = self.interfaces_table.\
            delete_interface_by_row_action(row)
        confirm_delete_interface.submit()

    def is_interface_present(self, interface_name):
        return bool(self._get_row_with_interface_name(interface_name))

    def is_interface_status(self, interface_name, status):
        row = self._get_row_with_interface_name(interface_name)
        return row.cells[self.INTERFACES_TABLE_STATUS_COLUMN].text == status
