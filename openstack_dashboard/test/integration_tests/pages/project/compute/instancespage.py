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
import netaddr
from selenium.common import exceptions
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import menus
from openstack_dashboard.test.integration_tests.regions import tables


class InstancesTable(tables.TableRegion):
    name = "instances"
    LAUNCH_INSTANCE_FORM_FIELDS = (
        ("name", "count", "availability_zone"),
        ("boot_source_type", "volume_size"),
        {
            'flavor': menus.InstanceFlavorMenuRegion
        },
        {
            'network': menus.InstanceAvailableResourceMenuRegion
        },
    )

    @tables.bind_table_action('launch-ng')
    def launch_instance(self, launch_button):
        launch_button.click()
        return forms.WizardFormRegion(self.driver, self.conf,
                                      self.LAUNCH_INSTANCE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_instance(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class InstancesPage(basepage.BaseNavigationPage):

    DEFAULT_FLAVOR = 'm1.tiny'
    DEFAULT_COUNT = 1
    DEFAULT_BOOT_SOURCE = 'Image'
    DEFAULT_VOLUME_NAME = None
    DEFAULT_SNAPSHOT_NAME = None
    DEFAULT_VOLUME_SNAPSHOT_NAME = None
    DEFAULT_VOL_DELETE_ON_INSTANCE_DELETE = True
    DEFAULT_SECURITY_GROUP = True
    DEFAULT_NETWORK_TYPE = 'shared'

    INSTANCES_TABLE_NAME_COLUMN = 'Instance Name'
    INSTANCES_TABLE_STATUS_COLUMN = 'Status'
    INSTANCES_TABLE_IP_COLUMN = 'IP Address'
    INSTANCES_TABLE_IMAGE_NAME_COLUMN = 'Image Name'

    SOURCE_STEP_INDEX = 1
    FLAVOR_STEP_INDEX = 2
    NETWORKS_STEP_INDEX = 3

    _search_state_active = (
        by.By.XPATH,
        "//*[contains(@class,'normal_column')][contains(text(),'Active')]"
    )

    def __init__(self, driver, conf):
        super().__init__(driver, conf)
        self._page_title = "Instances"

    def _get_row_with_instance_name(self, name):
        return self.instances_table.get_row(self.INSTANCES_TABLE_NAME_COLUMN,
                                            name)

    def _get_rows_with_instances_names(self, names):
        return [
            self.instances_table.get_row(
                self.INSTANCES_TABLE_IMAGE_NAME_COLUMN, n) for n in names
        ]

    @property
    def instances_table(self):
        return InstancesTable(self.driver, self.conf)

    def is_instance_present(self, name):
        return bool(self._get_row_with_instance_name(name))

    def create_instance(
            self, instance_name,
            available_zone=None,
            instance_count=DEFAULT_COUNT,
            flavor=DEFAULT_FLAVOR,
            boot_source=DEFAULT_BOOT_SOURCE,
            source_name=None,
            device_size=None,
            vol_delete_on_instance_delete=DEFAULT_VOL_DELETE_ON_INSTANCE_DELETE
    ):
        if not available_zone:
            available_zone = self.conf.launch_instances.available_zone
        instance_form = self.instances_table.launch_instance()
        instance_form.availability_zone.value = available_zone
        instance_form.name.text = instance_name
        instance_form.count.value = instance_count
        instance_form.switch_to(self.SOURCE_STEP_INDEX)
        instance_form.boot_source_type.text = boot_source
        boot_source = self._get_source_name(instance_form, boot_source,
                                            self.conf.launch_instances)
        if not source_name:
            source_name = boot_source
        menus.InstanceAvailableResourceMenuRegion(
            self.driver, self.conf).transfer_available_resource(source_name)
        if device_size:
            instance_form.volume_size.value = device_size
        if vol_delete_on_instance_delete:
            self.vol_delete_on_instance_delete_click()
        instance_form.switch_to(self.FLAVOR_STEP_INDEX)
        instance_form.flavor.transfer_available_resource(flavor)
        instance_form.switch_to(self.NETWORKS_STEP_INDEX)
        instance_form.network.transfer_available_resource(
            self.DEFAULT_NETWORK_TYPE)
        instance_form.submit()
        instance_form.wait_till_wizard_disappears()

    def vol_delete_on_instance_delete_click(self):
        locator = (
            by.By.XPATH,
            '//label[contains(@ng-model, "vol_delete_on_instance_delete")]')
        elements = self._get_elements(*locator)
        for ele in elements:
            if ele.text == 'Yes':
                ele.click()

    def delete_instance(self, name):
        row = self._get_row_with_instance_name(name)
        row.mark()
        confirm_delete_instances_form = self.instances_table.delete_instance()
        confirm_delete_instances_form.submit()

    def delete_instances(self, instances_names):
        for instance_name in instances_names:
            self._get_row_with_instance_name(instance_name).mark()
        confirm_delete_instances_form = self.instances_table.delete_instance()
        confirm_delete_instances_form.submit()

    def is_instance_deleted(self, name):
        return self.instances_table.is_row_deleted(
            lambda: self._get_row_with_instance_name(name))

    def are_instances_deleted(self, instances_names):
        return self.instances_table.are_rows_deleted(
            lambda: self._get_rows_with_instances_names(instances_names))

    def is_instance_active(self, name):
        def cell_getter():
            row = self._get_row_with_instance_name(name)
            return row and row.cells[self.INSTANCES_TABLE_STATUS_COLUMN]

        try:
            self.wait_until_element_is_visible(self._search_state_active)
        except exceptions.TimeoutException:
            return False
        status = self.instances_table.wait_cell_status(cell_getter,
                                                       ('Active', 'Error'))
        return status == 'Active'

    def _get_source_name(self, instance, boot_source, conf):
        if 'Image' in boot_source:
            return conf.image_name
        elif boot_source == 'Volume':
            return instance.volume_id, self.DEFAULT_VOLUME_NAME
        elif boot_source == 'Instance Snapshot':
            return instance.instance_snapshot_id, self.DEFAULT_SNAPSHOT_NAME
        elif 'Volume Snapshot' in boot_source:
            return (instance.volume_snapshot_id,
                    self.DEFAULT_VOLUME_SNAPSHOT_NAME)

    def get_image_name(self, instance_name):
        row = self._get_row_with_instance_name(instance_name)
        return row.cells[self.INSTANCES_TABLE_IMAGE_NAME_COLUMN].text

    def get_fixed_ipv4(self, name):
        row = self._get_row_with_instance_name(name)
        ips = row.cells[self.INSTANCES_TABLE_IP_COLUMN].text
        for ip in ips.split():
            if netaddr.valid_ipv4(ip):
                return ip
