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

from selenium.common import exceptions
from selenium.webdriver.common import by
import selenium.webdriver.support.ui as Support

from openstack_dashboard.test.integration_tests.regions import baseregion
from openstack_dashboard.test.integration_tests.regions import menus


class FieldFactory(baseregion.BaseRegion):
    """Factory for creating form field objects."""

    FORM_FIELDS_TYPES = set()
    _element_locator_str_prefix = 'div.form-group'

    def __init__(self, driver, conf, src_elem=None):
        super(FieldFactory, self).__init__(driver, conf, src_elem)

    def fields(self):
        for field_cls in self.FORM_FIELDS_TYPES:
            locator = (by.By.CSS_SELECTOR,
                       '%s %s' % (self._element_locator_str_prefix,
                                  field_cls._element_locator_str_suffix))
            elements = super(FieldFactory, self)._get_elements(*locator)
            for element in elements:
                yield field_cls(self.driver, self.conf, element)

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
        return self.src_elem

    @property
    def name(self):
        return self.element.get_attribute('name')

    def is_required(self):
        classes = self.driver.get_attribute('class')
        return 'required' in classes

    def is_displayed(self):
        return self.element.is_displayed()


class CheckBoxMixin(object):

    @property
    def label(self):
        id_attribute = self.element.get_attribute('id')
        return self.element.find_element(
            by.By.XPATH, '../..//label[@for="{}"]'.format(id_attribute))

    def is_marked(self):
        return self.element.is_selected()

    def mark(self):
        if not self.is_marked():
            self.label.click()

    def unmark(self):
        if self.is_marked():
            self.label.click()


class CheckBoxFormFieldRegion(CheckBoxMixin, BaseFormFieldRegion):
    """Checkbox field."""

    _element_locator_str_suffix = 'input[type=checkbox]'


class ChooseFileFormFieldRegion(BaseFormFieldRegion):
    """Choose file field."""

    _element_locator_str_suffix = 'div > input[type=file]'

    def choose(self, path):
        self.element.send_keys(path)


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

    _element_locator_str_suffix = \
        'div > input[type=text], div > input[type=None]'


class PasswordInputFormFieldRegion(BaseTextFormFieldRegion):
    """Password text input box."""

    _element_locator_str_suffix = 'div > input[type=password]'


class EmailInputFormFieldRegion(BaseTextFormFieldRegion):
    """Email text input box."""

    _element_locator_str_suffix = 'div > input[type=email]'


class TextAreaFormFieldRegion(BaseTextFormFieldRegion):
    """Multi-line text input box."""

    _element_locator_str_suffix = 'div > textarea'


class IntegerFormFieldRegion(BaseFormFieldRegion):
    """Integer input box."""

    _element_locator_str_suffix = 'div > input[type=number]'

    @property
    def value(self):
        return self.element.get_attribute("value")

    @value.setter
    def value(self, value):
        self._fill_field_element(value, self.element)


class SelectFormFieldRegion(BaseFormFieldRegion):
    """Select box field."""

    _element_locator_str_suffix = 'div > select'

    def is_displayed(self):
        return self.element._el.is_displayed()

    @property
    def element(self):
        return Support.Select(self.src_elem)

    @property
    def values(self):
        results = []
        for option in self.element.all_selected_options:
            results.append(option.get_attribute('value'))
        return results

    @property
    def name(self):
        return self.element._el.get_attribute('name')

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
    def _submit_element(self):
        return self._get_element(*self._submit_locator)

    def submit(self):
        self._submit_element.click()
        self.wait_till_spinner_disappears()

    @property
    def _cancel_element(self):
        return self._get_element(*self._cancel_locator)

    def cancel(self):
        self._cancel_element.click()


class FormRegion(BaseFormRegion):
    """Standard form."""

    _header_locator = (by.By.CSS_SELECTOR, 'div.modal-header > h3')
    _side_info_locator = (by.By.CSS_SELECTOR, 'div.right')
    _fields_locator = (by.By.CSS_SELECTOR, 'fieldset')

    # private methods
    def __init__(self, driver, conf, src_elem=None, field_mappings=None):
        super(FormRegion, self).__init__(driver, conf, src_elem)
        self.field_mappings = self._prepare_mappings(field_mappings)
        self.wait_till_spinner_disappears()
        self._init_form_fields()

    def _prepare_mappings(self, field_mappings):
        if isinstance(field_mappings, tuple):
            return {item: item for item in field_mappings}
        else:
            return field_mappings

    # protected methods
    def _init_form_fields(self):
        self.fields_src_elem = self._get_element(*self._fields_locator)
        fields = self._get_form_fields()
        for accessor_name, accessor_expr in self.field_mappings.items():
            if isinstance(accessor_expr, six.string_types):
                self._dynamic_properties[accessor_name] = fields[accessor_expr]
            else:  # it is a class
                self._dynamic_properties[accessor_name] = accessor_expr(
                    self.driver, self.conf)

    def _get_form_fields(self):
        factory = FieldFactory(self.driver, self.conf, self.fields_src_elem)
        try:
            self._turn_off_implicit_wait()
            return {field.name: field for field in factory.fields()}
        finally:
            self._turn_on_implicit_wait()

    def set_field_values(self, data):
        """Set fields values

        data - {field_name: field_value, field_name: field_value ...}
        """
        for field_name in data:
            field = getattr(self, field_name, None)
            # Field form does not exist
            if field is None:
                raise AttributeError("Unknown form field name.")
            value = data[field_name]
            # if None - default value is left in field
            if value is not None:
                # all text fields
                if hasattr(field, "text"):
                    field.text = value
                # file upload field
                elif hasattr(field, "path"):
                    field.path = value
                # integers fields
                elif hasattr(field, "value"):
                    field.value = value

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


