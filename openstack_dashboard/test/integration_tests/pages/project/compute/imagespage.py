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

from openstack_dashboard.test.integration_tests.pages.project.compute.\
    instancespage import InstancesPage
from openstack_dashboard.test.integration_tests.pages.project.volumes.\
    volumespage import VolumesPage


# TODO(bpokorny): Set the default source back to 'url' once Glance removes
# the show_multiple_locations option, and if the default devstack policies
# allow setting locations.
DEFAULT_IMAGE_SOURCE = 'file'
DEFAULT_IMAGE_FORMAT = 'qcow2'
DEFAULT_ACCESSIBILITY = False
DEFAULT_PROTECTION = False
IMAGES_TABLE_NAME_COLUMN = 'name'
IMAGES_TABLE_STATUS_COLUMN = 'status'
IMAGES_TABLE_FORMAT_COLUMN = 'disk_format'


class ImagesTable(tables.TableRegion):
    name = "images"

    CREATE_IMAGE_FORM_FIELDS = (
        "name", "description", "image_file", "kernel", "ramdisk",
        "disk_format", "architecture", "min_disk", "min_ram",
        "is_public", "protected"
    )

    CREATE_VOLUME_FROM_IMAGE_FORM_FIELDS = (
        "name", "description", "image_source",
        "type", "size", "availability_zone")

    LAUNCH_INSTANCE_FROM_FIELDS = ((
        "availability_zone", "name", "flavor",
        "count", "source_type", "instance_snapshot_id",
        "volume_id", "volume_snapshot_id", "image_id", "volume_size",
        "vol_delete_on_instance_delete"),
        ("keypair", "groups"),
        ("script_source", "script_upload", "script_data"),
        ("disk_config", "config_drive")
    )

    EDIT_IMAGE_FORM_FIELDS = (
        "name", "description", "disk_format", "min_disk",
        "min_ram", "public", "protected"
    )

    @tables.bind_table_action('create')
    def create_image(self, create_button):
        create_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.CREATE_IMAGE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_image(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('create_volume_from_image')
    def create_volume(self, create_volume, row):
        create_volume.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_VOLUME_FROM_IMAGE_FORM_FIELDS)

    @tables.bind_row_action('launch_image')
    def launch_instance(self, launch_instance, row):
        launch_instance.click()
        return forms.TabbedFormRegion(
            self.driver, self.conf,
            field_mappings=self.LAUNCH_INSTANCE_FROM_FIELDS)

    @tables.bind_row_action('update_metadata')
    def update_metadata(self, metadata_button, row):
        metadata_button.click()
        return forms.MetadataFormRegion(self.driver, self.conf)

    @tables.bind_row_action('delete')
    def delete_image_via_row_action(self, delete_button, row):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('edit')
    def edit_image(self, edit_button, row):
        edit_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.EDIT_IMAGE_FORM_FIELDS)

    @tables.bind_row_anchor_column(IMAGES_TABLE_NAME_COLUMN)
    def go_to_image_description_page(self, row_link, row):
        row_link.click()
        return forms.ItemTextDescription(self.driver, self.conf)


