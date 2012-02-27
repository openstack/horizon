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

from django import http
from django.utils.translation import ugettext_lazy as _

from horizon import tabs as horizon_tabs
from horizon import test


class BaseTestTab(horizon_tabs.Tab):
    def get_context_data(self, request):
        return {"tab": self}


class TabOne(BaseTestTab):
    slug = "tab_one"
    name = _("Tab One")
    template_name = "_tab.html"


class TabDelayed(BaseTestTab):
    slug = "tab_delayed"
    name = _("Delayed Tab")
    template_name = "_tab.html"
    preload = False


class TabDisabled(BaseTestTab):
    slug = "tab_disabled"
    name = _("Disabled Tab")
    template_name = "_tab.html"

    def enabled(self, request):
        return False


class TabDisallowed(BaseTestTab):
    slug = "tab_disallowed"
    name = _("Disallowed Tab")
    template_name = "_tab.html"

    def allowed(self, request):
        return False


class Group(horizon_tabs.TabGroup):
    slug = "tab_group"
    tabs = (TabOne, TabDelayed, TabDisabled, TabDisallowed)

    def tabs_not_available(self):
        self._assert_tabs_not_available = True


class TabTests(test.TestCase):
    def setUp(self):
        super(TabTests, self).setUp()

    def test_tab_group_basics(self):
        tg = Group(self.request)

        # Test tab instantiation/attachement to tab group, and get_tabs method
        tabs = tg.get_tabs()
        # "tab_disallowed" should NOT be in this list.
        self.assertQuerysetEqual(tabs, ['<TabOne: tab_one>',
                                        '<TabDelayed: tab_delayed>',
                                        '<TabDisabled: tab_disabled>'])
        # Test get_id
        self.assertEqual(tg.get_id(), "tab_group")
        # get_default_classes
        self.assertEqual(tg.get_default_classes(),
                         horizon_tabs.base.CSS_TAB_GROUP_CLASSES)
        # Test get_tab
        self.assertEqual(tg.get_tab("tab_one").slug, "tab_one")

        # Test selected is None w/o GET input
        self.assertEqual(tg.selected, None)

        # Test get_selected_tab is None w/o GET input
        self.assertEqual(tg.get_selected_tab(), None)

    def test_tab_group_active_tab(self):
        tg = Group(self.request)

        # active tab w/o selected
        self.assertEqual(tg.active, tg.get_tabs()[0])

        # active tab w/ selected
        self.request.GET['tab'] = "tab_group__tab_delayed"
        tg = Group(self.request)
        self.assertEqual(tg.active, tg.get_tab('tab_delayed'))

        # active tab w/ invalid selected
        self.request.GET['tab'] = "tab_group__tab_invalid"
        tg = Group(self.request)
        self.assertEqual(tg.active, tg.get_tabs()[0])

        # active tab w/ disallowed selected
        self.request.GET['tab'] = "tab_group__tab_disallowed"
        tg = Group(self.request)
        self.assertEqual(tg.active, tg.get_tabs()[0])

        # active tab w/ disabled selected
        self.request.GET['tab'] = "tab_group__tab_disabled"
        tg = Group(self.request)
        self.assertEqual(tg.active, tg.get_tabs()[0])

    def test_tab_basics(self):
        tg = Group(self.request)
        tab_one = tg.get_tab("tab_one")
        tab_delayed = tg.get_tab("tab_delayed")
        tab_disabled = tg.get_tab("tab_disabled", allow_disabled=True)

        # Disallowed tab isn't even returned
        tab_disallowed = tg.get_tab("tab_disallowed")
        self.assertEqual(tab_disallowed, None)

        # get_id
        self.assertEqual(tab_one.get_id(), "tab_group__tab_one")

        # get_default_classes
        self.assertEqual(tab_one.get_default_classes(),
                         horizon_tabs.base.CSS_ACTIVE_TAB_CLASSES)
        self.assertEqual(tab_disabled.get_default_classes(),
                         horizon_tabs.base.CSS_DISABLED_TAB_CLASSES)

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

        # tab
        output = tab_one.render()
        self.assertEqual(output.strip(), tab_one.name)

        # disabled tab
        output = tab_disabled.render()
        self.assertEqual(output.strip(), "")

        # preload false
        output = tab_delayed.render()
        self.assertEqual(output.strip(), "")

        # preload false w/ active
        self.request.GET['tab'] = tab_delayed.get_id()
        tg = Group(self.request)
        tab_delayed = tg.get_tab("tab_delayed")
        output = tab_delayed.render()
        self.assertEqual(output.strip(), tab_delayed.name)
