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


class QosSpecsTable(tables.TableRegion):
    name = 'qos_specs'
    CREATE_QOS_SPEC_FORM_FIELDS = ("name", "consumer")
    EDIT_CONSUMER_FORM_FIELDS = ("consumer_choice", )

    @tables.bind_table_action('create')
    def create_qos_spec(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_QOS_SPEC_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_qos_specs(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('edit_consumer')
    def edit_consumer(self, edit_consumer_button, row):
        edit_consumer_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.EDIT_CONSUMER_FORM_FIELDS)


class VolumeTypesTable(tables.TableRegion):
    name = 'volume_types'

    CREATE_VOLUME_TYPE_FORM_FIELDS = (
        "name", "vol_type_description")

    @tables.bind_table_action('create')
    def create_volume_type(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_VOLUME_TYPE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_volume_type(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class VolumetypesPage(basepage.BaseNavigationPage):
    QOS_SPECS_TABLE_NAME_COLUMN = 'Name'
    VOLUME_TYPES_TABLE_NAME_COLUMN = 'Name'
    QOS_SPECS_TABLE_CONSUMER_COLUMN = 'Consumer'
    CINDER_CONSUMER = 'back-end'

    def __init__(self, driver, conf):
        super(VolumetypesPage, self).__init__(driver, conf)
        self._page_title = "Volume Types"

    @property
    def qos_specs_table(self):
        return QosSpecsTable(self.driver, self.conf)

    @property
    def volume_types_table(self):
        return VolumeTypesTable(self.driver, self.conf)

    def _get_row_with_qos_spec_name(self, name):
        return self.qos_specs_table.get_row(
            self.QOS_SPECS_TABLE_NAME_COLUMN, name)

    def _get_row_with_volume_type_name(self, name):
        return self.volume_types_table.get_row(
            self.VOLUME_TYPES_TABLE_NAME_COLUMN, name)

    def create_qos_spec(self, qos_spec_name, consumer=CINDER_CONSUMER):
        create_qos_spec_form = self.qos_specs_table.create_qos_spec()
        create_qos_spec_form.name.text = qos_spec_name
        create_qos_spec_form.submit()

    def create_volume_type(self, volume_type_name, description=None):
        volume_type_form = self.volume_types_table.create_volume_type()
        volume_type_form.name.text = volume_type_name
        if description is not None:
            volume_type_form.description.text = description
        volume_type_form.submit()

    def delete_qos_specs(self, name):
        row = self._get_row_with_qos_spec_name(name)
        row.mark()
        confirm_delete_qos_spec_form = self.qos_specs_table.delete_qos_specs()
        confirm_delete_qos_spec_form.submit()

    def delete_volume_type(self, name):
        row = self._get_row_with_volume_type_name(name)
        row.mark()
        confirm_delete_volume_types_form = \
            self.volume_types_table.delete_volume_type()
        confirm_delete_volume_types_form.submit()

    def edit_consumer(self, name, consumer_choice):
        row = self._get_row_with_qos_spec_name(name)
        edit_consumer_form = self.qos_specs_table.edit_consumer(row)
        edit_consumer_form.consumer_choice.value = consumer_choice
        edit_consumer_form.submit()

    def is_qos_spec_present(self, name):
        return bool(self._get_row_with_qos_spec_name(name))

    def is_volume_type_present(self, name):
        return bool(self._get_row_with_volume_type_name(name))

    def is_qos_spec_deleted(self, name):
        return self.qos_specs_table.is_row_deleted(
            lambda: self._get_row_with_qos_spec_name(name))

    def is_volume_type_deleted(self, name):
        return self.volume_types_table.is_row_deleted(
            lambda: self._get_row_with_volume_type_name(name))

    def get_consumer(self, name):
        row = self._get_row_with_qos_spec_name(name)
        return row.cells[self.QOS_SPECS_TABLE_CONSUMER_COLUMN].text
