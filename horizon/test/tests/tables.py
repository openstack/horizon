# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from mox import IsA  # noqa

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
    FakeObject('1', 'object_1', 'A Value That is longer than 35 characters!',
               'down', 'optional_1'),
)

TEST_DATA_6 = (
    FakeObject('1', 'object_1', 'DELETED', 'down'),
    FakeObject('2', 'object_2', 'CREATED', 'up'),
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
            #up it
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
                          truncate=35,
                          link_classes=('link-modal',))
    status = tables.Column('status', link=get_link)
    optional = tables.Column('optional', empty_value='N/A')
    excluded = tables.Column('excluded')

    class Meta:
        name = "my_table"
        verbose_name = "My Table"
        status_columns = ["status"]
        columns = ('id', 'name', 'value', 'optional', 'status')
        row_class = MyRow
        column_class = MyColumn
        table_actions = (MyFilterAction, MyAction, MyBatchAction)
        row_actions = (MyAction, MyLinkAction, MyBatchAction, MyToggleAction)


class MyTableSelectable(MyTable):
    class Meta:
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

    class Meta:
        name = "my_table"
        columns = ('id', 'name', 'value', 'optional', 'status')
        row_class = MyRow


class NoActionsTable(tables.DataTable):
    id = tables.Column('id')

    class Meta:
        name = "no_actions_table"
        verbose_name = "No Actions Table"
        table_actions = ()
        row_actions = ()


