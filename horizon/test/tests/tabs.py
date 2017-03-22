# encoding=utf-8
#
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

import copy

from django.conf import settings
from django import http

import six

from horizon import exceptions
from horizon import middleware
from horizon import tabs as horizon_tabs
from horizon.test import helpers as test

from horizon.test.tests.tables import MyTable
from horizon.test.tests.tables import TEST_DATA


class BaseTestTab(horizon_tabs.Tab):
    def get_context_data(self, request):
        return {"tab": self}


class TabOne(BaseTestTab):
    slug = "tab_one"
    name = "Tab One"
    template_name = "_tab.html"


class TabDelayed(BaseTestTab):
    slug = "tab_delayed"
    name = "Delayed Tab"
    template_name = "_tab.html"
    preload = False


class TabDisabled(BaseTestTab):
    slug = "tab_disabled"
    name = "Disabled Tab"
    template_name = "_tab.html"

    def enabled(self, request):
        return False


class TabDisallowed(BaseTestTab):
    slug = "tab_disallowed"
    name = "Disallowed Tab"
    template_name = "_tab.html"

    def allowed(self, request):
        return False


class Group(horizon_tabs.TabGroup):
    slug = "tab_group"
    tabs = (TabOne, TabDelayed, TabDisabled, TabDisallowed)
    sticky = True

    def tabs_not_available(self):
        self._assert_tabs_not_available = True


class TabWithTable(horizon_tabs.TableTab):
    table_classes = (MyTable,)
    name = "Tab With My Table"
    slug = "tab_with_table"
    template_name = "horizon/common/_detail_table.html"

    def get_my_table_data(self):
        return TEST_DATA


class RecoverableErrorTab(horizon_tabs.Tab):
    name = "Recoverable Error Tab"
    slug = "recoverable_error_tab"
    template_name = "_tab.html"

    def get_context_data(self, request):
        # Raise a known recoverable error.
        exc = exceptions.AlreadyExists("Recoverable!", horizon_tabs.Tab)
        exc.silence_logging = True
        raise exc


class RedirectExceptionTab(horizon_tabs.Tab):
    name = "Redirect Exception Tab"
    slug = "redirect_exception_tab"
    template_name = "_tab.html"
    url = settings.TESTSERVER + settings.LOGIN_URL

    def get_context_data(self, request):
        # Raise a known recoverable error.
        exc = exceptions.Http302(self.url)
        exc.silence_logging = True
        raise exc


class TableTabGroup(horizon_tabs.TabGroup):
    slug = "tab_group"
    tabs = [TabWithTable]


class TabWithTableView(horizon_tabs.TabbedTableView):
    tab_group_class = TableTabGroup
    template_name = "tab_group.html"