class ImagesPage(basepage.BaseNavigationPage):

    def __init__(self, driver, conf):
        super(ImagesPage, self).__init__(driver, conf)
        self._page_title = "Images"

    def _get_row_with_image_name(self, name):
        return self.images_table.get_row(IMAGES_TABLE_NAME_COLUMN, name)

    @property
    def images_table(self):
        return ImagesTable(self.driver, self.conf)

    def create_image(self, name, description=None,
                     image_source_type=DEFAULT_IMAGE_SOURCE,
                     location=None, image_file=None,
                     image_format=DEFAULT_IMAGE_FORMAT,
                     is_public=DEFAULT_ACCESSIBILITY,
                     is_protected=DEFAULT_PROTECTION):
        create_image_form = self.images_table.create_image()
        create_image_form.name.text = name
        if description is not None:
            create_image_form.description.text = description
        # TODO(bpokorny): Add this back once the show_multiple_locations
        # option is removed from Glance
        # create_image_form.source_type.value = image_source_type
        if image_source_type == 'url':
            if location is None:
                create_image_form.image_url.text = \
                    self.conf.image.http_image
            else:
                create_image_form.image_url.text = location
        else:
            create_image_form.image_file.choose(image_file)
        create_image_form.disk_format.value = image_format
        if is_public:
            create_image_form.is_public.mark()
        if is_protected:
            create_image_form.protected.mark()
        create_image_form.submit()

    def delete_image(self, name):
        row = self._get_row_with_image_name(name)
        row.mark()
        confirm_delete_images_form = self.images_table.delete_image()
        confirm_delete_images_form.submit()

    def add_custom_metadata(self, name, metadata):
        row = self._get_row_with_image_name(name)
        update_metadata_form = self.images_table.update_metadata(row)
        for field_name, value in metadata.items():
            update_metadata_form.add_custom_field(field_name, value)
        update_metadata_form.submit()

    def check_image_details(self, name, dict_with_details):
        row = self._get_row_with_image_name(name)
        matches = []
        description_page = self.images_table.go_to_image_description_page(row)
        content = description_page.get_content()

        for name, value in content.items():
            if name in dict_with_details:
                if dict_with_details[name] in value:
                    matches.append(True)
        return matches

    def edit_image(self, name, new_name=None, description=None,
                   min_disk=None, min_ram=None,
                   public=None, protected=None):
        row = self._get_row_with_image_name(name)
        confirm_edit_images_form = self.images_table.edit_image(row)

        if new_name is not None:
            confirm_edit_images_form.name.text = new_name

        if description is not None:
            confirm_edit_images_form.description.text = description

        if min_disk is not None:
            confirm_edit_images_form.min_disk.value = min_disk

        if min_ram is not None:
            confirm_edit_images_form.min_ram.value = min_ram

        if public is True:
            confirm_edit_images_form.public.mark()
        elif public is False:
            confirm_edit_images_form.public.unmark()

        if protected is True:
            confirm_edit_images_form.protected.mark()
        elif protected is False:
            confirm_edit_images_form.protected.unmark()

        confirm_edit_images_form.submit()

    def delete_image_via_row_action(self, name):
        row = self._get_row_with_image_name(name)
        delete_image_form = self.images_table.delete_image_via_row_action(row)
        delete_image_form.submit()

    def is_image_present(self, name):
        return bool(self._get_row_with_image_name(name))

    def is_image_active(self, name):
        def cell_getter():
            row = self._get_row_with_image_name(name)
            return row and row.cells[IMAGES_TABLE_STATUS_COLUMN]

        return bool(self.images_table.wait_cell_status(cell_getter, 'Active'))

    def wait_until_image_active(self, name):
        self._wait_until(lambda x: self.is_image_active(name))

    def get_image_format(self, name):
        row = self._get_row_with_image_name(name)
        return row.cells[IMAGES_TABLE_FORMAT_COLUMN].text

    def create_volume_from_image(self, name, volume_name=None,
                                 description=None,
                                 volume_size=None):
        row = self._get_row_with_image_name(name)
        create_volume_form = self.images_table.create_volume(row)
        if volume_name is not None:
            create_volume_form.name.text = volume_name
        if description is not None:
            create_volume_form.description.text = description
        create_volume_form.image_source = name
        create_volume_form.size.value = volume_size if volume_size \
            else self.conf.volume.volume_size
        create_volume_form.availability_zone.value = \
            self.conf.launch_instances.available_zone
        create_volume_form.submit()
        return VolumesPage(self.driver, self.conf)

    def launch_instance_from_image(self, name, instance_name,
                                   instance_count=1, flavor=None):
        row = self._get_row_with_image_name(name)
        launch_instance = self.images_table.launch_instance(row)
        launch_instance.availability_zone.value = \
            self.conf.launch_instances.available_zone
        launch_instance.name.text = instance_name
        if flavor is None:
            flavor = self.conf.launch_instances.flavor
        launch_instance.flavor.text = flavor
        launch_instance.count.value = instance_count
        launch_instance.submit()
        return InstancesPage(self.driver, self.conf)


class ImagesPageNG(ImagesPage):
    _resource_page_header_locator = (by.By.CSS_SELECTOR,
                                     'hz-resource-panel hz-page-header h1')

    @property
    def header(self):
        return self._get_element(*self._resource_page_header_locator)
