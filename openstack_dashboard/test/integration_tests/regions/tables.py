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

import functools

from django.utils import html
from selenium.common import exceptions
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.regions import baseregion

NORMAL_COLUMN_CLASS = 'normal_column'


class RowRegion(baseregion.BaseRegion):
    """Classic table row."""

    _cell_locator = (by.By.CSS_SELECTOR, 'td.%s' % NORMAL_COLUMN_CLASS)
    _row_checkbox_locator = (
        by.By.CSS_SELECTOR,
        'td .themable-checkbox [type="checkbox"] + label'
    )

    def __init__(self, driver, conf, src_elem, column_names):
        self.column_names = column_names
        super().__init__(driver, conf, src_elem)

    @property
    def cells(self):
        elements = self._get_elements(*self._cell_locator)
        return {column_name: elements[i]
                for i, column_name in enumerate(self.column_names)}

    def mark(self):
        chck_box = self._get_element(*self._row_checkbox_locator)
        chck_box.click()


class TableRegion(baseregion.BaseRegion):
    """Basic class representing table object."""

    _heading_locator = (by.By.CSS_SELECTOR, 'h3.table_title')
    _columns_names_locator = (by.By.CSS_SELECTOR, 'thead > tr > th')
    _footer_locator = (by.By.CSS_SELECTOR, 'tfoot > tr > td > span')
    _rows_locator = (by.By.CSS_SELECTOR, 'tbody > tr')
    _empty_table_locator = (by.By.CSS_SELECTOR, 'tbody > tr.empty')
    _search_field_locator = (by.By.CSS_SELECTOR,
                             'div.table_search input.form-control')
    _search_button_locator = (by.By.CSS_SELECTOR,
                              'div.table_search > button')
    _search_option_locator = (by.By.CSS_SELECTOR,
                              'div.table_search > .themable-select')
    _cell_progress_bar_locator = (by.By.CSS_SELECTOR, 'div.progress-bar')
    _warning_cell_locator = (by.By.CSS_SELECTOR, 'td.warning')
    _default_form_locator = (by.By.CSS_SELECTOR, 'div.modal-dialog')
    marker_name = 'marker'
    prev_marker_name = 'prev_marker'

    def _table_locator(self, table_name):
        return by.By.CSS_SELECTOR, 'table#%s' % table_name

    @property
    def _next_locator(self):
        return by.By.CSS_SELECTOR, 'a[href^="?%s"]' % self.marker_name

    @property
    def _prev_locator(self):
        return by.By.CSS_SELECTOR, 'a[href^="?%s"]' % self.prev_marker_name

    def _search_menu_value_locator(self, value):
        return (by.By.CSS_SELECTOR,
                'ul.dropdown-menu a[data-select-value="%s"]' % value)

    def _cell_progress_bar_getter(self):
        return self.driver.find_element(*self._cell_progress_bar_locator)

    def _warning_cell_getter(self):
        return self.driver.find_element(*self._warning_cell_locator)

    def _form_getter(self):
        return self.driver.find_element(*self._default_form_locator)

    def __init__(self, driver, conf):
        self._default_src_locator = self._table_locator(self.__class__.name)
        super().__init__(driver, conf)

    @property
    def heading(self):
        return self._get_element(*self._heading_locator)

    @property
    def rows(self):
        if self._is_element_present(*self._empty_table_locator):
            return []
        else:
            return self._get_rows()

    @property
    def column_names(self):
        names = []
        for element in self._get_elements(*self._columns_names_locator):
            classes = element.get_attribute('class').split()
            if NORMAL_COLUMN_CLASS in classes:
                names.append(element.text)
        return names

    @property
    def footer(self):
        return self._get_element(*self._footer_locator)

    def filter(self, value):
        self._set_search_field(value)
        self._click_search_btn()
        self.driver.implicitly_wait(5)

    def set_filter_value(self, value):
        self.wait_till_element_disappears(self._form_getter)
        js_cmd = ("$('ul.dropdown-menu').find(\"a[data-select-value='%s']\")."
                  "click();" % (html.escape(value)))
        self.driver.execute_script(js_cmd)

    def get_row(self, column_name, text, exact_match=True):
        """Get row that contains specified text in specified column.

        In case exact_match is set to True, text contained in row must equal
        searched text, otherwise occurrence of searched text in the column
        text will result in row match.
        """
        def get_text(element):
            text = element.get_attribute('data-selenium')
            return text or element.text

        # wait until cells actions are completed eg: downloading image,
        # uploading image, creating, deleting etc.
        self.wait_till_element_disappears(self._cell_progress_bar_getter)
        self.wait_till_element_disappears(self._warning_cell_getter)

        for row in self.rows:
            try:
                cell = row.cells[column_name]
                if exact_match and text == get_text(cell):
                    return row
                if not exact_match and text in get_text(cell):
                    return row
            # NOTE(tsufiev): if a row was deleted during iteration
            except exceptions.StaleElementReferenceException:
                pass
        return None

    def _set_search_field(self, value):
        srch_field = self._get_element(*self._search_field_locator)
        srch_field.clear()
        srch_field.send_keys(value)

    def _click_search_btn(self):
        btn = self._get_element(*self._search_button_locator)
        btn.click()

    def _get_rows(self, *args):
        return [RowRegion(self.driver, self.conf, elem, self.column_names)
                for elem in self._get_elements(*self._rows_locator)]

    def _is_row_deleted(self, evaluator):
        def predicate(driver):
            if self._is_element_present(*self._empty_table_locator):
                return True
            with self.waits_disabled():
                return evaluator()
        try:
            self._wait_until(predicate)
        except exceptions.TimeoutException:
            return False
        except IndexError:
            return True
        return True

    def is_row_deleted(self, row_getter):
        return self._is_row_deleted(
            lambda: not self._is_element_displayed(row_getter()))

    def are_rows_deleted(self, rows_getter):
        # wait until rows are deleted.
        self.wait_till_element_disappears(self._warning_cell_getter)

        return self._is_row_deleted(
            lambda: all([not self._is_element_displayed(row) for row
                         in rows_getter()]))

    def wait_cell_status(self, cell_getter, statuses):
        if not isinstance(statuses, (list, tuple)):
            statuses = (statuses,)
        try:
            return self._wait_till_text_present_in_element(cell_getter,
                                                           statuses)
        except exceptions.TimeoutException:
            return False

    def is_next_link_available(self):
        try:
            self._turn_off_implicit_wait()
            return self._is_element_visible(*self._next_locator)
        finally:
            self._turn_on_implicit_wait()

    def is_prev_link_available(self):
        try:
            self._turn_off_implicit_wait()
            return self._is_element_visible(*self._prev_locator)
        finally:
            self._turn_on_implicit_wait()

    def turn_next_page(self):
        if self.is_next_link_available():
            lnk = self._get_element(*self._next_locator)
            lnk.click()

    def turn_prev_page(self):
        if self.is_prev_link_available():
            lnk = self._get_element(*self._prev_locator)
            lnk.click()

    def get_column_data(self, name_column='Name'):
        return [row.cells[name_column].text for row in self.rows]

    def assert_definition(self,
                          expected_table_definition,
                          sorting=False,
                          name_column='Name'):
        """Checks that actual table is expected one.

        Items to compare: 'next' and 'prev' links, count of rows and names of
        elements in list
        :param expected_table_definition: expected values (dictionary)
        :param sorting: boolean arg specifying whether to sort actual names
        :return:
        """
        names = self.get_column_data(name_column)
        if sorting:
            names.sort()
        actual_table = {'Next': self.is_next_link_available(),
                        'Prev': self.is_prev_link_available(),
                        'Count': len(self.rows),
                        'Names': names}
        self.assertDictEqual(actual_table, expected_table_definition)


