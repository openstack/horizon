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
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class InstancesPage(basepage.BaseNavigationPage):

    DEFAULT_FLAVOR = 'm1.tiny'
    DEFAULT_COUNT = 1
    DEFAULT_BOOT_SOURCE = 'Boot from image'
    DEFAULT_VOLUME_NAME = None
    DEFAULT_SNAPSHOT_NAME = None
    DEFAULT_VOLUME_SNAPSHOT_NAME = None
    DEFAULT_VOL_DELETE_ON_INSTANCE_DELETE = False
    DEFAULT_SECURITY_GROUP = True

    _instances_table_locator = (by.By.CSS_SELECTOR, 'table#instances')

    INSTANCES_TABLE_NAME = "instances"
    INSTANCES_TABLE_ACTIONS = ("launch_ng", "launch", "delete",
                               ('start', 'stop', "reboot"))
    INSTANCES_TABLE_NAME_COLUMN_INDEX = 0
    INSTANCES_TABLE_STATUS_COLUMN_INDEX = 5
    INSTANCES_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "create_snapshot",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: (
            "associate_floating_ip", "disassociate_floating_ip",
            "edit_instance", "edit_security_groups", "console",
            "view_log", "pause", "suspend", "resize", "lock", "unlock",
            "soft_reboot", "hard_reboot", "shutoff", "rebuild", "delete")
    }

    CREATE_INSTANCE_FORM_FIELDS = ((
        "availability_zone", "name", "flavor",
        "count", "source_type", "instance_snapshot_id",
        "volume_id", "volume_snapshot_id", "image_id", "volume_size",
        "vol_delete_on_instance_delete"),
        ("keypair", "groups"),
        ("script_source", "script_upload", "script_data"),
        ("disk_config", "config_drive")
    )

    def __init__(self, driver, conf):
        super(InstancesPage, self).__init__(driver, conf)
        self._page_title = "Instances"

    def _get_row_with_instance_name(self, name):
        return self.instances_table.get_row(
            self.INSTANCES_TABLE_NAME_COLUMN_INDEX, name)

    @property
    def instances_table(self):
        src_elem = self._get_element(*self._instances_table_locator)
        return tables.ComplexActionTableRegion(self.driver,
                                               self.conf, src_elem,
                                               self.INSTANCES_TABLE_NAME,
                                               self.INSTANCES_TABLE_ACTIONS,
                                               self.INSTANCES_TABLE_ROW_ACTIONS
                                               )

    @property
    def confirm_delete_instances_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    @property
    def create_instance_form(self):
        return forms.TabbedFormRegion(self.driver, self.conf, None,
                                      self.CREATE_INSTANCE_FORM_FIELDS)

    @property
    def delete_instance_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

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
        self.instances_table.launch.click()
        instance = self.create_instance_form
        instance.availability_zone.value = available_zone
        instance.name.text = instance_name
        instance.flavor.text = flavor
        instance.count.value = instance_count
        instance.source_type.text = boot_source
        boot_source = self._get_source_name(instance, boot_source,
                                            self.conf.launch_instances)
        if not source_name:
            source_name = boot_source[1]
        boot_source[0].text = source_name
        if device_size:
            instance.volume_size.value = device_size
        if vol_delete_on_instance_delete:
            instance.vol_delete_on_instance_delete.mark()
        instance.submit.click()
        self.wait_till_popups_disappear()

    def delete_instance(self, name):
        row = self._get_row_with_instance_name(name)
        row.mark()
        self.instances_table.delete.click()
        self.confirm_delete_instances_form.submit.click()
        self.wait_till_popups_disappear()

    def is_instance_deleted(self, name):
        try:
            row = self._get_row_with_instance_name(name)
            self._wait_till_element_disappears(row)
        except exceptions.TimeoutException:
            return False
        return True

    def is_instance_active(self, name):
        row = self._get_row_with_instance_name(name)

        def cell_getter():
            return row.cells[self.INSTANCES_TABLE_STATUS_COLUMN_INDEX]
        try:
            self._wait_till_text_present_in_element(cell_getter, 'Active')
        except exceptions.TimeoutException:
            return False
        return True

    def _get_source_name(self, instance, boot_source,
                         conf):
        if 'image' in boot_source:
            return instance.image_id, conf.image_name
        elif boot_source == 'Boot from volume':
            return instance.volume_id, self.DEFAULT_VOLUME_NAME
        elif boot_source == 'Boot from snapshot':
            return instance.instance_snapshot_id, self.DEFAULT_SNAPSHOT_NAME
        elif 'volume snapshot (creates a new volume)' in boot_source:
            return (instance.volume_snapshot_id,
                    self.DEFAULT_VOLUME_SNAPSHOT_NAME)
