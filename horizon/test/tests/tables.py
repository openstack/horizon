# Copyright 2012 Nebula, Inc.
# Copyright 2014 IBM Corp.
#
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

from django.core.urlresolvers import reverse
from django import forms
from django import http
from django import shortcuts
from django.template import defaultfilters

from mox3.mox import IsA  # noqa
import six

from horizon import tables
from horizon.tables import formset as table_formset
from horizon.tables import views as table_views
from horizon.test import helpers as test


class FakeObject(object):
    def __init__(self, id, name, value, status, optional=None, excluded=None):
        self.id = id
        self.name = name
        self.value = value
        self.status = status
        self.optional = optional
        self.excluded = excluded
        self.extra = "extra"

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)


TEST_DATA = (
    FakeObject('1', 'object_1', 'value_1', 'up', 'optional_1', 'excluded_1'),
    FakeObject('2', 'object_2', '<strong>evil</strong>', 'down', 'optional_2'),
    FakeObject('3', 'object_3', 'value_3', 'up'),
)

TEST_DATA_2 = (
    FakeObject('1', 'object_1', 'value_1', 'down', 'optional_1', 'excluded_1'),
)

TEST_DATA_3 = (
    FakeObject('1', 'object_1', 'value_1', 'up', 'optional_1', 'excluded_1'),
)

TEST_DATA_4 = (
    FakeObject('1', 'object_1', 2, 'up'),
    FakeObject('2', 'object_2', 4, 'up'),
)

TEST_DATA_5 = (
    FakeObject('1', 'object_1', 'value_1',
               'A Status that is longer than 35 characters!', 'optional_1'),
)

TEST_DATA_6 = (
    FakeObject('1', 'object_1', 'DELETED', 'down'),
    FakeObject('2', 'object_2', 'CREATED', 'up'),
    FakeObject('3', 'object_3', 'STANDBY', 'standby'),
)

TEST_DATA_7 = (
    FakeObject('1', 'wrapped name', 'wrapped value', 'status',
               'not wrapped optional'),
)


class MyLinkAction(tables.LinkAction):
    name = "login"
    verbose_name = "Log In"
    url = "login"
    attrs = {
        "class": "ajax-modal",
    }

    def get_link_url(self, datum=None, *args, **kwargs):
        return reverse(self.url)


class MyAction(tables.Action):
    name = "delete"
    verbose_name = "Delete Me"
    verbose_name_plural = "Delete Them"

    def allowed(self, request, obj=None):
        return getattr(obj, 'status', None) != 'down'

    def handle(self, data_table, request, object_ids):
        return shortcuts.redirect('http://example.com/?ids=%s'
                                  % ",".join(object_ids))


class MyColumn(tables.Column):
    pass


class MyRowSelectable(tables.Row):
    ajax = True

    def can_be_selected(self, datum):
        return datum.value != 'DELETED'


class MyRow(tables.Row):
    ajax = True

    @classmethod
    def get_data(cls, request, obj_id):
        return TEST_DATA_2[0]


class MyBatchAction(tables.BatchAction):
    name = "batch"
    action_present = "Batch"
    action_past = "Batched"
    data_type_singular = "Item"
    data_type_plural = "Items"

    def action(self, request, object_ids):
        pass


class MyBatchActionWithHelpText(MyBatchAction):
    name = "batch_help"
    help_text = "this is help."
    action_present = "BatchHelp"
    action_past = "BatchedHelp"


class MyToggleAction(tables.BatchAction):
    name = "toggle"
    action_present = ("Down", "Up")
    action_past = ("Downed", "Upped")
    data_type_singular = "Item"
    data_type_plural = "Items"

    def allowed(self, request, obj=None):
        if not obj:
            return False
        self.down = getattr(obj, 'status', None) == 'down'
        if self.down:
            self.current_present_action = 1
        return self.down or getattr(obj, 'status', None) == 'up'

    def action(self, request, object_ids):
        if self.down:
            # up it
            self.current_past_action = 1


class MyDisabledAction(MyToggleAction):
    def allowed(self, request, obj=None):
        return False


class MyFilterAction(tables.FilterAction):
    def filter(self, table, objs, filter_string):
        q = filter_string.lower()

        def comp(obj):
            if q in obj.name.lower():
                return True
            return False

        return filter(comp, objs)


class MyServerFilterAction(tables.FilterAction):
    filter_type = 'server'
    filter_choices = (('name', 'Name', False),
                      ('status', 'Status', True))
    needs_preloading = True

    def filter(self, table, items, filter_string):
        filter_field = table.get_filter_field()
        if filter_field == 'name' and filter_string:
            return [item for item in items
                    if filter_string in item.name]
        return items


class MyUpdateAction(tables.UpdateAction):
    def allowed(self, *args):
        return True

    def update_cell(self, *args):
        pass


class MyUpdateActionNotAllowed(MyUpdateAction):
    def allowed(self, *args):
        return False


def get_name(obj):
    return "custom %s" % obj.name


def get_link(obj):
    return reverse('login')


class MyTable(tables.DataTable):
    tooltip_dict = {'up': {'title': 'service is up and running',
                           'style': 'color:green;cursor:pointer'},
                    'down': {'title': 'service is not available',
                             'style': 'color:red;cursor:pointer'}}
    id = tables.Column('id', hidden=True, sortable=False)
    name = tables.Column(get_name,
                         verbose_name="Verbose Name",
                         sortable=True,
                         form_field=forms.CharField(required=True),
                         form_field_attributes={'class': 'test'},
                         update_action=MyUpdateAction)
    value = tables.Column('value',
                          sortable=True,
                          link='http://example.com/',
                          attrs={'class': 'green blue'},
                          summation="average",
                          link_classes=('link-modal',),
                          link_attrs={'data-type': 'modal dialog',
                                      'data-tip': 'click for dialog'})
    status = tables.Column('status', link=get_link, truncate=35,
                           cell_attributes_getter=tooltip_dict.get)
    optional = tables.Column('optional', empty_value='N/A')
    excluded = tables.Column('excluded')

    class Meta(object):
        name = "my_table"
        verbose_name = "My Table"
        status_columns = ["status"]
        columns = ('id', 'name', 'value', 'optional', 'status')
        row_class = MyRow
        column_class = MyColumn
        table_actions = (MyFilterAction, MyAction, MyBatchAction,
                         MyBatchActionWithHelpText)
        row_actions = (MyAction, MyLinkAction, MyBatchAction, MyToggleAction,
                       MyBatchActionWithHelpText)