class TabbedFormRegion(FormRegion):
    """Forms that are divided with tabs.

    As example is taken form under the
    the  Project/Network/Networks/Create Network, on initialization form needs
    to have form field names divided into tuples, that represents the tabs
    and the fields located under them.

    Usage:

    form_field_names = (("network_name", "admin_state"),
                        ("create_subnet", "subnet_name", "network_address",
                         "ip_version", "gateway_ip", "disable_gateway"),
                        ("enable_dhcp", "allocation_pools", "dns_name_servers",
                         "host_routes"))
    form = TabbedFormRegion(self.conf, self.driver, None, form_field_names)
    form.network_name.text = "test_network_name"
    """

    _submit_locator = (by.By.CSS_SELECTOR, '*.btn.btn-primary[type=submit]')
    _side_info_locator = (by.By.CSS_SELECTOR, "td.help_text")

    def __init__(self, driver, conf, field_mappings=None, default_tab=0):
        self.current_tab = default_tab
        super(TabbedFormRegion, self).__init__(
            driver, conf, field_mappings=field_mappings)

    def _prepare_mappings(self, field_mappings):
        return [super(TabbedFormRegion, self)._prepare_mappings(tab_mappings)
                for tab_mappings in field_mappings]

    def _init_form_fields(self):
        self.switch_to(self.current_tab)

    def _init_tab_fields(self, tab_index):
        fieldsets = self._get_elements(*self._fields_locator)
        self.fields_src_elem = fieldsets[tab_index]
        fields = self._get_form_fields()
        current_tab_mappings = self.field_mappings[tab_index]
        for accessor_name, accessor_expr in current_tab_mappings.items():
            if isinstance(accessor_expr, six.string_types):
                self._dynamic_properties[accessor_name] = fields[accessor_expr]
            else:  # it is a class
                self._dynamic_properties[accessor_name] = accessor_expr(
                    self.driver, self.conf)

    def switch_to(self, tab_index=0):
        self.tabs.switch_to(index=tab_index)
        self._init_tab_fields(tab_index)

    @property
    def tabs(self):
        return menus.TabbedMenuRegion(self.driver, self.conf,
                                      src_elem=self.src_elem)


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


class MetadataFormRegion(BaseFormRegion):

    _input_fields = (by.By.CSS_SELECTOR, 'div.input-group')
    _custom_input_field = (by.By.XPATH, "//input[@name='customItem']")
    _custom_input_button = (by.By.CSS_SELECTOR, 'span.input-group-btn > .btn')
    _submit_locator = (by.By.CSS_SELECTOR, '.modal-footer > .btn.btn-primary')
    _cancel_locator = (by.By.CSS_SELECTOR, '.modal-footer > .btn.btn-default')

    def _form_getter(self):
        return self.driver.find_element(*self._default_form_locator)

    @property
    def custom_field_value(self):
        return self._get_element(*self._custom_input_field)

    @property
    def add_button(self):
        return self._get_element(*self._custom_input_button)

    def add_custom_field(self, field_name, field_value):
        self.custom_field_value.send_keys(field_name)
        self.add_button.click()
        for div in self._get_elements(*self._input_fields):
            if div.text in field_name:
                field = div.find_element(by.By.CSS_SELECTOR, 'input')
                if not hasattr(self, field_name):
                    self._dynamic_properties[field_name] = field
        self.set_field_value(field_name, field_value)

    def set_field_value(self, field_name, field_value):
        if hasattr(self, field_name):
            field = getattr(self, field_name)
            field.send_keys(field_value)
        else:
            raise AttributeError("Unknown form field '{}'.".format(field_name))

    def wait_till_spinner_disappears(self):
        # No spinner is invoked after the 'Save' button click
        # Will wait till the form itself disappears
        try:
            self.wait_till_element_disappears(self._form_getter)
        except exceptions.StaleElementReferenceException:
            # The form might be absent already by the time the first check
            # occurs. So just suppress the exception here.
            pass


class ItemTextDescription(baseregion.BaseRegion):

    _separator_locator = (by.By.CSS_SELECTOR, 'dl.dl-horizontal')
    _key_locator = (by.By.CSS_SELECTOR, 'dt')
    _value_locator = (by.By.CSS_SELECTOR, 'dd')

    def __init__(self, driver, conf, src=None):
        super(ItemTextDescription, self).__init__(driver, conf, src)

    def get_content(self):
        keys = []
        values = []
        for section in self._get_elements(*self._separator_locator):
            keys.extend([x.text for x in
                         section.find_elements(*self._key_locator)])
            values.extend([x.text for x in
                           section.find_elements(*self._value_locator)])
        return dict(zip(keys, values))
