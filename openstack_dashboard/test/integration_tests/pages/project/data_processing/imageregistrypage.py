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


class ImageregistryPage(basepage.BaseNavigationPage):

    _image_table_locator = (by.By.CSS_SELECTOR, 'table#image_registry')
    _unregister_form_locator = (by.By.CSS_SELECTOR, 'div.modal-dialog')
    _register_form_locator = (by.By.CSS_SELECTOR, 'div.modal-dialog')

    IMAGE_TABLE_ACTIONS = ("register_image", "unregister_images")
    IMAGE_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "edit_tags",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: ("unregister_image",)
    }
    TABLE_IMAGE_COLUMN = 0

    REGISTER_FORM_IMAGE = "image"
    REGISTER_FORM_USER_NAME = "user_name"
    REGISTER_FORM_DESCRIPTION = "description"
    REGISTER_FORM_FIELDS = (REGISTER_FORM_IMAGE, REGISTER_FORM_USER_NAME,
                            REGISTER_FORM_DESCRIPTION)

    def __init__(self, driver, conf):
        super(ImageregistryPage, self).__init__(driver, conf)
        self._page_title = "Data Processing"

    def _get_row_with_image_name(self, name):
        return self.image_table.get_row(self.TABLE_IMAGE_COLUMN, name)

    @property
    def image_table(self):
        src_elem = self._get_element(*self._image_table_locator)
        return tables.ComplexActionTableRegion(self.driver, self.conf,
                                               src_elem,
                                               self.IMAGE_TABLE_ACTIONS,
                                               self.IMAGE_TABLE_ROW_ACTIONS)

    @property
    def unregister_form(self):
        src_elem = self._get_element(*self._unregister_form_locator)
        return forms.BaseFormRegion(self.driver, self.conf, src_elem)

    @property
    def register_form(self):
        src_elem = self._get_element(*self._register_form_locator)
        return forms.FormRegion(self.driver, self.conf, src_elem,
                                self.REGISTER_FORM_FIELDS)

    def is_image_registered(self, name):
        return bool(self._get_row_with_image_name(name))

    def unregister_image(self, name):
        self._get_row_with_image_name(name).mark()
        self.image_table.unregister_images.click()
        self.unregister_form.submit.click()

    def register_image(self, image, user_name, description):
        self.image_table.register_image.click()
        self.register_form.image.text = image
        self.register_form.user_name.text = user_name
        self.register_form.description.text = description
        self.register_form.submit.click()

    def wait_until_image_registered(self, name):
        self._wait_until(lambda x: self.is_image_registered(name))
