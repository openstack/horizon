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


class ImagesTable(tables.TableRegion):
    name = "images"
    CREATE_IMAGE_FORM_FIELDS = (
        "name", "description", "source_type", "image_url",
        "image_file", "kernel", "ramdisk",
        "disk_format", "architecture", "minimum_disk",
        "minimum_ram", "is_public", "protected"
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


class ImagesPage(basepage.BaseNavigationPage):

    DEFAULT_IMAGE_SOURCE = 'url'
    DEFAULT_IMAGE_FORMAT = 'qcow2'
    DEFAULT_ACCESSIBILITY = False
    DEFAULT_PROTECTION = False
    IMAGES_TABLE_NAME_COLUMN = 'name'
    IMAGES_TABLE_STATUS_COLUMN = 'status'

    def __init__(self, driver, conf):
        super(ImagesPage, self).__init__(driver, conf)
        self._page_title = "Images"

    def _get_row_with_image_name(self, name):
        return self.images_table.get_row(self.IMAGES_TABLE_NAME_COLUMN, name)

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
        create_image_form.source_type.value = image_source_type
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

    def is_image_present(self, name):
        return bool(self._get_row_with_image_name(name))

    def is_image_active(self, name):
        row = self._get_row_with_image_name(name)

        def cell_getter():
            return row.cells[self.IMAGES_TABLE_STATUS_COLUMN]
        try:
            self._wait_till_text_present_in_element(cell_getter, 'Active')
        except exceptions.TimeoutException:
            return False
        return True

    def wait_until_image_active(self, name):
        self._wait_until(lambda x: self.is_image_active(name))
