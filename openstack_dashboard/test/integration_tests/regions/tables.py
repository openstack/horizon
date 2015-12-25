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
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.regions import baseregion
from openstack_dashboard.test.integration_tests.regions import menus

NORMAL_COLUMN_CLASS = 'normal_column'


class RowRegion(baseregion.BaseRegion):
    """Classic table row."""

    _cell_locator = (by.By.CSS_SELECTOR, 'td.%s' % NORMAL_COLUMN_CLASS)

    def __init__(self, driver, conf, src_elem, column_names):
        self.column_names = column_names
        super(RowRegion, self).__init__(driver, conf, src_elem)

    @property
    def cells(self):
        elements = self._get_elements(*self._cell_locator)
        return {column_name: elements[i]
                for i, column_name in enumerate(self.column_names)}


class BaseActionRowRegion(RowRegion):
    """Base class for creating ActionRow class derivative."""

    _row_checkbox_locator = (by.By.CSS_SELECTOR, 'td > input')

    def mark(self):
        chck_box = self._get_element(*self._row_checkbox_locator)
        chck_box.click()


class BtnActionRowRegion(BaseActionRowRegion):
    """Row with buttons in action column."""

    _action_locator = (by.By.CSS_SELECTOR, 'td.actions_column > button')

    def __init__(self, driver, conf, src_elem, column_names, action_name):
        super(BtnActionRowRegion, self).__init__(driver, conf, src_elem,
                                                 column_names)
        self.action_name = action_name
        self._action_id_pattern = ("%s__action_%%s" %
                                   src_elem.get_attribute('id'))
        self._init_action()

    def _init_action(self):
        self._init_dynamic_property(self.action_name, self._get_action,
                                    self._action_id_pattern)

    def _get_action(self):
        return self._get_element(*self._action_locator)

    @property
    def action(self):
        return self._get_action()


class ComplexActionRowRegion(BaseActionRowRegion):
    """Row with button and select box in action column."""

    _primary_action_locator = (by.By.CSS_SELECTOR,
                               'td.actions_column > div.btn-group > *.btn')
    _secondary_actions_dropdown_locator = (by.By.CSS_SELECTOR,
                                           'div.btn-group')

    PRIMARY_ACTION = "primary_action"
    SECONDARY_ACTIONS = "secondary_actions"

    ACTIONS_ERROR_MSG = ("Actions must be supplied in dictionary:"
                         " {%s: 'action_name', '%s': ('action_name',...)}"
                         % (PRIMARY_ACTION, SECONDARY_ACTIONS))

    def __init__(self, driver, conf, src_elem, column_names, action_names):
        super(ComplexActionRowRegion, self).__init__(driver, conf, src_elem,
                                                     column_names)
        try:
            self.primary_action_name = action_names[self.PRIMARY_ACTION]
            self.secondary_action_names = action_names[self.SECONDARY_ACTIONS]
            self._action_id_pattern = ("%s__action_%%s" %
                                       src_elem.get_attribute('id'))
            self._init_actions()
        except (TypeError, KeyError):
            raise AttributeError(self.ACTIONS_ERROR_MSG)

    def _init_actions(self):
        self._init_dynamic_property(self.primary_action_name,
                                    self._get_primary_action,
                                    self._action_id_pattern)
        self._init_dynamic_properties(self.secondary_action_names,
                                      self._get_secondary_actions,
                                      self._action_id_pattern)

    def _get_primary_action(self):
        return self._get_element(*self._primary_action_locator)

    def _get_secondary_actions(self):
        src_elem = self._get_element(*self._secondary_actions_dropdown_locator)
        dropdown = menus.DropDownMenuRegion(self.driver, self.conf, src_elem)
        return dropdown.menu_items

    @property
    def primary_action(self):
        return self._get_primary_action()

    @property
    def secondary_actions(self):
        return self._get_secondary_actions()


class BasicTableRegion(baseregion.BaseRegion):
    """Basic class representing table object."""

    _heading_locator = (by.By.CSS_SELECTOR, 'h3.table_title')
    _columns_names_locator = (by.By.CSS_SELECTOR, 'thead > tr > th')
    _footer_locator = (by.By.CSS_SELECTOR, 'tfoot > tr > td > span')
    _rows_locator = (by.By.CSS_SELECTOR, 'tbody > tr')
    _empty_table_locator = (by.By.CSS_SELECTOR, 'tbody > tr.empty')
    _search_field_locator = (by.By.CSS_SELECTOR,
                             'div.table_search.client > input')
    _search_button_locator = (by.By.CSS_SELECTOR,
                              'div.table_search.client > button')

    def _table_locator(self, table_name):
        return by.By.CSS_SELECTOR, 'table#%s' % table_name

    def __init__(self, driver, conf, table_name):
        self._default_src_locator = self._table_locator(table_name)
        super(BasicTableRegion, self).__init__(driver, conf)

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
                names.append(element.get_attribute('data-selenium'))
        return names

    @property
    def footer(self):
        return self._get_element(*self._footer_locator)

    def filter(self, value):
        self._set_search_field(value)
        self._click_search_btn()

    def get_row(self, column_name, text, exact_match=True):
        """Get row that contains specified text in specified column.

        In case exact_match is set to True, text contained in row must equal
        searched text, otherwise occurrence of searched text in the column
        text will result in row match.
        """
        def get_text(element):
            text = element.get_attribute('data-selenium')
            return text or element.text

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
        srch_field.send_keys(value)

    def _click_search_btn(self):
        btn = self._get_element(*self._search_button_locator)
        btn.click()

    def _make_row(self, elem):
        return RowRegion(self.driver, self.conf, elem, self.column_names)

    def _get_rows(self, *args):
        elements = self._get_elements(*self._rows_locator)
        return [self._make_row(elem) for elem in elements]


class ActionsTableRegion(BasicTableRegion):
    """Base class for creating derivative of BasicTableRegion that
    has some actions.
    """

    _actions_locator = (by.By.CSS_SELECTOR, 'div.table_actions > button,'
                                            ' div.table_actions > a')

    # private methods
    def __init__(self, driver, conf, table_name, action_names):
        super(ActionsTableRegion, self).__init__(driver, conf, table_name)
        self._action_id_pattern = "%s__action_%%s" % table_name
        self.action_names = action_names
        self._init_actions()

    # protected methods
    def _init_actions(self):
        """Create new methods that corresponds to picking table's
        action buttons.
        """
        self._init_dynamic_properties(self.action_names, self._get_actions,
                                      self._action_id_pattern)

    def _get_actions(self):
        return self._get_elements(*self._actions_locator)

    # properties
    @property
    def actions(self):
        return self._get_actions()


class SimpleActionsTableRegion(ActionsTableRegion):
    """Table which rows has buttons in action column."""

    def __init__(self, driver, conf, table_name, action_names,
                 row_action_name):
        super(SimpleActionsTableRegion, self).__init__(
            driver, conf, table_name, action_names)
        self.row_action_name = row_action_name

    def _make_row(self, elem):
        return BtnActionRowRegion(self.driver, self.conf, elem,
                                  self.column_names, self.row_action_name)


class ComplexActionTableRegion(ActionsTableRegion):
    """Table which has button and selectbox in the action column."""

    def __init__(self, driver, conf, table_name,
                 action_names, row_action_names):
        super(ComplexActionTableRegion, self).__init__(
            driver, conf, table_name, action_names)
        self.row_action_names = row_action_names

    def _make_row(self, elem):
        return ComplexActionRowRegion(self.driver, self.conf, elem,
                                      self.column_names, self.row_action_names)