def bind_table_action(action_name):
    """Decorator to bind table region method to an actual table action button.

    Many table actions when started (by clicking a corresponding button
    in UI) lead to some form showing up. To further interact with this form,
    a Python/ Selenium wrapper needs to be created for it. It is very
    convenient to return this newly created wrapper in the same method that
    initiates clicking an actual table action button. Binding the method to a
    button is performed behind the scenes in this decorator.

    .. param:: action_name

        Part of the action button id which is specific to action itself. It
        is safe to use action `name` attribute from the dashboard tables.py
        code.
    """
    _actions_locator = (by.By.CSS_SELECTOR, 'div.table_actions > button, a')

    def decorator(method):
        @functools.wraps(method)
        def wrapper(table):
            actions = table._get_elements(*_actions_locator)
            action_element = None
            for action in actions:
                target_action_id = '%s__action_%s' % (table.name, action_name)
                if action.get_attribute('id') == target_action_id:
                    action_element = action
                    break
            if action_element is None:
                msg = "Could not bind method '%s' to action control '%s'" % (
                    method.__name__, action_name)
                raise ValueError(msg)
            return method(table, action_element)
        return wrapper
    return decorator


def bind_row_action(action_name):
    """A decorator to bind table region method to an actual row action button.

    Many table actions when started (by clicking a corresponding button
    in UI) lead to some form showing up. To further interact with this form,
    a Python/ Selenium wrapper needs to be created for it. It is very
    convenient to return this newly created wrapper in the same method that
    initiates clicking an actual action button. Row action could be
    either primary (if its name is written right away on row action
    button) or secondary (if its name is inside of a button drop-down). Binding
    the method to a button and toggling the button drop-down open (in case
    a row action is secondary) is performed behind the scenes in this
    decorator.

    .. param:: action_name

        Part of the action button id which is specific to action itself. It
        is safe to use action `name` attribute from the dashboard tables.py
        code.
    """
    # NOTE(tsufiev): button tag could be either <a> or <button> - target
    # both with *. Also primary action could be single as well, do not use
    # .btn-group because of that
    primary_action_locator = (
        by.By.CSS_SELECTOR, 'td.actions_column *.btn:nth-child(1)')
    secondary_actions_opener_locator = (
        by.By.CSS_SELECTOR,
        'td.actions_column > .btn-group > *.btn:nth-child(2)')
    secondary_actions_locator = (
        by.By.CSS_SELECTOR,
        'td.actions_column > .btn-group > ul.row_actions > li > a, button')

    def decorator(method):
        @functools.wraps(method)
        def wrapper(table, row):
            def find_action(element):
                pattern = "__action_%s" % action_name
                return element.get_attribute('id').endswith(pattern)

            action_element = row._get_element(*primary_action_locator)
            if not find_action(action_element):
                action_element = None
                row._get_element(*secondary_actions_opener_locator).click()
                for element in row._get_elements(*secondary_actions_locator):
                    if find_action(element):
                        action_element = element
                        break

            if action_element is None:
                msg = "Could not bind method '%s' to action control '%s'" % (
                    method.__name__, action_name)
                raise ValueError(msg)
            return method(table, action_element, row)
        return wrapper
    return decorator


def bind_row_anchor_column(column_name):
    """A decorator to bind table region method to a anchor in a column.

    Typical examples of such tables are Project -> Compute -> Images, Admin
    -> System -> Flavors, Project -> Compute -> Instancies.
    The method can be used to follow the link in the anchor by the click.
    """

    def decorator(method):
        @functools.wraps(method)
        def wrapper(table, row):
            cell = row.cells[column_name]
            action_element = cell.find_element(
                by.By.CSS_SELECTOR, 'td.%s > a' % NORMAL_COLUMN_CLASS)
            return method(table, action_element, row)

        return wrapper
    return decorator
