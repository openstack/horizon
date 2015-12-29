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


class HostAggregatesTable(tables.TableRegion):
    name = "host_aggregates"

    CREATE_HOST_AGGREGATE_FORM_FIELDS = (("name",
                                          "availability_zone"),)

    @tables.bind_table_action('create')
    def create_host_aggregate(self, create_button):
        create_button.click()
        return forms.TabbedFormRegion(self.driver, self.conf,
                                      field_mappings=self.
                                      CREATE_HOST_AGGREGATE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_host_aggregate(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf, None)

    # Examples of how to bind to secondary actions
    @tables.bind_row_action('update', primary=True)
    def update_host_aggregate(self, edit_host_aggregate_button, row):
        edit_host_aggregate_button.click()
        pass

    @tables.bind_row_action('manage')
    def modify_access(self, manage_button, row):
        manage_button.click()
        pass


class HostaggregatesPage(basepage.BaseNavigationPage):
    HOST_AGGREGATES_TABLE_NAME_COLUMN = 'name'

    def __init__(self, driver, conf):
        super(HostaggregatesPage, self).__init__(driver, conf)
        self._page_title = "Host Aggregates"

    @property
    def host_aggregates_table(self):
        return HostAggregatesTable(self.driver, self.conf)

    def _get_host_aggregate_row(self, name):
        return self.host_aggregates_table.get_row(
            self.HOST_AGGREGATES_TABLE_NAME_COLUMN, name)

    def create_host_aggregate(self, name, availability_zone):
        create_host_aggregate_form = \
            self.host_aggregates_table.create_host_aggregate()
        create_host_aggregate_form.name.text = name
        create_host_aggregate_form.availability_zone.text = \
            availability_zone
        create_host_aggregate_form.submit()

    def delete_host_aggregate(self, name):
        row = self._get_host_aggregate_row(name)
        row.mark()
        modal_confirmation_form = self.host_aggregates_table.\
            delete_host_aggregate()
        modal_confirmation_form.submit()

    def is_host_aggregate_present(self, name):
        return bool(self._get_host_aggregate_row(name))
