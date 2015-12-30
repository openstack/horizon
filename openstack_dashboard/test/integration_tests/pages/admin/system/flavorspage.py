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


class FlavorsTable(tables.TableRegion):
    name = "flavors"

    CREATE_FLAVOR_FORM_FIELDS = (("name", "flavor_id", "vcpus", "memory_mb",
                                  "disk_gb", "eph_gb", "swap_mb"),
                                 ("all_projects", "selected_projects"))

    @tables.bind_table_action('create')
    def create_flavor(self, create_button):
        create_button.click()
        return forms.TabbedFormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_FLAVOR_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_flavor(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf, None)


class FlavorsPage(basepage.BaseNavigationPage):
    DEFAULT_ID = "auto"
    FLAVORS_TABLE_NAME_COLUMN = 'name'

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

    def delete_flavor(self, name):
        row = self._get_flavor_row(name)
        row.mark()
        confirm_delete_flavors_form = self.flavors_table.delete_flavor()
        confirm_delete_flavors_form.submit()

    def is_flavor_present(self, name):
        return bool(self._get_flavor_row(name))