class MyServerFilterTable(MyTable):
    class Meta(object):
        name = "my_table"
        verbose_name = "My Table"
        status_columns = ["status"]
        columns = ('id', 'name', 'value', 'optional', 'status')
        row_class = MyRow
        column_class = MyColumn
        table_actions = (MyServerFilterAction, MyAction, MyBatchAction)
        row_actions = (MyAction, MyLinkAction, MyBatchAction, MyToggleAction,
                       MyBatchActionWithHelpText)


class MyTableSelectable(MyTable):
    class Meta(object):
        name = "my_table"
        columns = ('id', 'name', 'value', 'status')
        row_class = MyRowSelectable
        status_columns = ["status"]
        multi_select = True


class MyTableNotAllowedInlineEdit(MyTable):
    name = tables.Column(get_name,
                         verbose_name="Verbose Name",
                         sortable=True,
                         form_field=forms.CharField(required=True),
                         form_field_attributes={'class': 'test'},
                         update_action=MyUpdateActionNotAllowed)

    class Meta(object):
        name = "my_table"
        columns = ('id', 'name', 'value', 'optional', 'status')
        row_class = MyRow


class MyTableWrapList(MyTable):
    name = tables.Column('name',
                         form_field=forms.CharField(required=True),
                         form_field_attributes={'class': 'test'},
                         update_action=MyUpdateActionNotAllowed,
                         wrap_list=True)
    value = tables.Column('value',

                          wrap_list=True)
    optional = tables.Column('optional',
                             wrap_list=False)


class NoActionsTable(tables.DataTable):
    id = tables.Column('id')

    class Meta(object):
        name = "no_actions_table"
        verbose_name = "No Actions Table"
        table_actions = ()
        row_actions = ()


class DisabledActionsTable(tables.DataTable):
    id = tables.Column('id')

    class Meta(object):
        name = "disabled_actions_table"
        verbose_name = "Disabled Actions Table"
        table_actions = (MyDisabledAction,)
        row_actions = ()
        multi_select = True


