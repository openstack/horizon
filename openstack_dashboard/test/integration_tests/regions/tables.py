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
from openstack_dashboard.test.integration_tests.regions import menus


class RowRegion(baseregion.BaseRegion):
    """Classic table row."""

    _cell_locator = (by.By.CSS_SELECTOR, 'td.normal_column')

    @property
    def cells(self):
        return self._get_elements(*self._cell_locator)


class BaseActionRowRegion(RowRegion):
    """Base class for creating ActionRow class derivative."""

    _row_checkbox_locator = (by.By.CSS_SELECTOR, 'td > input')

    def mark(self):
        chck_box = self._get_element(*self._row_checkbox_locator)
        chck_box.click()


class BtnActionRowRegion(BaseActionRowRegion):
    """Row with buttons in action column."""

    _action_locator = (by.By.CSS_SELECTOR, 'td.actions_column > button')

    def __init__(self, driver, conf, src_elem, action_name):
        super(BtnActionRowRegion, self).__init__(driver, conf, src_elem)
        self.action_name = action_name
        self._init_action()

    def _init_action(self):
        self._init_dynamic_property(self.action_name, self._get_action)

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

    def __init__(self, driver, conf, src_elem, action_names):
        super(ComplexActionRowRegion, self).__init__(driver, conf, src_elem)
        try:
            self.primary_action_name = action_names[self.PRIMARY_ACTION]
            self.secondary_action_names = action_names[self.SECONDARY_ACTIONS]
            self._init_actions()
        except (TypeError, KeyError):
            raise AttributeError(self.ACTIONS_ERROR_MSG)

    def _init_actions(self):
        self._init_dynamic_property(self.primary_action_name,
                                    self._get_primary_action)
        self._init_dynamic_properties(self.secondary_action_names,
                                      self._get_secondary_actions)

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
        return self._get_elements(*self._columns_names_locator)

    @property
    def footer(self):
        return self._get_element(*self._footer_locator)

    def filter(self, value):
        self._set_search_field(value)
        self._click_search_btn()

    def get_row(self, column_index, text, exact_match=True):
        """Get row that contains specified text in specified column.

        In case exact_match is set to True, text contained in row must equal
        searched text, otherwise occurrence of searched text in the column
        text will result in row match.
        """
        for row in self.rows:
            if exact_match and text == row.cells[column_index].text:
                return row
            if not exact_match and text in row.cells[column_index].text:
                return row
        return None

    def _set_search_field(self, value):
        srch_field = self._get_element(*self._search_field_locator)
        srch_field.send_keys(value)

    def _click_search_btn(self):
        btn = self._get_element(*self._search_button_locator)
        btn.click()

    def _get_rows(self):
        rows = []
        for elem in self._get_elements(*self._rows_locator):
            rows.append(RowRegion(self.driver, self.conf, elem))


class ActionsTableRegion(BasicTableRegion):
    """Base class for creating derivative of BasicTableRegion that
    has some actions.
    """

    _actions_locator = (by.By.CSS_SELECTOR, 'div.table_actions > button,'
                                            ' div.table_actions > a')

    # private methods
    def __init__(self, driver, conf, src_elm, action_names):
        super(ActionsTableRegion, self).__init__(driver, conf, src_elm)
        self.action_names = action_names
        self._init_actions()

    # protected methods
    def _init_actions(self):
        """Create new methods that corresponds to picking table's
        action buttons.
        """
        self._init_dynamic_properties(self.action_names, self._get_actions)

    def _get_actions(self):
        return self._get_elements(*self._actions_locator)

    # properties
    @property
    def actions(self):
        return self._get_actions()


class SimpleActionsTableRegion(ActionsTableRegion):
    """Table which rows has buttons in action column."""

    def __init__(self, driver, conf, src_elm, action_names, row_action_name):
        super(SimpleActionsTableRegion, self).__init__(driver, conf, src_elm,
                                                       action_names)
        self.row_action_name = row_action_name

    def _get_rows(self):
        rows = []
        for elem in self._get_elements(*self._rows_locator):
            rows.append(BtnActionRowRegion(self.driver, self.conf, elem,
                                           self.row_action_name))
        return rows


class ComplexActionTableRegion(ActionsTableRegion):
    """Table which has button and selectbox in the action column."""

    def __init__(self, driver, conf, src_elm, action_names, row_action_names):
        super(ComplexActionTableRegion, self).__init__(driver, conf, src_elm,
                                                       action_names)
        self.row_action_names = row_action_names

    def _get_rows(self):
        rows = []
        for elem in self._get_elements(*self._rows_locator):
            rows.append(ComplexActionRowRegion(self.driver, self.conf, elem,
                                               self.row_action_names))
        return rows
