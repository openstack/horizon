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


class DefaultQuotasTable(tables.TableRegion):
    name = "compute_quotas"

    UPDATE_DEFAULTS_FORM_FIELDS = (("injected_file_content_bytes",
                                    "metadata_items", "ram",
                                    "key_pairs",
                                    "injected_file_path_bytes",
                                    "instances", "injected_files",
                                    "cores", "server_groups",
                                    "server_group_members"),
                                   ("volumes", "gigabytes",
                                    "snapshots"))

    @tables.bind_table_action('update_compute_defaults')
    def update(self, update_button):
        update_button.click()
        return forms.TabbedFormRegion(
            self.driver,
            self.conf,
            self.UPDATE_DEFAULTS_FORM_FIELDS)


class DefaultVolumeQuotasTable(DefaultQuotasTable):
    name = "volume_quotas"

    @tables.bind_table_action('update_volume_defaults')
    def update(self, update_button):
        update_button.click()
        return forms.TabbedFormRegion(
            self.driver,
            self.conf,
            self.UPDATE_DEFAULTS_FORM_FIELDS)


class DefaultsPage(basepage.BaseNavigationPage):

    QUOTAS_TABLE_NAME_COLUMN = 'Quota Name'
    QUOTAS_TABLE_LIMIT_COLUMN = 'Limit'
    VOLUMES_TAB_INDEX = 1
    DEFAULT_COMPUTE_QUOTA_NAMES = [
        'Injected File Content Bytes',
        'Metadata Items',
        'Server Group Members',
        'Server Groups',
        'RAM (MB)',
        'Key Pairs',
        'Length of Injected File Path',
        'Instances',
        'Injected Files',
        'VCPUs'
    ]
    DEFAULT_VOLUME_QUOTA_NAMES = [
        'Volumes',
        'Total Size of Volumes and Snapshots (GiB)',
        'Volume Snapshots',
    ]
    _volume_quotas_tab_locator = (by.By.CSS_SELECTOR,
                                  'a[href*="defaults__volume_quotas"]')

    def __init__(self, driver, conf):
        super(DefaultsPage, self).__init__(driver, conf)
        self._page_title = "Defaults"

    def _get_compute_quota_row(self, name):
        return self.default_compute_quotas_table.get_row(
            self.QUOTAS_TABLE_NAME_COLUMN, name)

    def _get_volume_quota_row(self, name):
        return self.default_volume_quotas_table.get_row(
            self.QUOTAS_TABLE_NAME_COLUMN, name)

    @property
    def default_compute_quotas_table(self):
        return DefaultQuotasTable(self.driver, self.conf)

    @property
    def default_volume_quotas_table(self):
        return DefaultVolumeQuotasTable(self.driver, self.conf)

    @property
    def compute_quota_values(self):
        quota_dict = {}
        for row in self.default_compute_quotas_table.rows:
            if row.cells[self.QUOTAS_TABLE_NAME_COLUMN].text in \
                    self.DEFAULT_COMPUTE_QUOTA_NAMES:
                quota_dict[row.cells[self.QUOTAS_TABLE_NAME_COLUMN].text] =\
                    int(row.cells[self.QUOTAS_TABLE_LIMIT_COLUMN].text)
        return quota_dict

    @property
    def volume_quota_values(self):
        quota_dict = {}
        for row in self.default_volume_quotas_table.rows:
            if row.cells[self.QUOTAS_TABLE_NAME_COLUMN].text in \
                    self.DEFAULT_VOLUME_QUOTA_NAMES:
                quota_dict[row.cells[self.QUOTAS_TABLE_NAME_COLUMN].text] =\
                    int(row.cells[self.QUOTAS_TABLE_LIMIT_COLUMN].text)
        return quota_dict

    @property
    def volume_quotas_tab(self):
        return self._get_element(*self._volume_quotas_tab_locator)

    def update_compute_defaults(self, add_up):
        update_form = self.default_compute_quotas_table.update()
        update_form.injected_file_content_bytes.value = \
            int(update_form.injected_file_content_bytes.value) + add_up

        update_form.metadata_items.value = \
            int(update_form.metadata_items.value) + add_up

        update_form.server_group_members.value = \
            int(update_form.server_group_members.value) + add_up

        update_form.server_groups.value = \
            int(update_form.server_groups.value) + add_up

        update_form.ram.value = int(update_form.ram.value) + add_up
        update_form.key_pairs.value = int(update_form.key_pairs.value) + add_up
        update_form.injected_file_path_bytes.value = \
            int(update_form.injected_file_path_bytes.value) + add_up

        update_form.instances.value = int(update_form.instances.value) + add_up
        update_form.injected_files.value = int(
            update_form.injected_files.value) + add_up
        update_form.cores.value = int(update_form.cores.value) + add_up

        update_form.submit()

    def update_volume_defaults(self, add_up):
        update_form = self.default_volume_quotas_table.update()
        update_form.switch_to(self.VOLUMES_TAB_INDEX)
        update_form.volumes.value = int(update_form.volumes.value) + add_up
        update_form.gigabytes.value = int(update_form.gigabytes.value) + add_up
        update_form.snapshots.value = int(update_form.snapshots.value) + add_up
        update_form.submit()

    def is_compute_quota_a_match(self, quota_name, limit):
        row = self._get_compute_quota_row(quota_name)
        return row.cells[self.QUOTAS_TABLE_LIMIT_COLUMN].text == str(limit)

    def is_volume_quota_a_match(self, quota_name, limit):
        row = self._get_volume_quota_row(quota_name)
        return row.cells[self.QUOTAS_TABLE_LIMIT_COLUMN].text == str(limit)

    def go_to_volume_quotas_tab(self):
        self.volume_quotas_tab.click()
