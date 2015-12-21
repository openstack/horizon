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

from selenium.common import exceptions

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class RoutersTable(tables.TableRegion):
    name = "routers"
    CREATE_ROUTER_FORM_FIELDS = ("name", "admin_state_up",
                                 "external_network")

    @tables.bind_table_action('create')
    def create_router(self, create_button):
        create_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.CREATE_ROUTER_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_router(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class RoutersPage(basepage.BaseNavigationPage):

    DEFAULT_ADMIN_STATE_UP = 'True'
    DEFAULT_EXTERNAL_NETWORK = 'public'
    ROUTERS_TABLE_NAME_COLUMN = 'name'
    ROUTERS_TABLE_STATUS_COLUMN = 'status'

    def __init__(self, driver, conf):
        super(RoutersPage, self).__init__(driver, conf)
        self._page_title = "Routers"

    def _get_row_with_router_name(self, name):
        return self.routers_table.get_row(
            self.ROUTERS_TABLE_NAME_COLUMN, name)

    @property
    def routers_table(self):
        return RoutersTable(self.driver, self.conf)

    def create_router(self, name, admin_state_up=DEFAULT_ADMIN_STATE_UP,
                      external_network=DEFAULT_EXTERNAL_NETWORK):
        create_router_form = self.routers_table.create_router()
        create_router_form.name.text = name
        create_router_form.admin_state_up.value = admin_state_up
        create_router_form.external_network.text = external_network
        create_router_form.submit()

    def delete_router(self, name):
        row = self._get_row_with_router_name(name)
        row.mark()
        confirm_delete_routers_form = self.routers_table.delete_router()
        confirm_delete_routers_form.submit()

    def is_router_present(self, name):
        return bool(self._get_row_with_router_name(name))

    def is_router_active(self, name):
        row = self._get_row_with_router_name(name)

        def cell_getter():
            return row.cells[self.ROUTERS_TABLE_STATUS_COLUMN]
        try:
            self._wait_till_text_present_in_element(cell_getter, 'Active')
        except exceptions.TimeoutException:
            return False
        return True
