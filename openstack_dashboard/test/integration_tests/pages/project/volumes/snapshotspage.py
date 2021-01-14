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
from openstack_dashboard.test.integration_tests.pages.project.volumes.\
    volumespage import VolumesPage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class VolumesnapshotsTable(tables.TableRegion):
    name = 'volume_snapshots'
    marker_name = 'snapshot_marker'
    prev_marker_name = 'prev_snapshot_marker'

    EDIT_SNAPSHOT_FORM_FIELDS = ("name", "description")

    CREATE_VOLUME_FORM_FIELDS = (
        "name", "description", "snapshot_source", "size")

    @tables.bind_table_action('delete')
    def delete_volume_snapshots(self, delete_button):
        """Batch Delete table action."""
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('delete')
    def delete_volume_snapshot(self, delete_button, row):
        """Per-entity delete row action."""
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('edit')
    def edit_snapshot(self, edit_button, row):
        edit_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.EDIT_SNAPSHOT_FORM_FIELDS)

    @tables.bind_row_action('create_from_snapshot')
    def create_volume(self, create_volume_button, row):
        create_volume_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.CREATE_VOLUME_FORM_FIELDS)


class SnapshotsPage(basepage.BaseNavigationPage):
    SNAPSHOT_TABLE_NAME_COLUMN = 'Name'
    SNAPSHOT_TABLE_STATUS_COLUMN = 'Status'
    SNAPSHOT_TABLE_VOLUME_NAME_COLUMN = 'Volume Name'
    _volumes_tab_locator = (
        by.By.CSS_SELECTOR,
        'a[href*="tab=volumes_and_snapshots__volumes_tab"]')

    def __init__(self, driver, conf):
        super().__init__(driver, conf)
        self._page_title = "Volume Snapshots"

    @property
    def volumesnapshots_table(self):
        return VolumesnapshotsTable(self.driver, self.conf)

    def switch_to_volumes_tab(self):
        self._get_element(*self._volumes_tab_locator).click()
        return VolumesPage(self.driver, self.conf)

    def _get_row_with_volume_snapshot_name(self, name):
        return self.volumesnapshots_table.get_row(
            self.SNAPSHOT_TABLE_NAME_COLUMN,
            name)

    def is_snapshot_present(self, name):
        return bool(self._get_row_with_volume_snapshot_name(name))

    def delete_volume_snapshot(self, name):
        row = self._get_row_with_volume_snapshot_name(name)
        confirm_form = self.volumesnapshots_table.delete_volume_snapshot(row)
        confirm_form.submit()

    def delete_volume_snapshots(self, names):
        for name in names:
            row = self._get_row_with_volume_snapshot_name(name)
            row.mark()
        confirm_form = self.volumesnapshots_table.delete_volume_snapshots()
        confirm_form.submit()

    def is_volume_snapshot_deleted(self, name):
        return self.volumesnapshots_table.is_row_deleted(
            lambda: self._get_row_with_volume_snapshot_name(name))

    def is_volume_snapshot_available(self, name):
        def cell_getter():
            row = self._get_row_with_volume_snapshot_name(name)
            return row and row.cells[self.SNAPSHOT_TABLE_STATUS_COLUMN]

        return bool(self.volumesnapshots_table.wait_cell_status(cell_getter,
                                                                'Available'))

    def get_volume_name(self, snapshot_name):
        row = self._get_row_with_volume_snapshot_name(snapshot_name)
        return row.cells[self.SNAPSHOT_TABLE_VOLUME_NAME_COLUMN].text

    def edit_snapshot(self, name, new_name=None, description=None):
        row = self._get_row_with_volume_snapshot_name(name)
        snapshot_edit_form = self.volumesnapshots_table.edit_snapshot(row)
        if new_name:
            snapshot_edit_form.name.text = new_name
        if description:
            snapshot_edit_form.description.text = description
        snapshot_edit_form.submit()

    def create_volume_from_snapshot(self, snapshot_name, volume_name=None,
                                    description=None, volume_size=None):
        row = self._get_row_with_volume_snapshot_name(snapshot_name)
        volume_form = self.volumesnapshots_table.create_volume(row)
        if volume_name:
            volume_form.name.text = volume_name
        if description:
            volume_form.description.text = description
        if volume_size is None:
            volume_size = self.conf.volume.volume_size
        volume_form.size.value = volume_size
        volume_form.submit()
