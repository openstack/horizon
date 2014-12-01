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
import six

from selenium.webdriver.common import by
import selenium.webdriver.support.ui as Support

from openstack_dashboard.test.integration_tests.regions import baseregion
from openstack_dashboard.test.integration_tests.regions import exceptions


class FieldFactory(baseregion.BaseRegion):
    """Factory for creating form field objects."""

    FORM_FIELDS_TYPES = set()

    def make_form_field(self):
        for form_type in self.FORM_FIELDS_TYPES:
            if self._is_element_present(*form_type._element_locator):
                return form_type(self.driver, self.conf, self.src_elem)
        raise exceptions.UnknownFormFieldTypeException()

    @classmethod
    def register_field_cls(cls, field_class, base_classes=None):
        """Register new field class.

        Add new field class and remove all base classes from the set of
        registered classes as they should not be in.
        """
        cls.FORM_FIELDS_TYPES.add(field_class)
        cls.FORM_FIELDS_TYPES -= set(base_classes)


class MetaBaseFormFieldRegion(type):
    """Register form field class in FieldFactory."""

    def __init__(cls, name, bases, dct):
        FieldFactory.register_field_cls(cls, bases)
        super(MetaBaseFormFieldRegion, cls).__init__(name, bases, dct)


@six.add_metaclass(MetaBaseFormFieldRegion)
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


class BaseTextFormFieldRegion(BaseFormFieldRegion):

    _element_locator = None

    @property
    def text(self):
        return self.element.text

    @text.setter
    def text(self, text):
        self._fill_field_element(text, self.element)


class TextInputFormFieldRegion(BaseTextFormFieldRegion):
    """Text input box."""

    _element_locator = (by.By.CSS_SELECTOR, 'div > input[type=text]')


class PasswordInputFormFieldRegion(BaseTextFormFieldRegion):
    """Password text input box."""

    _element_locator = (by.By.CSS_SELECTOR, 'div > input[type=password]')


class IntegerFormFieldRegion(BaseFormFieldRegion):
    """Integer input box."""

    _element_locator = (by.By.CSS_SELECTOR, 'div > input[type=number]')

    @property
    def value(self):
        return self.element.get_attribute("value")

    @value.setter
    def value(self, value):
        self._fill_field_element(value, self.element)


class SelectFormFieldRegion(BaseFormFieldRegion):
    """Select box field."""

    _element_locator = (by.By.CSS_SELECTOR, 'div > select')

    @property
    def element(self):
        select = self._get_element(*self._element_locator)
        return Support.Select(select)

    @property
    def values(self):
        results = []
        for option in self.element.all_selected_options:
            results.append(option.get_attribute('value'))
        return results

    @property
    def text(self):
        return self.element.first_selected_option.text

    @text.setter
    def text(self, text):
        self.element.select_by_visible_text(text)

    @property
    def value(self):
        return self.element.first_selected_option.get_attribute('value')

    @value.setter
    def value(self, value):
        self.element.select_by_value(value)


class BaseFormRegion(baseregion.BaseRegion):
    """Base class for forms."""

    _submit_locator = (by.By.CSS_SELECTOR, '*.btn.btn-primary')
    _cancel_locator = (by.By.CSS_SELECTOR, '*.btn.cancel')
    _default_form_locator = (by.By.CSS_SELECTOR, 'div.modal-dialog')

    def __init__(self, driver, conf, src_elem=None):
        """In most cases forms can be located through _default_form_locator,
        so specifying source element can be skipped.
        """
        if src_elem is None:
            # fake self.src_elem must be set up in order self._get_element work
            self.src_elem = driver
            src_elem = self._get_element(*self._default_form_locator)
        super(BaseFormRegion, self).__init__(driver, conf, src_elem)

    @property
    def submit(self):
        return self._get_element(*self._submit_locator)

    @property
    def cancel(self):
        return self._get_element(*self._cancel_locator)


class FormRegion(BaseFormRegion):
    """Standard form."""

    _header_locator = (by.By.CSS_SELECTOR, 'div.modal-header > h3')
    _side_info_locator = (by.By.CSS_SELECTOR, 'div.right')
    _fields_locator = (by.By.CSS_SELECTOR, 'fieldset > div.form-group')

    # private methods
    def __init__(self, driver, conf, src_elem, form_field_names):
        super(self.__class__, self).__init__(driver, conf, src_elem)
        self.form_field_names = form_field_names
        self._init_form_fields()

    # protected methods
    def _init_form_fields(self):
        self._init_dynamic_properties(self.form_field_names,
                                      self._get_form_fields)

    def _get_form_fields(self):
        fields_els = self._get_elements(*self._fields_locator)
        form_fields = []
        try:
            self._turn_off_implicit_wait()
            for elem in fields_els:
                field_factory = FieldFactory(self.driver, self.conf, elem)
                form_fields.append(field_factory.make_form_field())
        finally:
            self._turn_on_implicit_wait()
        return form_fields

    # properties
    @property
    def header(self):
        """Form header."""
        return self._get_element(*self._header_locator)

    @property
    def sideinfo(self):
        """Right part of form, usually contains description."""
        return self._get_element(*self._side_info_locator)

    @property
    def fields(self):
        """List of all fields that form contains."""
        return self._get_form_fields()


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
        self.submit.click()

    def _set_from_field(self, value):
        self._fill_field_element(value, self.from_date)

    def _set_to_field(self, value):
        self._fill_field_element(value, self.to_date)
