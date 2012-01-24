# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

from django import http
from django import shortcuts
from django.core.urlresolvers import reverse

from horizon import tables
from horizon import test


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


class MyLinkAction(tables.LinkAction):
    name = "login"
    verbose_name = "Log In"
    url = "horizon:auth_login"
    attrs = {
        "class": "ajax-modal",
    }

    def get_link_url(self, datum=None, *args, **kwargs):
        return reverse(self.url)


class MyAction(tables.Action):
    name = "click"
    verbose_name = "Click Me"
    verbose_name_plural = "Click Them"

    def allowed(self, request, obj=None):
        return getattr(obj, 'status', None) != 'down'

    def handle(self, data_table, request, object_ids):
        return shortcuts.redirect('http://example.com/%s' % len(object_ids))


class MyFilterAction(tables.FilterAction):
    def filter(self, table, objs, filter_string):
        q = filter_string.lower()

        def comp(obj):
            if q in obj.name.lower():
                return True
            return False

        return filter(comp, objs)


def get_name(obj):
    return "custom %s" % obj.name


def get_link(obj):
    return reverse('horizon:auth_login')


class MyTable(tables.DataTable):
    id = tables.Column('id', hidden=True)
    name = tables.Column(get_name, verbose_name="Verbose Name", sortable=True)
    value = tables.Column('value',
                          sortable=True,
                          link='http://example.com/',
                          attrs={'classes': ('green', 'blue')})
    status = tables.Column('status', link=get_link)
    optional = tables.Column('optional', empty_value='N/A')
    excluded = tables.Column('excluded')

    class Meta:
        name = "my_table"
        verbose_name = "My Table"
        status_column = "status"
        columns = ('id', 'name', 'value', 'optional', 'status')
        table_actions = (MyFilterAction, MyAction,)
        row_actions = (MyAction, MyLinkAction,)


