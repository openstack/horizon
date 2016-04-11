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

VOLUME_SOURCE_TYPE = 'Volume'
IMAGE_SOURCE_TYPE = 'Image'


class VolumesTable(tables.TableRegion):
    name = 'volumes'

    # This form is applicable for volume creation from image only.
    # Volume creation from volume requires additional 'volume_source' field
    # which is available only in case at least one volume is already present.
    CREATE_VOLUME_FROM_IMAGE_FORM_FIELDS = (
        "name", "description", "volume_source_type", "image_source",
        "type", "size", "availability_zone")

    EDIT_VOLUME_FORM_FIELDS = ("name", "description")

    CREATE_VOLUME_SNAPSHOT_FORM_FIELDS = ("name", "description")

    EXTEND_VOLUME_FORM_FIELDS = ("new_size",)

    UPLOAD_VOLUME_FORM_FIELDS = ("image_name", "disk_format")

    @tables.bind_table_action('create')
    def create_volume(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_VOLUME_FROM_IMAGE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_volume(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('edit')
    def edit_volume(self, edit_button, row):
        edit_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.EDIT_VOLUME_FORM_FIELDS)

    @tables.bind_row_action('snapshots')
    def create_snapshot(self, create_snapshot_button, row):
        create_snapshot_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_VOLUME_SNAPSHOT_FORM_FIELDS)

    @tables.bind_row_action('extend')
    def extend_volume(self, extend_button, row):
        extend_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.EXTEND_VOLUME_FORM_FIELDS)

    @tables.bind_row_action('upload_to_image')
    def upload_volume_to_image(self, upload_button, row):
        upload_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.UPLOAD_VOLUME_FORM_FIELDS)


class VolumesPage(basepage.BaseNavigationPage):

    VOLUMES_TABLE_NAME_COLUMN = 'name'
    VOLUMES_TABLE_STATUS_COLUMN = 'status'
    VOLUMES_TABLE_TYPE_COLUMN = 'volume_type'
    VOLUMES_TABLE_SIZE_COLUMN = 'size'
    VOLUMES_TABLE_ATTACHED_COLUMN = 'attachments'

    def __init__(self, driver, conf):
        super(VolumesPage, self).__init__(driver, conf)
        self._page_title = "Volumes"

    def _get_row_with_volume_name(self, name):
        return self.volumes_table.get_row(
            self.VOLUMES_TABLE_NAME_COLUMN, name)

    @property
    def volumes_table(self):
        return VolumesTable(self.driver, self.conf)

    def create_volume(self, volume_name, description=None,
                      volume_source_type=IMAGE_SOURCE_TYPE,
                      volume_size=None,
                      volume_source=None):
        volume_form = self.volumes_table.create_volume()
        volume_form.name.text = volume_name
        if description is not None:
            volume_form.description.text = description
        volume_form.volume_source_type.text = volume_source_type
        volume_source_type = self._get_source_name(volume_form,
                                                   volume_source_type,
                                                   self.conf.launch_instances,
                                                   volume_source)
        volume_source_type[0].text = volume_source_type[1]
        if volume_size is None:
            volume_size = self.conf.volume.volume_size
        volume_form.size.value = volume_size
        if volume_source_type != "Volume":
            volume_form.type.value = self.conf.volume.volume_type
            volume_form.availability_zone.value = \
                self.conf.launch_instances.available_zone
        volume_form.submit()

    def delete_volume(self, name):
        row = self._get_row_with_volume_name(name)
        row.mark()
        confirm_delete_volumes_form = self.volumes_table.delete_volume()
        confirm_delete_volumes_form.submit()

    def edit_volume(self, name, new_name=None, description=None):
        row = self._get_row_with_volume_name(name)
        volume_edit_form = self.volumes_table.edit_volume(row)
        if new_name:
            volume_edit_form.name.text = new_name
        if description:
            volume_edit_form.description.text = description
        volume_edit_form.submit()

    def is_volume_present(self, name):
        return bool(self._get_row_with_volume_name(name))

    def is_volume_status(self, name, status):
        row = self._get_row_with_volume_name(name)
        return self.volumes_table.is_cell_status(
            lambda: row.cells[self.VOLUMES_TABLE_STATUS_COLUMN], status)

    def is_volume_deleted(self, name):
        return self.volumes_table.is_row_deleted(
            lambda: self._get_row_with_volume_name(name))

    def _get_source_name(self, volume_form, volume_source_type, conf,
                         volume_source):
        if volume_source_type == IMAGE_SOURCE_TYPE:
            return volume_form.image_source, conf.image_name
        if volume_source_type == VOLUME_SOURCE_TYPE:
            return volume_form.volume_id, volume_source

    def create_volume_snapshot(self, volume, snapshot, description='test'):
        from openstack_dashboard.test.integration_tests.pages.project.compute.\
            volumes.volumesnapshotspage import VolumesnapshotsPage
        row = self._get_row_with_volume_name(volume)
        snapshot_form = self.volumes_table.create_snapshot(row)
        snapshot_form.name.text = snapshot
        if description is not None:
            snapshot_form.description.text = description
        snapshot_form.submit()
        return VolumesnapshotsPage(self.driver, self.conf)

    def extend_volume(self, name, new_size):
        row = self._get_row_with_volume_name(name)
        extend_volume_form = self.volumes_table.extend_volume(row)
        extend_volume_form.new_size.value = new_size
        extend_volume_form.submit()

    def upload_volume_to_image(self, name, image_name, disk_format):
        row = self._get_row_with_volume_name(name)
        upload_volume_form = self.volumes_table.upload_volume_to_image(row)
        upload_volume_form.image_name.text = image_name
        upload_volume_form.disk_format.value = disk_format
        upload_volume_form.submit()

    def get_size(self, name):
        row = self._get_row_with_volume_name(name)
        size = str(row.cells[self.VOLUMES_TABLE_SIZE_COLUMN].text)
        return int(filter(str.isdigit, size))