class DisabledActionsTable(tables.DataTable):
    id = tables.Column('id')

    class Meta:
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
        self.assertEqual(self.table.data, TEST_DATA)
        self.assertEqual(self.table.name, "my_table")
        # Verify calculated options that weren't specified explicitly
        self.assertTrue(self.table._meta.actions_column)
        self.assertTrue(self.table._meta.multi_select)
        # Test for verbose_name
        self.assertEqual(unicode(self.table), u"My Table")
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
                                  '<MyAction: delete>',
                                  '<MyFilterAction: filter>',
                                  '<MyLinkAction: login>',
                                  '<MyToggleAction: toggle>'])
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<MyFilterAction: filter>',
                                  '<MyAction: delete>',
                                  '<MyBatchAction: batch>'])
        self.assertQuerysetEqual(self.table.get_row_actions(TEST_DATA[0]),
                                 ['<MyAction: delete>',
                                  '<MyLinkAction: login>',
                                  '<MyBatchAction: batch>',
                                  '<MyToggleAction: toggle>'])
        # Auto-generated columns
        multi_select = self.table.columns['multi_select']
        self.assertEqual(multi_select.auto, "multi_select")
        self.assertEqual(multi_select.get_final_attrs().get('class', ""),
                         "multi_select_column")
        actions = self.table.columns['actions']
        self.assertEqual(actions.auto, "actions")
        self.assertEqual(actions.get_final_attrs().get('class', ""),
                         "actions_column")
        # In-line edit action on column.
        name_column = self.table.columns['name']
        self.assertEqual(name_column.update_action, MyUpdateAction)
        self.assertEqual(name_column.form_field.__class__, forms.CharField)
        self.assertEqual(name_column.form_field_attributes, {'class': 'test'})

    def test_table_force_no_multiselect(self):
        class TempTable(MyTable):
            class Meta:
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
            class Meta:
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

            class Meta:
                name = "my_table"
                columns = ('id', 'name', 'value', 'optional', 'status')

        self.table = TempTable(self.request, TEST_DATA_2)
        name_column = self.table.columns['name']
        self.assertIsNone(name_column.update_action)
        self.assertIsNone(name_column.form_field)
        self.assertEqual(name_column.form_field_attributes, {})

    def test_table_natural_no_actions_column(self):
        class TempTable(MyTable):
            class Meta:
                columns = ('id',)
                table_actions = (MyFilterAction, MyAction,)
        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: multi_select>',
                                  '<Column: id>'])

    def test_table_natural_no_multiselect(self):
        class TempTable(MyTable):
            class Meta:
                columns = ('id',)
                row_actions = (MyAction, MyLinkAction,)
        self.table = TempTable(self.request, TEST_DATA)
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: id>',
                                  '<Column: actions>'])

    def test_table_column_inheritance(self):
        class TempTable(MyTable):
            extra = tables.Column('extra')

            class Meta:
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
        self.assertEqual(row.cells['id'].data, '1')  # Standard attr access
        self.assertEqual(row.cells['name'].data, 'custom object_1')  # Callable
        # name and verbose_name
        self.assertEqual(unicode(id_col), "Id")
        self.assertEqual(unicode(name_col), "Verbose Name")
        # sortable
        self.assertEqual(id_col.sortable, False)
        self.assertNotIn("sortable", id_col.get_final_attrs().get('class', ""))
        self.assertEqual(name_col.sortable, True)
        self.assertIn("sortable", name_col.get_final_attrs().get('class', ""))
        # hidden
        self.assertEqual(id_col.hidden, True)
        self.assertIn("hide", id_col.get_final_attrs().get('class', ""))
        self.assertEqual(name_col.hidden, False)
        self.assertNotIn("hide", name_col.get_final_attrs().get('class', ""))
        # link, link_classes and get_link_url
        self.assertIn('href="http://example.com/"', row.cells['value'].value)
        self.assertIn('class="link-modal"', row.cells['value'].value)
        self.assertIn('href="/auth/login/"', row.cells['status'].value)
        # empty_value
        self.assertEqual(row3.cells['optional'].value, "N/A")
        # classes
        self.assertEqual(value_col.get_final_attrs().get('class', ""),
                         "green blue sortable anchor normal_column")
        # status
        cell_status = row.cells['status'].status
        self.assertEqual(cell_status, True)
        self.assertEqual(row.cells['status'].get_status_class(cell_status),
                         'status_up')
        # status_choices
        id_col.status = True
        id_col.status_choices = (('1', False), ('2', True), ('3', None))
        cell_status = row.cells['id'].status
        self.assertEqual(cell_status, False)
        self.assertEqual(row.cells['id'].get_status_class(cell_status),
                         'status_down')
        cell_status = row3.cells['id'].status
        self.assertIsNone(cell_status)
        self.assertEqual(row.cells['id'].get_status_class(cell_status),
                         'status_unknown')

        # Ensure data is not cached on the column across table instances
        self.table = MyTable(self.request, TEST_DATA_2)
        row = self.table.get_rows()[0]
        self.assertTrue("down" in row.cells['status'].value)

    def test_table_row(self):
        self.table = MyTable(self.request, TEST_DATA)
        row = self.table.get_rows()[0]
        self.assertEqual(row.table, self.table)
        self.assertEqual(row.datum, TEST_DATA[0])
        self.assertEqual(row.id, 'my_table__row__1')
        # Verify row status works even if status isn't set on the column
        self.assertEqual(row.status, True)
        self.assertEqual(row.status_class, 'status_up')
        # Check the cells as well
        cell_status = row.cells['status'].status
        self.assertEqual(cell_status, True)
        self.assertEqual(row.cells['status'].get_status_class(cell_status),
                         'status_up')

    def test_table_column_truncation(self):
        self.table = MyTable(self.request, TEST_DATA_5)
        row = self.table.get_rows()[0]

        self.assertEqual(len(row.cells['value'].data), 35)
        self.assertEqual(row.cells['value'].data,
                         u'A Value That is longer than 35 c...')

    def test_table_rendering(self):
        self.table = MyTable(self.request, TEST_DATA)
        # Table actions
        table_actions = self.table.render_table_actions()
        resp = http.HttpResponse(table_actions)
        self.assertContains(resp, "table_search", 1)
        self.assertContains(resp, "my_table__filter__q", 1)
        self.assertContains(resp, "my_table__delete", 1)
        self.assertContains(resp, 'id="my_table__action_delete"', 1)
        # Row actions
        row_actions = self.table.render_row_actions(TEST_DATA[0])
        resp = http.HttpResponse(row_actions)
        self.assertContains(resp, "<li", 3)
        self.assertContains(resp, "my_table__delete__1", 1)
        self.assertContains(resp, "my_table__toggle__1", 1)
        self.assertContains(resp, "/auth/login/", 1)
        self.assertContains(resp, "ajax-modal", 1)
        self.assertContains(resp, 'id="my_table__row_1__action_delete"', 1)
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
        # Verify our XSS protection
        self.assertContains(resp, '<a href="http://example.com/" '
                                  'class="link-modal">'
                                  '&lt;strong&gt;evil&lt;/strong&gt;</a>', 1)
        # Filter = False hides the search box
        self.table._meta.filter = False
        table_actions = self.table.render_table_actions()
        resp = http.HttpResponse(table_actions)
        self.assertContains(resp, "table_search", 0)

    def test_inline_edit_available_cell_rendering(self):
        self.table = MyTable(self.request, TEST_DATA_2)
        row = self.table.get_rows()[0]
        name_cell = row.cells['name']

        # Check if in-line edit is available in the cell,
        # but is not in inline_edit_mod.
        self.assertEqual(name_cell.inline_edit_available,
                         True)
        self.assertEqual(name_cell.inline_edit_mod,
                         False)

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
        self.assertEqual(name_cell.inline_edit_available,
                         True)
        self.assertEqual(name_cell.inline_edit_mod,
                         False)

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
        self.assertEqual(name_cell.inline_edit_available,
                         True)
        self.assertEqual(name_cell.inline_edit_mod,
                         True)
        self.assertEqual(name_col.auto,
                         'form_field')

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

            class Meta:
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

            class Meta:
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
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'delete', '1'))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "http://example.com/?ids=1")

        # Batch action (without toggle) conjugation behavior
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_3)
        toggle_action = self.table.get_row_actions(TEST_DATA_3[0])[2]
        self.assertEqual(unicode(toggle_action.verbose_name), "Batch Item")

        # Single object toggle action
        # GET page - 'up' to 'down'
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_3)
        self.assertEqual(len(self.table.get_row_actions(TEST_DATA_3[0])), 4)
        toggle_action = self.table.get_row_actions(TEST_DATA_3[0])[3]
        self.assertEqual(unicode(toggle_action.verbose_name), "Down Item")

        # Toggle from status 'up' to 'down'
        # POST page
        action_string = "my_table__toggle__1"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'toggle', '1'))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "/my_url/")
        self.assertEqual(list(req._messages)[0].message,
                        u"Downed Item: object_1")

        # Toggle from status 'down' to 'up'
        # GET page - 'down' to 'up'
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_2)
        self.assertEqual(len(self.table.get_row_actions(TEST_DATA_2[0])), 3)
        toggle_action = self.table.get_row_actions(TEST_DATA_2[0])[2]
        self.assertEqual(unicode(toggle_action.verbose_name), "Up Item")

        # POST page
        action_string = "my_table__toggle__2"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'toggle', '2'))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "/my_url/")
        self.assertEqual(list(req._messages)[0].message,
                        u"Upped Item: object_2")

        # Multiple object action
        action_string = "my_table__delete"
        req = self.factory.post('/my_url/', {'action': action_string,
                                             'object_ids': [1, 2]})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'delete', None))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "http://example.com/?ids=1,2")

        # Action with nothing selected
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'delete', None))
        handled = self.table.maybe_handle()
        self.assertIsNone(handled)
        self.assertEqual(list(req._messages)[0].message,
                         "Please select a row before taking that action.")

        # Action with specific id and multiple ids favors single id
        action_string = "my_table__delete__3"
        req = self.factory.post('/my_url/', {'action': action_string,
                                             'object_ids': [1, 2]})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'delete', '3'))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"],
                         "http://example.com/?ids=3")

        # At least one object in table
        # BatchAction is available
        req = self.factory.get('/my_url/')
        self.table = MyTable(req, TEST_DATA_2)
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<MyFilterAction: filter>',
                                  '<MyAction: delete>',
                                  '<MyBatchAction: batch>'])

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
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(unicode(table_actions[0].verbose_name), "Filter")
        self.assertEqual(unicode(table_actions[1].verbose_name), "Delete Me")

        row_actions = self.table.get_row_actions(TEST_DATA[0])
        self.assertEqual(unicode(row_actions[0].verbose_name), "Delete Me")
        self.assertEqual(unicode(row_actions[1].verbose_name), "Log In")

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
        self.assertEqual(handled.status_code, 200)
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
        self.assertEqual(handled.status_code, 401)

    def test_inline_edit_update_action_get_inline_edit_mod(self):
        # Get request in inline_edit_mode should return td with form field.
        url = ('/my_url/?inline_edit_mod=true&action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.get(url, {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.table = MyTable(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertEqual(handled.status_code, 200)
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
        self.assertEqual(handled.status_code, 200)

    def test_inline_edit_update_action_post_not_allowed(self):
        # Post request should invoke the cell update table action.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.post(url, {'name__1': 'test_name'})
        self.table = MyTableNotAllowedInlineEdit(req, TEST_DATA_2)
        # checking the response header
        handled = self.table.maybe_preempt()
        self.assertEqual(handled.status_code, 401)

    def test_inline_edit_update_action_post_validation_error(self):
        # Name column has required validation, sending blank
        # will return error.
        url = ('/my_url/?action=cell_update'
               '&table=my_table&cell_name=name&obj_id=1')
        req = self.factory.post(url, {})
        self.table = MyTable(req, TEST_DATA_2)
        handled = self.table.maybe_preempt()
        # Checking the response header.
        self.assertEqual(handled.status_code, 400)
        self.assertEqual(handled._headers['content-type'],
                         ('Content-Type', 'application/json'))
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

    def test_table_action_object_display_is_none(self):
        action_string = "my_table__toggle__1"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)

        self.mox.StubOutWithMock(self.table, 'get_object_display')
        self.table.get_object_display(IsA(FakeObject)).AndReturn(None)
        self.mox.ReplayAll()

        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'toggle', '1'))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "/my_url/")
        self.assertEqual(list(req._messages)[0].message,
                        u"Downed Item: N/A")

    def test_table_column_can_be_selected(self):
        self.table = MyTableSelectable(self.request, TEST_DATA_6)
        #non selectable row
        row = self.table.get_rows()[0]
        #selectable
        row1 = self.table.get_rows()[1]

        id_col = self.table.columns['id']
        name_col = self.table.columns['name']
        value_col = self.table.columns['value']
        # transform
        self.assertEqual(row.cells['id'].data, '1')  # Standard attr access
        self.assertEqual(row.cells['name'].data, 'custom object_1')  # Callable
        # name and verbose_name
        self.assertEqual(unicode(id_col), "Id")
        self.assertEqual(unicode(name_col), "Verbose Name")
        self.assertIn("sortable", name_col.get_final_attrs().get('class', ""))
        # hidden
        self.assertEqual(id_col.hidden, True)
        self.assertIn("hide", id_col.get_final_attrs().get('class', ""))
        self.assertEqual(name_col.hidden, False)
        self.assertNotIn("hide", name_col.get_final_attrs().get('class', ""))
        # link, link_classes and get_link_url
        self.assertIn('href="http://example.com/"', row.cells['value'].value)
        self.assertIn('class="link-modal"', row.cells['value'].value)
        self.assertIn('href="/auth/login/"', row.cells['status'].value)
        # classes
        self.assertEqual(value_col.get_final_attrs().get('class', ""),
                         "green blue sortable anchor normal_column")

        self.assertQuerysetEqual(row.get_cells(),
                                 ['<Cell: multi_select, my_table__row__1>',
                                  '<Cell: id, my_table__row__1>',
                                  '<Cell: name, my_table__row__1>',
                                  '<Cell: value, my_table__row__1>',
                                  '<Cell: status, my_table__row__1>',
                                  ])
        #can_be_selected = False
        self.assertTrue(row.get_cells()[0].data == "")
        #can_be_selected = True
        self.assertIn('checkbox', row1.get_cells()[0].data)
        #status
        cell_status = row.cells['status'].status
        self.assertEqual(row.cells['status'].get_status_class(cell_status),
                         'status_down')
        # status_choices
        id_col.status = True
        id_col.status_choices = (('1', False), ('2', True))
        cell_status = row.cells['id'].status
        self.assertEqual(cell_status, False)
        self.assertEqual(row.cells['id'].get_status_class(cell_status),
                         'status_down')
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


