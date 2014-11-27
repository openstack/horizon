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

from openstack_dashboard.test.integration_tests.regions import baseregion


class BaseFormFieldRegion(baseregion.BaseRegion):
    """Base class for form fields classes."""

    _label_locator = None
    _element_locator = None

    @property
    def label(self):
        return self._get_element(*self._label_locator)

    @property
    def element(self):
        return self._get_element(*self._element_locator)

    def is_required(self):
        classes = self.driver.get_attribute('class')
        return 'required' in classes


class BaseFormRegion(baseregion.BaseRegion):
    """Base class for forms."""

    _submit_locator = (by.By.CSS_SELECTOR, 'button.btn.btn-primary,'
                                           ' a.btn.btn-primary')

    def submit(self):
        self._get_element(*self._submit_locator).click()


class DateFormRegion(BaseFormRegion):
    """Form that queries data to table that is regularly below the form,
     typical example is located on Project/Compute/Overview page.
     """

    _from_field_locator = (by.By.CSS_SELECTOR, 'input#id_start')
    _to_field_locator = (by.By.CSS_SELECTOR, 'input#id_end')

    @property
    def from_date(self):
        return self._get_element(*self._from_field_locator)

    @property
    def to_date(self):
        return self._get_element(*self._to_field_locator)

    def query(self, start, end):
        self._set_from_field(start)
        self._set_to_field(end)
        self.submit()

    def _set_from_field(self, value):
        self._fill_field_element(value, self.from_date)

    def _set_to_field(self, value):
        self._fill_field_element(value, self.to_date)