class DataTableTests(test.TestCase):
    def test_table_instantiation(self):
        """Tests everything that happens when the table is instantiated."""
        self.table = MyTable(self.request, TEST_DATA)
        # Properties defined on the table
        self.assertEqual(TEST_DATA, self.table.data)
        self.assertEqual("my_table", self.table.name)
        # Verify calculated options that weren't specified explicitly
        self.assertTrue(self.table._meta.actions_column)
        self.assertTrue(self.table._meta.multi_select)
        # Test for verbose_name
        self.assertEqual(u"My Table", six.text_type(self.table))
        # Column ordering and exclusion.
        # This should include auto-columns for multi_select and actions,
        # but should not contain the excluded column.
        # Additionally, auto-generated columns should use the custom
        # column class specified on the table.
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<MyColumn: multi_select>',
                                  '<Column: id>',
                                  '<Column: name>',
                                  '<Column: value>',
                                  '<Column: optional>',
                                  '<Column: status>',
                                  '<MyColumn: actions>'])
        # Actions (these also test ordering)
        self.assertQuerysetEqual(self.table.base_actions.values(),
                                 ['<MyBatchAction: batch>',
                                  '<MyBatchActionWithHelpText: batch_help>',
                                  '<MyAction: delete>',
                                  '<MyFilterAction: filter>',
                                  '<MyLinkAction: login>',
                                  '<MyToggleAction: toggle>'])
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<MyFilterAction: filter>',
                                  '<MyAction: delete>',
                                  '<MyBatchAction: batch>',
                                  '<MyBatchActionWithHelpText: batch_help>'])
        self.assertQuerysetEqual(self.table.get_row_actions(TEST_DATA[0]),
                                 ['<MyAction: delete>',
                                  '<MyLinkAction: login>',
                                  '<MyBatchAction: batch>',
                                  '<MyToggleAction: toggle>',
                                  '<MyBatchActionWithHelpText: batch_help>'])
        # Auto-generated columns
        multi_select = self.table.columns['multi_select']
        self.assertEqual("multi_select", multi_select.auto)
        self.assertEqual("multi_select_column",
                         multi_select.get_final_attrs().get('class', ""))
        actions = self.table.columns['actions']
        self.assertEqual("actions", actions.auto)
        self.assertEqual("actions_column",
                         actions.get_final_attrs().get('class', ""))
        # In-line edit action on column.
        name_column = self.table.columns['name']
        self.assertEqual(MyUpdateAction, name_column.update_action)
        self.assertEqual(forms.CharField, name_column.form_field.__class__)
        self.assertEqual({'class': 'test'}, name_column.form_field_attributes)

    def test_table_force_no_multiselect(self):
        class TempTable(MyTable):
            class Meta(object):
                columns = ('id',)
                table_actions = (MyFilterAction, MyAction,)
                row_actions = (MyAction, MyLinkAction,)
                multi_select = False
        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: id>',
                                  '<Column: actions>'])

    def test_table_force_no_actions_column(self):
        class TempTable(MyTable):
            class Meta(object):
                columns = ('id',)
                table_actions = (MyFilterAction, MyAction,)
                row_actions = (MyAction, MyLinkAction,)
                actions_column = False
        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: multi_select>',
                                  '<Column: id>'])

    def test_table_natural_no_inline_editing(self):
        class TempTable(MyTable):
            name = tables.Column(get_name,
                                 verbose_name="Verbose Name",
                                 sortable=True)

            class Meta(object):
                name = "my_table"
                columns = ('id', 'name', 'value', 'optional', 'status')

        self.table = TempTable(self.request, TEST_DATA_2)
        name_column = self.table.columns['name']
        self.assertIsNone(name_column.update_action)
        self.assertIsNone(name_column.form_field)
        self.assertEqual({}, name_column.form_field_attributes)

    def test_table_natural_no_actions_column(self):
        class TempTable(MyTable):
            class Meta(object):
                columns = ('id',)
                table_actions = (MyFilterAction, MyAction,)
        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: multi_select>',
                                  '<Column: id>'])

    def test_table_natural_no_multiselect(self):
        class TempTable(MyTable):
            class Meta(object):
                columns = ('id',)
                row_actions = (MyAction, MyLinkAction,)
        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: id>',
                                  '<Column: actions>'])

    def test_table_column_inheritance(self):
        class TempTable(MyTable):
            extra = tables.Column('extra')

            class Meta(object):
                name = "temp_table"
                table_actions = (MyFilterAction, MyAction,)
                row_actions = (MyAction, MyLinkAction,)

        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: multi_select>',
                                  '<Column: id>',
                                  '<Column: name>',
                                  '<Column: value>',
                                  '<Column: status>',
                                  '<Column: optional>',
                                  '<Column: excluded>',
                                  '<Column: extra>',
                                  '<Column: actions>'])

    def test_table_construction(self):
        self.table = MyTable(self.request, TEST_DATA)
        # Verify we retrieve the right columns for headers
        columns = self.table.get_columns()
        self.assertQuerysetEqual(columns, ['<MyColumn: multi_select>',
                                           '<Column: id>',
                                           '<Column: name>',
                                           '<Column: value>',
                                           '<Column: optional>',
                                           '<Column: status>',
                                           '<MyColumn: actions>'])
        # Verify we retrieve the right rows from our data
        rows = self.table.get_rows()
        self.assertQuerysetEqual(rows, ['<MyRow: my_table__row__1>',
                                        '<MyRow: my_table__row__2>',
                                        '<MyRow: my_table__row__3>'])
        # Verify each row contains the right cells
        self.assertQuerysetEqual(rows[0].get_cells(),
                                 ['<Cell: multi_select, my_table__row__1>',
                                  '<Cell: id, my_table__row__1>',
                                  '<Cell: name, my_table__row__1>',
                                  '<Cell: value, my_table__row__1>',
                                  '<Cell: optional, my_table__row__1>',
                                  '<Cell: status, my_table__row__1>',
                                  '<Cell: actions, my_table__row__1>'])

    def test_table_column(self):
        self.table = MyTable(self.request, TEST_DATA)
        row = self.table.get_rows()[0]
        row3 = self.table.get_rows()[2]
        id_col = self.table.columns['id']
        name_col = self.table.columns['name']
        value_col = self.table.columns['value']
        # transform
        self.assertEqual('1', row.cells['id'].data)  # Standard attr access
        self.assertEqual('custom object_1', row.cells['name'].data)  # Callable
        # name and verbose_name
        self.assertEqual("Id", six.text_type(id_col))
        self.assertEqual("Verbose Name", six.text_type(name_col))
        # sortable
        self.assertEqual(False, id_col.sortable)
        self.assertNotIn("sortable", id_col.get_final_attrs().get('class', ""))
        self.assertEqual(True, name_col.sortable)
        self.assertIn("sortable", name_col.get_final_attrs().get('class', ""))
        # hidden
        self.assertEqual(True, id_col.hidden)
        self.assertIn("hide", id_col.get_final_attrs().get('class', ""))
        self.assertEqual(False, name_col.hidden)
        self.assertNotIn("hide", name_col.get_final_attrs().get('class', ""))
        # link, link_classes, link_attrs, and get_link_url
        self.assertIn('href="http://example.com/"', row.cells['value'].value)
        self.assertIn('class="link-modal"', row.cells['value'].value)
        self.assertIn('data-type="modal dialog"', row.cells['value'].value)
        self.assertIn('data-tip="click for dialog"', row.cells['value'].value)
        self.assertIn('href="/auth/login/"', row.cells['status'].value)
        # empty_value
        self.assertEqual("N/A", row3.cells['optional'].value)
        # classes
        self.assertEqual("green blue sortable anchor normal_column",
                         value_col.get_final_attrs().get('class', ""))
        # status
        cell_status = row.cells['status'].status
        self.assertEqual(True, cell_status)
        self.assertEqual('status_up',
                         row.cells['status'].get_status_class(cell_status))
        # status_choices
        id_col.status = True
        id_col.status_choices = (('1', False), ('2', True), ('3', None))
        cell_status = row.cells['id'].status
        self.assertEqual(False, cell_status)
        self.assertEqual('status_down',
                         row.cells['id'].get_status_class(cell_status))
        cell_status = row3.cells['id'].status
        self.assertIsNone(cell_status)
        self.assertEqual('status_unknown',
                         row.cells['id'].get_status_class(cell_status))

        # Ensure data is not cached on the column across table instances
        self.table = MyTable(self.request, TEST_DATA_2)
        row = self.table.get_rows()[0]
        self.assertTrue("down" in row.cells['status'].value)

    def test_table_row(self):
        self.table = MyTable(self.request, TEST_DATA)
        row = self.table.get_rows()[0]
        self.assertEqual(self.table, row.table)
        self.assertEqual(TEST_DATA[0], row.datum)
        self.assertEqual('my_table__row__1', row.id)
        # Verify row status works even if status isn't set on the column
        self.assertEqual(True, row.status)
        self.assertEqual('status_up', row.status_class)
        # Check the cells as well
        cell_status = row.cells['status'].status
        self.assertEqual(True, cell_status)
        self.assertEqual('status_up',
                         row.cells['status'].get_status_class(cell_status))

    def test_table_column_truncation(self):
        self.table = MyTable(self.request, TEST_DATA_5)
        row = self.table.get_rows()[0]

        self.assertEqual(35, len(row.cells['status'].data))
        self.assertEqual(u'A Status that is longer than 35 ...',
                         row.cells['status'].data)

    def test_table_rendering(self):
        self.table = MyTable(self.request, TEST_DATA)
        # Table actions
        table_actions = self.table.render_table_actions()
        resp = http.HttpResponse(table_actions)
        self.assertContains(resp, "table_search", 1)
        self.assertContains(resp, "my_table__filter__q", 1)
        self.assertContains(resp, "my_table__delete", 1)
        self.assertContains(resp, 'id="my_table__action_delete"', 1)

        # Table BatchActions
        self.assertContains(resp, 'id="my_table__action_batch_help"', 1)
        self.assertContains(resp, 'help_text="this is help."', 1)
        self.assertContains(resp, 'BatchHelp Item', 1)

        # Row actions
        row_actions = self.table.render_row_actions(TEST_DATA[0])
        resp = http.HttpResponse(row_actions)
        self.assertContains(resp, "<li", 4)
        self.assertContains(resp, "my_table__delete__1", 1)
        self.assertContains(resp, "my_table__toggle__1", 1)
        self.assertContains(resp, "/auth/login/", 1)
        self.assertContains(resp, "ajax-modal", 1)
        self.assertContains(resp, 'id="my_table__row_1__action_delete"', 1)

        # Row BatchActions
        row_actions = self.table.render_row_actions(TEST_DATA[0])
        resp = http.HttpResponse(row_actions)
        self.assertContains(resp, 'id="my_table__row_1__action_batch_help"', 1)
        self.assertContains(resp, 'help_text="this is help."', 1)
        self.assertContains(resp, 'value="my_table__batch_help__1"', 1)
        self.assertContains(resp, 'BatchHelp Item', 1)

        # Whole table
        resp = http.HttpResponse(self.table.render())
        self.assertContains(resp, '<table id="my_table"', 1)
        self.assertContains(resp, '<th ', 8)
        self.assertContains(resp, 'id="my_table__row__1"', 1)
        self.assertContains(resp, 'id="my_table__row__2"', 1)
        self.assertContains(resp, 'id="my_table__row__3"', 1)
        update_string = "action=row_update&amp;table=my_table&amp;obj_id="
        self.assertContains(resp, update_string, 3)
        self.assertContains(resp, "data-update-interval", 3)
        # Verify no table heading
        self.assertNotContains(resp, "<h3 class='table_title'")
        # Verify our XSS protection
        self.assertContains(resp, '<a href="http://example.com/" '
                                  'data-tip="click for dialog" '
                                  'data-type="modal dialog" '
                                  'class="link-modal">'
                                  '&lt;strong&gt;evil&lt;/strong&gt;</a>', 1)
        # Hidden Title = False shows the table title
        self.table._meta.hidden_title = False
        resp = http.HttpResponse(self.table.render())
        self.assertContains(resp, "<h3 class='table_title'", 1)

        # Filter = False hides the search box
        self.table._meta.filter = False
        table_actions = self.table.render_table_actions()
        resp = http.HttpResponse(table_actions)
        self.assertContains(resp, "table_search", 0)

    def test_wrap_list_rendering(self):
        self.table = MyTableWrapList(self.request, TEST_DATA_7)
        row = self.table.get_rows()[0]
        name_cell = row.cells['name']
        value_cell = row.cells['value']
        optional_cell = row.cells['optional']

        # Check if is cell is rendered correctly.
        name_cell_rendered = name_cell.render()
        value_cell_rendered = value_cell.render()
        optional_cell_rendered = optional_cell.render()
        resp_name = http.HttpResponse(name_cell_rendered)
        resp_value = http.HttpResponse(value_cell_rendered)
        resp_optional = http.HttpResponse(optional_cell_rendered)
        self.assertContains(resp_name, '<ul>wrapped name</ul>', 1)
        self.assertContains(resp_value, '<ul>wrapped value</ul>', 1)
        self.assertContains(resp_optional, 'not wrapped optional', 1)
        self.assertNotContains(resp_optional, '<ul>')
        self.assertNotContains(resp_optional, '</ul>')

    def test_inline_edit_available_cell_rendering(self):
        self.table = MyTable(self.request, TEST_DATA_2)
        row = self.table.get_rows()[0]
        name_cell = row.cells['name']

        # Check if in-line edit is available in the cell,
        # but is not in inline_edit_mod.
        self.assertEqual(True,
                         name_cell.inline_edit_available)
        self.assertEqual(False,
                         name_cell.inline_edit_mod)

        # Check if is cell is rendered correctly.
        name_cell_rendered = name_cell.render()
        resp = http.HttpResponse(name_cell_rendered)

        self.assertContains(resp, '<td', 1)
        self.assertContains(resp, 'inline_edit_available', 1)
        self.assertContains(resp,
                            'data-update-url="?action=cell_update&amp;'
                            'table=my_table&amp;cell_name=name&amp;obj_id=1"',
                            1)
        self.assertContains(resp, 'table_cell_wrapper', 1)
        self.assertContains(resp, 'table_cell_data_wrapper', 1)
        self.assertContains(resp, 'table_cell_action', 1)
        self.assertContains(resp, 'ajax-inline-edit', 1)

    def test_inline_edit_available_not_allowed_cell_rendering(self):
        self.table = MyTableNotAllowedInlineEdit(self.request, TEST_DATA_2)

        row = self.table.get_rows()[0]
        name_cell = row.cells['name']

        # Check if in-line edit is available in the cell,
        # but is not in inline_edit_mod.
        self.assertEqual(True,
                         name_cell.inline_edit_available)
        self.assertEqual(False,
                         name_cell.inline_edit_mod)

        # Check if is cell is rendered correctly.
        name_cell_rendered = name_cell.render()
        resp = http.HttpResponse(name_cell_rendered)

        self.assertContains(resp, '<td', 1)
        self.assertContains(resp, 'inline_edit_available', 1)
        self.assertContains(resp,
                            'data-update-url="?action=cell_update&amp;'
                            'table=my_table&amp;cell_name=name&amp;obj_id=1"',
                            1)
        self.assertContains(resp, 'table_cell_wrapper', 0)
        self.assertContains(resp, 'table_cell_data_wrapper', 0)
        self.assertContains(resp, 'table_cell_action', 0)
        self.assertContains(resp, 'ajax-inline-edit', 0)

    def test_inline_edit_mod_cell_rendering(self):
        self.table = MyTable(self.request, TEST_DATA_2)
        name_col = self.table.columns['name']
        name_col.auto = "form_field"

        row = self.table.get_rows()[0]
        name_cell = row.cells['name']
        name_cell.inline_edit_mod = True

        # Check if in-line edit is available in the cell,
        # and is in inline_edit_mod, also column auto must be
        # set as form_field.
        self.assertEqual(True,
                         name_cell.inline_edit_available)
        self.assertEqual(True,
                         name_cell.inline_edit_mod)
        self.assertEqual('form_field',
                         name_col.auto)

        # Check if is cell is rendered correctly.
        name_cell_rendered = name_cell.render()
        resp = http.HttpResponse(name_cell_rendered)

        self.assertContains(resp,
                            '<input class="test" id="name__1" name="name__1"'
                            ' type="text" value="custom object_1" />',
                            count=1, html=True)

        self.assertContains(resp, '<td', 1)
        self.assertContains(resp, 'inline_edit_available', 1)
        self.assertContains(resp,
                            'data-update-url="?action=cell_update&amp;'
                            'table=my_table&amp;cell_name=name&amp;obj_id=1"',
                            1)
        self.assertContains(resp, 'table_cell_wrapper', 1)
        self.assertContains(resp, 'inline-edit-error', 1)
        self.assertContains(resp, 'inline-edit-form', 1)
        self.assertContains(resp, 'inline-edit-actions', 1)
        self.assertContains(resp, 'inline-edit-submit', 1)
        self.assertContains(resp, 'inline-edit-cancel', 1)

    def test_inline_edit_mod_checkbox_with_label(self):
        class TempTable(MyTable):
            name = tables.Column(get_name,
                                 verbose_name="Verbose Name",
                                 sortable=True,
                                 form_field=forms.BooleanField(
                                     required=True,
                                     label="Verbose Name"),
                                 form_field_attributes={'class': 'test'},
                                 update_action=MyUpdateAction)

            class Meta(object):
                name = "my_table"
                columns = ('id', 'name', 'value', 'optional', 'status')

        self.table = TempTable(self.request, TEST_DATA_2)
        name_col = self.table.columns['name']
        name_col.auto = "form_field"

        row = self.table.get_rows()[0]
        name_cell = row.cells['name']
        name_cell.inline_edit_mod = True

        # Check if is cell is rendered correctly.
        name_cell_rendered = name_cell.render()
        resp = http.HttpResponse(name_cell_rendered)

        self.assertContains(resp,
                            '<input checked="checked" class="test" '
                            'id="name__1" name="name__1" type="checkbox" '
                            'value="custom object_1" />',
                            count=1, html=True)
        self.assertContains(resp,
                            '<label class="inline-edit-label" for="name__1">'
                            'Verbose Name</label>',
                            count=1, html=True)

    def test_table_search_action(self):
        class TempTable(MyTable):
            class Meta(object):
                name = "my_table"
                table_actions = (tables.NameFilterAction,)

        # with the filter string 2, it should return 2nd item
        action_string = "my_table__filter__q"
        req = self.factory.post('/my_url/', {action_string: '2'})
        self.table = TempTable(req, TEST_DATA)
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<NameFilterAction: filter>'])
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_2>'])

        # with empty filter string, it should return all data
        req = self.factory.post('/my_url/', {action_string: ''})
        self.table = TempTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_1>',
                                  '<FakeObject: object_2>',
                                  '<FakeObject: object_3>'])

        # with unknown value it should return empty list
        req = self.factory.post('/my_url/', {action_string: 'horizon'})
        self.table = TempTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data, [])

    def test_inline_edit_mod_textarea(self):
        class TempTable(MyTable):
            name = tables.Column(get_name,
                                 verbose_name="Verbose Name",
                                 sortable=True,
                                 form_field=forms.CharField(
                                     widget=forms.Textarea(),
                                     required=False),
                                 form_field_attributes={'class': 'test'},
                                 update_action=MyUpdateAction)

            class Meta(object):
                name = "my_table"
                columns = ('id', 'name', 'value', 'optional', 'status')

        self.table = TempTable(self.request, TEST_DATA_2)
        name_col = self.table.columns['name']
        name_col.auto = "form_field"

        row = self.table.get_rows()[0]
        name_cell = row.cells['name']
        name_cell.inline_edit_mod = True

        # Check if is cell is rendered correctly.
        name_cell_rendered = name_cell.render()
        resp = http.HttpResponse(name_cell_rendered)

        self.assertContains(resp,
                            '<textarea class="test" cols="40" id="name__1" '
                            'name="name__1" rows="10">\r\ncustom object_1'
                            '</textarea>',
                            count=1, html=True)

    def test_table_actions(self):
        # Single object action
        action_string = "my_table__delete__1"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'delete', '1'),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertEqual(302, handled.status_code)
        self.assertEqual("http://example.com/?ids=1", handled["location"])

        # Batch action (without toggle) conjugation behavior
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_3)
        toggle_action = self.table.get_row_actions(TEST_DATA_3[0])[2]
        self.assertEqual("Batch Item",
                         six.text_type(toggle_action.verbose_name))

        # Batch action with custom help text
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_3)
        toggle_action = self.table.get_row_actions(TEST_DATA_3[0])[4]
        self.assertEqual("BatchHelp Item",
                         six.text_type(toggle_action.verbose_name))

        # Single object toggle action
        # GET page - 'up' to 'down'
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_3)
        self.assertEqual(5, len(self.table.get_row_actions(TEST_DATA_3[0])))
        toggle_action = self.table.get_row_actions(TEST_DATA_3[0])[3]
        self.assertEqual("Down Item",
                         six.text_type(toggle_action.verbose_name))

        # Toggle from status 'up' to 'down'
        # POST page
        action_string = "my_table__toggle__1"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'toggle', '1'),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertEqual(302, handled.status_code)
        self.assertEqual("/my_url/", handled["location"])
        self.assertEqual(u"Downed Item: object_1",
                         list(req._messages)[0].message)

        # Toggle from status 'down' to 'up'
        # GET page - 'down' to 'up'
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_2)
        self.assertEqual(4, len(self.table.get_row_actions(TEST_DATA_2[0])))
        toggle_action = self.table.get_row_actions(TEST_DATA_2[0])[2]
        self.assertEqual("Up Item", six.text_type(toggle_action.verbose_name))

        # POST page
        action_string = "my_table__toggle__2"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'toggle', '2'),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertEqual(302, handled.status_code)
        self.assertEqual("/my_url/", handled["location"])
        self.assertEqual(u"Upped Item: object_2",
                         list(req._messages)[0].message)

        # there are underscore in object-id.
        # (because swift support custom object id)
        action_string = "my_table__toggle__2__33__$$"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'toggle', '2__33__$$'),
                         self.table.parse_action(action_string))

        # Multiple object action
        action_string = "my_table__delete"
        req = self.factory.post('/my_url/', {'action': action_string,
                                             'object_ids': [1, 2]})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'delete', None),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertEqual(302, handled.status_code)
        self.assertEqual("http://example.com/?ids=1,2", handled["location"])

        # Action with nothing selected
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'delete', None),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertEqual("Please select a row before taking that action.",
                         list(req._messages)[0].message)

        # Action with specific id and multiple ids favors single id
        action_string = "my_table__delete__3"
        req = self.factory.post('/my_url/', {'action': action_string,
                                             'object_ids': [1, 2]})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(('my_table', 'delete', '3'),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertEqual(302, handled.status_code)
        self.assertEqual("http://example.com/?ids=3",
                         handled["location"])

        # At least one object in table
        # BatchAction is available
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_2)
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<MyFilterAction: filter>',
                                  '<MyAction: delete>',
                                  '<MyBatchAction: batch>',
                                  '<MyBatchActionWithHelpText: batch_help>'])

        # Zero objects in table
        # BatchAction not available
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, None)
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<MyFilterAction: filter>',
                                  '<MyAction: delete>'])

        # Filtering
        action_string = "my_table__filter__q"
        req = self.factory.post('/my_url/', {action_string: '2'})
        self.table = MyTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_2>'])

        # Ensure fitering respects the request method, e.g. no filter here
        req = self.factory.get('/my_url/', {action_string: '2'})
        self.table = MyTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_1>',
                                  '<FakeObject: object_2>',
                                  '<FakeObject: object_3>'])

        # Updating and preemptive actions
        params = {"table": "my_table", "action": "row_update", "obj_id": "1"}
        req = self.factory.get('/my_url/',
                               params,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.table = MyTable(req)
        resp = self.table.maybe_preempt()
        self.assertEqual(200, resp.status_code)
        # Make sure the data returned differs from the original
        self.assertContains(resp, "my_table__row__1")
        self.assertContains(resp, "status_down")

        # Verify that we don't get a response for a valid action with the
        # wrong method.
        params = {"table": "my_table", "action": "delete", "obj_id": "1"}
        req = self.factory.get('/my_url/', params)
        self.table = MyTable(req)
        resp = self.table.maybe_preempt()
        self.assertIsNone(resp)
        resp = self.table.maybe_handle()
        self.assertIsNone(resp)

        # Verbose names
        table_actions = self.table.get_table_actions()
        self.assertEqual("Filter",
                         six.text_type(table_actions[0].verbose_name))
        self.assertEqual("Delete Me",
                         six.text_type(table_actions[1].verbose_name))

        row_actions = self.table.get_row_actions(TEST_DATA[0])
        self.assertEqual("Delete Me",
                         six.text_type(row_actions[0].verbose_name))
        self.assertEqual("Log In",
                         six.text_type(row_actions[1].verbose_name))

    def test_server_filtering(self):
        filter_value_param = "my_table__filter__q"
        filter_field_param = '%s_field' % filter_value_param

        # Server Filtering
        req = self.factory.post('/my_url/')
        req.session[filter_value_param] = '2'
        req.session[filter_field_param] = 'name'
        self.table = MyServerFilterTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_2>'])

        # Ensure API filtering does not filter on server, e.g. no filter here
        req = self.factory.post('/my_url/')
        req.session[filter_value_param] = 'up'
        req.session[filter_field_param] = 'status'
        self.table = MyServerFilterTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_1>',
                                  '<FakeObject: object_2>',
                                  '<FakeObject: object_3>'])

    def test_inline_edit_update_action_get_non_ajax(self):
        # Non ajax inline edit request should return None.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.get(url, {})
        self.table = MyTable(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertIsNone(handled)

    def test_inline_edit_update_action_get(self):
        # Get request should return td field with data.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.get(url, {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.table = MyTable(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertEqual(200, handled.status_code)
        # Checking the response content.
        resp = handled
        self.assertContains(resp, '<td', 1)
        self.assertContains(resp, 'inline_edit_available', 1)
        self.assertContains(
            resp,
            'data-update-url="/my_url/?action=cell_update&amp;'
            'table=my_table&amp;cell_name=name&amp;obj_id=1"',
            1)
        self.assertContains(resp, 'table_cell_wrapper', 1)
        self.assertContains(resp, 'table_cell_data_wrapper', 1)
        self.assertContains(resp, 'table_cell_action', 1)
        self.assertContains(resp, 'ajax-inline-edit', 1)

    def test_inline_edit_update_action_get_not_allowed(self):
        # Name column has required validation, sending blank
        # will return error.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.post(url, {})
        self.table = MyTableNotAllowedInlineEdit(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertEqual(401, handled.status_code)

    def test_inline_edit_update_action_get_inline_edit_mod(self):
        # Get request in inline_edit_mode should return td with form field.
        url = ('/my_url/?inline_edit_mod=true&action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.get(url, {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.table = MyTable(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertEqual(200, handled.status_code)
        # Checking the response content.
        resp = handled
        self.assertContains(resp,
                            '<input class="test" id="name__1" name="name__1"'
                            ' type="text" value="custom object_1" />',
                            count=1, html=True)

        self.assertContains(resp, '<td', 1)
        self.assertContains(resp, 'inline_edit_available', 1)
        self.assertContains(
            resp,
            'data-update-url="/my_url/?action=cell_update&amp;'
            'table=my_table&amp;cell_name=name&amp;obj_id=1"',
            1)
        self.assertContains(resp, 'table_cell_wrapper', 1)
        self.assertContains(resp, 'inline-edit-error', 1)
        self.assertContains(resp, 'inline-edit-form', 1)
        self.assertContains(resp, 'inline-edit-actions', 1)
        self.assertContains(resp, '<button', 2)
        self.assertContains(resp, 'inline-edit-submit', 1)
        self.assertContains(resp, 'inline-edit-cancel', 1)

    def test_inline_edit_update_action_post(self):
        # Post request should invoke the cell update table action.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.post(url, {'name__1': 'test_name'})
        self.table = MyTable(req, TEST_DATA_2)
        # checking the response header
        handled = self.table.maybe_preempt()
        self.assertEqual(200, handled.status_code)

    def test_inline_edit_update_action_post_not_allowed(self):
        # Post request should invoke the cell update table action.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.post(url, {'name__1': 'test_name'})
        self.table = MyTableNotAllowedInlineEdit(req, TEST_DATA_2)
        # checking the response header
        handled = self.table.maybe_preempt()
        self.assertEqual(401, handled.status_code)

    def test_inline_edit_update_action_post_validation_error(self):
        # Name column has required validation, sending blank
        # will return error.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.post(url, {})
        self.table = MyTable(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertEqual(400, handled.status_code)
        self.assertEqual(('Content-Type', 'application/json'),
                         handled._headers['content-type'])
        # Checking the response content.
        resp = handled
        self.assertContains(resp,
                            '"message": "This field is required."',
                            count=1, status_code=400)

    def test_column_uniqueness(self):
        table1 = MyTable(self.request)
        table2 = MyTable(self.request)
        # Regression test for launchpad bug 964345.
        self.assertNotEqual(id(table1), id(table2))
        self.assertNotEqual(id(table1.columns), id(table2.columns))
        t1cols = table1.columns.values()
        t2cols = table2.columns.values()
        self.assertEqual(t1cols[0].name, t2cols[0].name)
        self.assertNotEqual(id(t1cols[0]), id(t2cols[0]))
        self.assertNotEqual(id(t1cols[0].table),
                            id(t2cols[0].table))
        self.assertNotEqual(id(t1cols[0].table._data_cache),
                            id(t2cols[0].table._data_cache))

    def test_summation_row(self):
        # Test with the "average" method.
        table = MyTable(self.request, TEST_DATA_4)
        res = http.HttpResponse(table.render())
        self.assertContains(res, '<tr class="summation"', 1)
        self.assertContains(res, '<td>Summary</td>', 1)
        self.assertContains(res, '<td>3.0</td>', 1)

        # Test again with the "sum" method.
        table.columns['value'].summation = "sum"
        res = http.HttpResponse(table.render())
        self.assertContains(res, '<tr class="summation"', 1)
        self.assertContains(res, '<td>Summary</td>', 1)
        self.assertContains(res, '<td>6</td>', 1)

        # One last test with no summation.
        table.columns['value'].summation = None
        table.needs_summary_row = False
        res = http.HttpResponse(table.render())
        self.assertNotContains(res, '<tr class="summation"')
        self.assertNotContains(res, '<td>3.0</td>')
        self.assertNotContains(res, '<td>6</td>')

        # Even if "average" summation method is specified,
        # we have summation fields but no value is provided
        # if the provided data cannot be summed.
        table = MyTable(self.request, TEST_DATA)
        res = http.HttpResponse(table.render())
        self.assertContains(res, '<tr class="summation"')
        self.assertNotContains(res, '<td>3.0</td>')
        self.assertNotContains(res, '<td>6</td>')

    def test_table_action_attributes(self):
        table = MyTable(self.request, TEST_DATA)
        self.assertTrue(table.has_actions)
        self.assertTrue(table.needs_form_wrapper)
        res = http.HttpResponse(table.render())
        self.assertContains(res, "<form")

        table = MyTable(self.request, TEST_DATA, needs_form_wrapper=False)
        self.assertTrue(table.has_actions)
        self.assertFalse(table.needs_form_wrapper)
        res = http.HttpResponse(table.render())
        self.assertNotContains(res, "<form")

        table = NoActionsTable(self.request, TEST_DATA)
        self.assertFalse(table.has_actions)
        self.assertFalse(table.needs_form_wrapper)
        res = http.HttpResponse(table.render())
        self.assertNotContains(res, "<form")

    def test_table_actions_not_allowed_hide_multiselect(self):
        table = DisabledActionsTable(self.request, TEST_DATA)
        self.assertFalse(table.has_actions)
        self.assertFalse(table.needs_form_wrapper)
        res = http.HttpResponse(table.render())
        self.assertContains(res, "multi_select_column hidden")

    def test_table_action_object_display_is_id(self):
        action_string = "my_table__toggle__1"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)

        self.mox.StubOutWithMock(self.table, 'get_object_display')
        self.table.get_object_display(IsA(FakeObject)).AndReturn(None)
        self.mox.ReplayAll()

        self.assertEqual(('my_table', 'toggle', '1'),
                         self.table.parse_action(action_string))
        handled = self.table.maybe_handle()
        self.assertEqual(302, handled.status_code)
        self.assertEqual("/my_url/", handled["location"])
        self.assertEqual(u"Downed Item: 1",
                         list(req._messages)[0].message)

    def test_table_column_can_be_selected(self):
        self.table = MyTableSelectable(self.request, TEST_DATA_6)
        # non selectable row
        row = self.table.get_rows()[0]
        # selectable
        row1 = self.table.get_rows()[1]
        row2 = self.table.get_rows()[2]

        id_col = self.table.columns['id']
        name_col = self.table.columns['name']
        value_col = self.table.columns['value']
        # transform
        self.assertEqual('1', row.cells['id'].data)  # Standard attr access
        self.assertEqual('custom object_1', row.cells['name'].data)  # Callable
        # name and verbose_name
        self.assertEqual("Id", six.text_type(id_col))
        self.assertEqual("Verbose Name", six.text_type(name_col))
        self.assertIn("sortable", name_col.get_final_attrs().get('class', ""))
        # hidden
        self.assertEqual(True, id_col.hidden)
        self.assertIn("hide", id_col.get_final_attrs().get('class', ""))
        self.assertEqual(False, name_col.hidden)
        self.assertNotIn("hide", name_col.get_final_attrs().get('class', ""))
        # link, link_classes, link_attrs and get_link_url
        self.assertIn('href="http://example.com/"', row.cells['value'].value)
        self.assertIn('class="link-modal"', row.cells['value'].value)
        self.assertIn('data-type="modal dialog"', row.cells['value'].value)
        self.assertIn('data-tip="click for dialog"', row.cells['value'].value)
        self.assertIn('href="/auth/login/"', row.cells['status'].value)
        # classes
        self.assertEqual("green blue sortable anchor normal_column",
                         value_col.get_final_attrs().get('class', ""))

        self.assertQuerysetEqual(row.get_cells(),
                                 ['<Cell: multi_select, my_table__row__1>',
                                  '<Cell: id, my_table__row__1>',
                                  '<Cell: name, my_table__row__1>',
                                  '<Cell: value, my_table__row__1>',
                                  '<Cell: status, my_table__row__1>',
                                  ])
        # can_be_selected = False
        self.assertTrue(row.get_cells()[0].data == "")
        # can_be_selected = True
        self.assertIn('checkbox', row1.get_cells()[0].data)
        # status
        cell_status = row.cells['status'].status
        self.assertEqual('status_down',
                         row.cells['status'].get_status_class(cell_status))

        self.assertEqual(row.cells['status'].data, 'down')
        self.assertEqual(row.cells['status'].attrs,
                         {'title': 'service is not available',
                          'style': 'color:red;cursor:pointer'})
        self.assertEqual(row1.cells['status'].data, 'up')
        self.assertEqual(row1.cells['status'].attrs,
                         {'title': 'service is up and running',
                          'style': 'color:green;cursor:pointer'})
        self.assertEqual(row2.cells['status'].data, 'standby')
        self.assertEqual(row2.cells['status'].attrs, {})

        status_rendered = row.cells['status'].render()
        resp = http.HttpResponse(status_rendered)
        self.assertContains(resp, 'style="color:red;cursor:pointer"', 1)
        self.assertContains(resp, 'title="service is not available"', 1)

        status_rendered = row1.cells['status'].render()
        resp = http.HttpResponse(status_rendered)
        self.assertContains(resp, 'style="color:green;cursor:pointer"', 1)
        self.assertContains(resp, 'title="service is up and running"', 1)

        # status_choices
        id_col.status = True
        id_col.status_choices = (('1', False), ('2', True))
        cell_status = row.cells['id'].status
        self.assertEqual(False, cell_status)
        self.assertEqual('status_down',
                         row.cells['id'].get_status_class(cell_status))
        # Ensure data is not cached on the column across table instances
        self.table = MyTable(self.request, TEST_DATA_6)
        row = self.table.get_rows()[0]
        self.assertTrue("down" in row.cells['status'].value)

    def test_broken_filter(self):
        class MyTableBrokenFilter(MyTable):
            value = tables.Column('value',
                                  filters=(defaultfilters.timesince,))

        value = "not_a_date"
        data = TEST_DATA[0]
        data.value = value

        table = MyTableBrokenFilter(self.request, [data])
        resp = http.HttpResponse(table.render())
        self.assertContains(resp, value)


class SingleTableView(table_views.DataTableView):
    table_class = MyTable
    name = "Single Table"
    slug = "single"
    template_name = "horizon/common/_detail_table.html"

    def get_data(self):
        return TEST_DATA


class APIFilterTableView(SingleTableView):
    table_class = MyServerFilterTable


class TableWithPermissions(tables.DataTable):
    id = tables.Column('id')

    class Meta(object):
        name = "table_with_permissions"
        permissions = ('horizon.test',)


class SingleTableViewWithPermissions(SingleTableView):
    table_class = TableWithPermissions


class MultiTableView(tables.MultiTableView):
    table_classes = (TableWithPermissions, MyTable)

    def get_table_with_permissions_data(self):
        return TEST_DATA

    def get_my_table_data(self):
        return TEST_DATA


class DataTableViewTests(test.TestCase):
    def _prepare_view(self, cls, *args, **kwargs):
        req = self.factory.get('/my_url/')
        req.user = self.user
        view = cls()
        view.request = req
        view.args = args
        view.kwargs = kwargs
        return view

    def test_data_table_view(self):
        view = self._prepare_view(SingleTableView)
        context = view.get_context_data()
        self.assertEqual(SingleTableView.table_class,
                         context['table'].__class__)

    def test_data_table_view_not_authorized(self):
        view = self._prepare_view(SingleTableViewWithPermissions)
        context = view.get_context_data()
        self.assertNotIn('table', context)

    def test_data_table_view_authorized(self):
        view = self._prepare_view(SingleTableViewWithPermissions)
        self.set_permissions(permissions=['test'])
        context = view.get_context_data()
        self.assertIn('table', context)
        self.assertEqual(SingleTableViewWithPermissions.table_class,
                         context['table'].__class__)

    def test_multi_table_view_not_authorized(self):
        view = self._prepare_view(MultiTableView)
        context = view.get_context_data()
        self.assertEqual(MyTable, context['my_table_table'].__class__)
        self.assertNotIn('table_with_permissions_table', context)

    def test_multi_table_view_authorized(self):
        view = self._prepare_view(MultiTableView)
        self.set_permissions(permissions=['test'])
        context = view.get_context_data()
        self.assertEqual(MyTable, context['my_table_table'].__class__)
        self.assertEqual(TableWithPermissions,
                         context['table_with_permissions_table'].__class__)

    fil_value_param = "my_table__filter__q"
    fil_field_param = '%s_field' % fil_value_param

    def _test_filter_setup_view(self, request):
        view = APIFilterTableView()
        view.request = request
        view.kwargs = {}
        view.handle_server_filter(request)
        return view

    def test_api_filter_table_view(self):
        req = self.factory.post('/my_url/', {self.fil_value_param: 'up',
                                             self.fil_field_param: 'status'})
        req.user = self.user
        view = self._test_filter_setup_view(req)
        data = view.get_data()
        context = view.get_context_data()
        self.assertEqual(context['table'].__class__, MyServerFilterTable)
        self.assertQuerysetEqual(data,
                                 ['<FakeObject: object_1>',
                                  '<FakeObject: object_2>',
                                  '<FakeObject: object_3>'])
        self.assertEqual(req.session.get(self.fil_value_param), 'up')
        self.assertEqual(req.session.get(self.fil_field_param), 'status')

    def test_filter_changed_deleted(self):
        req = self.factory.post('/my_url/', {self.fil_value_param: '',
                                             self.fil_field_param: 'status'})
        req.session[self.fil_value_param] = 'up'
        req.session[self.fil_field_param] = 'status'
        req.user = self.user
        view = self._test_filter_setup_view(req)
        context = view.get_context_data()
        self.assertEqual(context['table'].__class__, MyServerFilterTable)
        self.assertEqual(req.session.get(self.fil_value_param), '')
        self.assertEqual(req.session.get(self.fil_field_param), 'status')

    def test_filter_changed_nothing_sent(self):
        req = self.factory.post('/my_url/', {})
        req.session[self.fil_value_param] = 'up'
        req.session[self.fil_field_param] = 'status'
        req.user = self.user
        view = self._test_filter_setup_view(req)
        context = view.get_context_data()
        self.assertEqual(context['table'].__class__, MyServerFilterTable)
        self.assertEqual(req.session.get(self.fil_value_param), 'up')
        self.assertEqual(req.session.get(self.fil_field_param), 'status')

    def test_filter_changed_new_filter_sent(self):
        req = self.factory.post('/my_url/', {self.fil_value_param: 'down',
                                             self.fil_field_param: 'status'})
        req.session[self.fil_value_param] = 'up'
        req.session[self.fil_field_param] = 'status'
        req.user = self.user
        view = self._test_filter_setup_view(req)
        context = view.get_context_data()
        self.assertEqual(context['table'].__class__, MyServerFilterTable)
        self.assertEqual(req.session.get(self.fil_value_param), 'down')
        self.assertEqual(req.session.get(self.fil_field_param), 'status')


class FormsetTableTests(test.TestCase):

    def test_populate(self):
        """Create a FormsetDataTable and populate it with data."""

        class TableForm(forms.Form):
            name = forms.CharField()
            value = forms.IntegerField()

        TableFormset = forms.formsets.formset_factory(TableForm, extra=0)

        class Table(table_formset.FormsetDataTable):
            formset_class = TableFormset

            name = tables.Column('name')
            value = tables.Column('value')

            class Meta(object):
                name = 'table'

        table = Table(self.request)
        table.data = TEST_DATA_4
        formset = table.get_formset()
        self.assertEqual(2, len(formset))
        form = formset[0]
        form_data = form.initial
        self.assertEqual('object_1', form_data['name'])
        self.assertEqual(2, form_data['value'])