class TableWithPermissions(tables.DataTable):
    id = tables.Column('id')

    class Meta:
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
        self.assertEqual(context['table'].__class__,
                         SingleTableView.table_class)

    def test_data_table_view_not_authorized(self):
        view = self._prepare_view(SingleTableViewWithPermissions)
        context = view.get_context_data()
        self.assertNotIn('table', context)

    def test_data_table_view_authorized(self):
        view = self._prepare_view(SingleTableViewWithPermissions)
        self.set_permissions(permissions=['test'])
        context = view.get_context_data()
        self.assertIn('table', context)
        self.assertEqual(context['table'].__class__,
                         SingleTableViewWithPermissions.table_class)

    def test_multi_table_view_not_authorized(self):
        view = self._prepare_view(MultiTableView)
        context = view.get_context_data()
        self.assertEqual(context['my_table_table'].__class__, MyTable)
        self.assertNotIn('table_with_permissions_table', context)

    def test_multi_table_view_authorized(self):
        view = self._prepare_view(MultiTableView)
        self.set_permissions(permissions=['test'])
        context = view.get_context_data()
        self.assertEqual(context['my_table_table'].__class__, MyTable)
        self.assertEqual(context['table_with_permissions_table'].__class__,
                         TableWithPermissions)


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

            class Meta:
                name = 'table'

        table = Table(self.request)
        table.data = TEST_DATA_4
        formset = table.get_formset()
        self.assertEqual(len(formset), 2)
        form = formset[0]
        form_data = form.initial
        self.assertEqual(form_data['name'], 'object_1')
        self.assertEqual(form_data['value'], 2)