class DataTableTests(test.TestCase):
    def test_table_instantiation(self):
        """ Tests everything that happens when the table is instantiated. """
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
        self.assertQuerysetEqual(self.table.columns.values(),
                                 ['<Column: multi_select>',
                                  '<Column: id>',
                                  '<Column: name>',
                                  '<Column: value>',
                                  '<Column: optional>',
                                  '<Column: status>',
                                  '<Column: actions>'])
        # Actions (these also test ordering)
        self.assertQuerysetEqual(self.table.base_actions.values(),
                                 ['<MyAction: click>',
                                  '<MyFilterAction: filter>',
                                  '<MyLinkAction: login>'])
        self.assertQuerysetEqual(self.table.get_table_actions(),
                                 ['<MyFilterAction: filter>',
                                  '<MyAction: click>'])
        self.assertQuerysetEqual(self.table.get_row_actions(TEST_DATA[0]),
                                 ['<MyAction: click>',
                                  '<MyLinkAction: login>'])
        # Auto-generated columns
        multi_select = self.table.columns['multi_select']
        self.assertEqual(multi_select.auto, "multi_select")
        self.assertEqual(multi_select.get_classes(), "multi_select_column")
        actions = self.table.columns['actions']
        self.assertEqual(actions.auto, "actions")
        self.assertEqual(actions.get_classes(), "actions_column")

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
        self.assertQuerysetEqual(columns, ['<Column: multi_select>',
                                           '<Column: id>',
                                           '<Column: name>',
                                           '<Column: value>',
                                           '<Column: optional>',
                                           '<Column: status>',
                                           '<Column: actions>'])
        # Verify we retrieve the right rows from our data
        rows = self.table.get_rows()
        self.assertQuerysetEqual(rows, ['<Row: my_table__row__1>',
                                        '<Row: my_table__row__2>',
                                        '<Row: my_table__row__3>'])
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
        id_col = self.table.base_columns['id']
        name_col = self.table.base_columns['name']
        value_col = self.table.base_columns['value']
        # transform
        self.assertEqual(row.cells['id'].data, '1')  # Standard attr access
        self.assertEqual(row.cells['name'].data, 'custom object_1')  # Callable
        # name and verbose_name
        self.assertEqual(unicode(id_col), "Id")
        self.assertEqual(unicode(name_col), "Verbose Name")
        # sortable
        self.assertEqual(id_col.sortable, False)
        self.assertNotIn("sortable", id_col.get_classes())
        self.assertEqual(name_col.sortable, True)
        self.assertIn("sortable", name_col.get_classes())
        # hidden
        self.assertEqual(id_col.hidden, True)
        self.assertIn("hide", id_col.get_classes())
        self.assertEqual(name_col.hidden, False)
        self.assertNotIn("hide", name_col.get_classes())
        # link and get_link_url
        self.assertIn('href="http://example.com/"', row.cells['value'].value)
        self.assertIn('href="/auth/login/"', row.cells['status'].value)
        # empty_value
        self.assertEqual(row3.cells['optional'].value, "N/A")
        # get_classes
        self.assertEqual(value_col.get_classes(), "green blue sortable")
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
        self.assertEqual(cell_status, None)
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

    def test_table_rendering(self):
        self.table = MyTable(self.request, TEST_DATA)
        # Table actions
        table_actions = self.table.render_table_actions()
        resp = http.HttpResponse(table_actions)
        self.assertContains(resp, "table_search", 1)
        self.assertContains(resp, "my_table__filter__q", 1)
        self.assertContains(resp, "my_table__click", 1)
        # Row actions
        row_actions = self.table.render_row_actions(TEST_DATA[0])
        resp = http.HttpResponse(row_actions)
        self.assertContains(resp, "<li", 1)
        self.assertContains(resp, "my_table__click__1", 1)
        self.assertContains(resp, "/auth/login/", 1)
        self.assertContains(resp, "ajax-modal", 1)
        # Whole table
        resp = http.HttpResponse(self.table.render())
        self.assertContains(resp, '<table id="my_table"', 1)
        self.assertContains(resp, '<th ', 7)
        self.assertContains(resp, '<tr id="my_table__row__1"', 1)
        self.assertContains(resp, '<tr id="my_table__row__2"', 1)
        self.assertContains(resp, '<tr id="my_table__row__3"', 1)
        # Verify our XSS protection
        self.assertContains(resp, '<a href="http://example.com/">'
                                  '&lt;strong&gt;evil&lt;/strong&gt;</a>', 1)
        # Filter = False hides the search box
        self.table._meta.filter = False
        table_actions = self.table.render_table_actions()
        resp = http.HttpResponse(table_actions)
        self.assertContains(resp, "table_search", 0)

    def test_table_actions(self):
        # Single object action
        action_string = "my_table__click__1"
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'click', '1'))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "http://example.com/1")

        # Multiple object action
        action_string = "my_table__click"
        req = self.factory.post('/my_url/', {'action': action_string,
                                             'object_ids': [1, 2]})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'click', None))
        handled = self.table.maybe_handle()
        self.assertEqual(handled.status_code, 302)
        self.assertEqual(handled["location"], "http://example.com/2")

        # Action with nothing selected
        req = self.factory.post('/my_url/', {'action': action_string})
        self.table = MyTable(req, TEST_DATA)
        self.assertEqual(self.table.parse_action(action_string),
                         ('my_table', 'click', None))
        handled = self.table.maybe_handle()
        self.assertEqual(handled, None)
        self.assertEqual(list(req._messages)[0].message,
                         "Please select a row before taking that action.")

        # Filtering
        action_string = "my_table__filter__q"
        req = self.factory.post('/my_url/', {action_string: '2'})
        self.table = MyTable(req, TEST_DATA)
        handled = self.table.maybe_handle()
        self.assertEqual(handled, None)
        self.assertQuerysetEqual(self.table.filtered_data,
                                 ['<FakeObject: object_2>'])