class TabTests(test.TestCase):
    def test_tab_group_basics(self):
        tg = Group(self.request)

        # Test tab instantiation/attachment to tab group, and get_tabs method
        tabs = tg.get_tabs()
        # "tab_disallowed" should NOT be in this list.
        self.assertQuerysetEqual(tabs, ['<TabOne: tab_one>',
                                        '<TabDelayed: tab_delayed>',
                                        '<TabDisabled: tab_disabled>'])
        # Test get_id
        self.assertEqual("tab_group", tg.get_id())
        # get_default_classes
        self.assertEqual(horizon_tabs.base.CSS_TAB_GROUP_CLASSES,
                         tg.get_default_classes())
        # Test get_tab
        self.assertEqual("tab_one", tg.get_tab("tab_one").slug)

        # Test selected is None w/o GET input
        self.assertIsNone(tg.selected)

        # Test get_selected_tab is None w/o GET input
        self.assertIsNone(tg.get_selected_tab())

    def test_tab_group_active_tab(self):
        tg = Group(self.request)

        # active tab w/o selected
        self.assertEqual(tg.get_tabs()[0], tg.active)

        # active tab w/ selected
        self.request.GET['tab'] = "tab_group__tab_delayed"
        tg = Group(self.request)
        self.assertEqual(tg.get_tab('tab_delayed'), tg.active)

        # active tab w/ invalid selected
        self.request.GET['tab'] = "tab_group__tab_invalid"
        tg = Group(self.request)
        self.assertEqual(tg.get_tabs()[0], tg.active)

        # active tab w/ disallowed selected
        self.request.GET['tab'] = "tab_group__tab_disallowed"
        tg = Group(self.request)
        self.assertEqual(tg.get_tabs()[0], tg.active)

        # active tab w/ disabled selected
        self.request.GET['tab'] = "tab_group__tab_disabled"
        tg = Group(self.request)
        self.assertEqual(tg.get_tabs()[0], tg.active)

        # active tab w/ non-empty garbage selected
        # Note: this entry does not contain the '__' SEPARATOR string.
        self.request.GET['tab'] = "<!--"
        tg = Group(self.request)
        self.assertEqual(tg.get_tabs()[0], tg.active)

    def test_tab_basics(self):
        tg = Group(self.request)
        tab_one = tg.get_tab("tab_one")
        tab_delayed = tg.get_tab("tab_delayed")
        tab_disabled = tg.get_tab("tab_disabled", allow_disabled=True)

        # Disallowed tab isn't even returned
        tab_disallowed = tg.get_tab("tab_disallowed")
        self.assertIsNone(tab_disallowed)

        # get_id
        self.assertEqual("tab_group__tab_one", tab_one.get_id())

        # get_default_classes
        self.assertEqual(horizon_tabs.base.CSS_ACTIVE_TAB_CLASSES,
                         tab_one.get_default_classes())
        self.assertEqual(horizon_tabs.base.CSS_DISABLED_TAB_CLASSES,
                         tab_disabled.get_default_classes())

        # load, allowed, enabled
        self.assertTrue(tab_one.load)
        self.assertFalse(tab_delayed.load)
        self.assertFalse(tab_disabled.load)
        self.request.GET['tab'] = tab_delayed.get_id()
        tg = Group(self.request)
        tab_delayed = tg.get_tab("tab_delayed")
        self.assertTrue(tab_delayed.load)

        # is_active
        self.request.GET['tab'] = ""
        tg = Group(self.request)
        tab_one = tg.get_tab("tab_one")
        tab_delayed = tg.get_tab("tab_delayed")
        self.assertTrue(tab_one.is_active())
        self.assertFalse(tab_delayed.is_active())

        self.request.GET['tab'] = tab_delayed.get_id()
        tg = Group(self.request)
        tab_one = tg.get_tab("tab_one")
        tab_delayed = tg.get_tab("tab_delayed")
        self.assertFalse(tab_one.is_active())
        self.assertTrue(tab_delayed.is_active())

    def test_rendering(self):
        tg = Group(self.request)
        tab_one = tg.get_tab("tab_one")
        tab_delayed = tg.get_tab("tab_delayed")
        tab_disabled = tg.get_tab("tab_disabled", allow_disabled=True)

        # tab group
        output = tg.render()
        res = http.HttpResponse(output.strip())
        self.assertContains(res, "<li", 3)

        # stickiness
        self.assertContains(res, 'data-sticky-tabs="sticky"', 1)

        # tab
        output = tab_one.render()
        self.assertEqual(tab_one.name, output.strip())

        # disabled tab
        output = tab_disabled.render()
        self.assertEqual("", output.strip())

        # preload false
        output = tab_delayed.render()
        self.assertEqual("", output.strip())

        # preload false w/ active
        self.request.GET['tab'] = tab_delayed.get_id()
        tg = Group(self.request)
        tab_delayed = tg.get_tab("tab_delayed")
        output = tab_delayed.render()
        self.assertEqual(tab_delayed.name, output.strip())

    def test_table_tabs(self):
        tab_group = TableTabGroup(self.request)
        tabs = tab_group.get_tabs()
        # Only one tab, as expected.
        self.assertEqual(1, len(tabs))
        tab = tabs[0]
        # Make sure it's the tab we think it is.
        self.assertIsInstance(tab, horizon_tabs.TableTab)
        # Data should not be loaded yet.
        self.assertFalse(tab._table_data_loaded)
        table = tab._tables[MyTable.Meta.name]
        self.assertIsInstance(table, MyTable)
        # Let's make sure the data *really* isn't loaded yet.
        self.assertIsNone(table.data)
        # Okay, load the data.
        tab.load_table_data()
        self.assertTrue(tab._table_data_loaded)
        self.assertQuerysetEqual(table.data,
                                 ['FakeObject: object_1',
                                  'FakeObject: object_2',
                                  'FakeObject: object_3',
                                  u'FakeObject: öbject_4'],
                                 transform=six.text_type)
        context = tab.get_context_data(self.request)
        # Make sure our table is loaded into the context correctly
        self.assertEqual(table, context['my_table_table'])
        # Since we only had one table we should get the shortcut name too.
        self.assertEqual(table, context['table'])

    def test_tabbed_table_view(self):
        view = TabWithTableView.as_view()

        # Be sure we get back a rendered table containing data for a GET
        req = self.factory.get("/")
        res = view(req)
        self.assertContains(res, "<table", 1)
        self.assertContains(res, "Displaying 4 items", 2)

        # AJAX response to GET for row update
        params = {"table": "my_table", "action": "row_update", "obj_id": "1"}
        req = self.factory.get('/', params,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        res = view(req)
        self.assertEqual(200, res.status_code)
        # Make sure we got back a row but not a table or body
        self.assertContains(res, "<tr", 1)
        self.assertContains(res, "<table", 0)
        self.assertContains(res, "<body", 0)

        # Response to POST for table action
        action_string = "my_table__toggle__2"
        req = self.factory.post('/', {'action': action_string})
        res = view(req)
        self.assertEqual(302, res.status_code)
        self.assertEqual("/", res["location"])

        # Ensure that lookup errors are raised as such instead of converted
        # to TemplateSyntaxErrors.
        action_string = "my_table__toggle__2000000000"
        req = self.factory.post('/', {'action': action_string})
        self.assertRaises(exceptions.Http302, view, req)


class TabExceptionTests(test.TestCase):
    def setUp(self):
        super(TabExceptionTests, self).setUp()
        self._original_tabs = copy.copy(TabWithTableView.tab_group_class.tabs)

    def tearDown(self):
        super(TabExceptionTests, self).tearDown()
        TabWithTableView.tab_group_class.tabs = self._original_tabs

    def test_tab_view_exception(self):
        TabWithTableView.tab_group_class.tabs.append(RecoverableErrorTab)
        view = TabWithTableView.as_view()
        req = self.factory.get("/")
        res = view(req)
        self.assertMessageCount(res, error=1)

    def test_tab_302_exception(self):
        TabWithTableView.tab_group_class.tabs.append(RedirectExceptionTab)
        view = TabWithTableView.as_view()
        req = self.factory.get("/")
        mw = middleware.HorizonMiddleware()
        try:
            resp = view(req)
        except Exception as e:
            resp = mw.process_exception(req, e)
            resp.client = self.client
        self.assertRedirects(resp, RedirectExceptionTab.url)
