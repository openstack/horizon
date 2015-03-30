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


class ImagesPage(basepage.BaseNavigationPage):

    DEFAULT_IMAGE_SOURCE = 'url'
    DEFAULT_IMAGE_FORMAT = 'qcow2'
    DEFAULT_ACCESSIBILITY = False
    DEFAULT_PROTECTION = False
    IMAGES_TABLE_NAME_COLUMN_INDEX = 0
    IMAGES_TABLE_STATUS_COLUMN_INDEX = 2

    _images_table_locator = (by.By.ID, 'images')

    IMAGES_TABLE_ACTIONS = ("create_image", "delete_images")
    IMAGES_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "launch",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: ("create_volume",)
    }

    CREATE_IMAGE_FORM_FIELDS = (
        "name", "description", "image_source", "image_location",
        "image_file", "format", "architecture", "minimum_disk",
        "minimum_ram", "public", "protected"
    )

    def __init__(self, driver, conf):
        super(ImagesPage, self).__init__(driver, conf)
        self._page_title = "Images"

    def _get_row_with_image_name(self, name):
        return self.images_table.get_row(
            self.IMAGES_TABLE_NAME_COLUMN_INDEX, name)

    @property
    def images_table(self):
        src_elem = self._get_element(*self._images_table_locator)
        return tables.ComplexActionTableRegion(self.driver,
                                               self.conf, src_elem,
                                               self.IMAGES_TABLE_ACTIONS,
                                               self.IMAGES_TABLE_ROW_ACTIONS
                                               )

    @property
    def create_image_form(self):
        return forms.FormRegion(self.driver, self.conf, None,
                                self.CREATE_IMAGE_FORM_FIELDS)

    @property
    def confirm_delete_images_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def create_image(self, name, description=None,
                     image_source=DEFAULT_IMAGE_SOURCE,
                     location=None, image_file=None,
                     image_format=DEFAULT_IMAGE_FORMAT,
                     is_public=DEFAULT_ACCESSIBILITY,
                     is_protected=DEFAULT_PROTECTION):
        self.images_table.create_image.click()
        self.create_image_form.name.text = name
        if description is not None:
            self.create_image_form.description.text = description
        self.create_image_form.image_source.value = image_source
        if image_source == 'url':
            if location is None:
                self.create_image_form.image_location.text = \
                    self.conf.image.http_image
            else:
                self.create_image_form.location.text = location
        else:
            self.create_image_form.image_file.choose(image_file)
        self.create_image_form.format.value = image_format
        if is_public:
            self.create_image_form.public.mark()
        if is_protected:
            self.create_image_form.protected.mark()
        self.create_image_form.submit.click()
        self._wait_till_spinner_disappears()

    def delete_image(self, name):
        row = self._get_row_with_image_name(name)
        row.mark()
        self.images_table.delete_images.click()
        self.confirm_delete_images_form.submit.click()
        self._wait_till_spinner_disappears()

    def is_image_present(self, name):
        return bool(self._get_row_with_image_name(name))

    def is_image_active(self, name):
        row = self._get_row_with_image_name(name)
        return row.cells[self.IMAGES_TABLE_STATUS_COLUMN_INDEX].text == \
            'Active'

    def wait_until_image_active(self, name):
        self._wait_until(lambda x: self.is_image_active(name))
