# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import copy

from django.core.urlresolvers import NoReverseMatch
from django.test.client import Client

import horizon
from horizon import base
from horizon import exceptions
from horizon import test
from horizon import users
from horizon.base import Horizon


class MyDash(horizon.Dashboard):
    name = "My Dashboard"
    slug = "mydash"


class MyPanel(horizon.Panel):
    name = "My Panel"
    slug = "myslug"


class HorizonTests(test.TestCase):
    def setUp(self):
        super(HorizonTests, self).setUp()
        self._orig_horizon = copy.deepcopy(base.Horizon)

    def tearDown(self):
        super(HorizonTests, self).tearDown()
        base.Horizon = self._orig_horizon

    def test_registry(self):
        """ Verify registration and autodiscovery work correctly.

        Please note that this implicitly tests that autodiscovery works
        by virtue of the fact that the dashboards listed in
        ``settings.INSTALLED_APPS`` are loaded from the start.
        """

        # Registration
        self.assertEqual(len(Horizon._registry), 3)
        horizon.register(MyDash)
        self.assertEqual(len(Horizon._registry), 4)
        with self.assertRaises(ValueError):
            horizon.register(MyPanel)
        with self.assertRaises(ValueError):
            horizon.register("MyPanel")

        # Retrieval
        my_dash_instance_by_name = horizon.get_dashboard("mydash")
        self.assertTrue(isinstance(my_dash_instance_by_name, MyDash))
        my_dash_instance_by_class = horizon.get_dashboard(MyDash)
        self.assertEqual(my_dash_instance_by_name, my_dash_instance_by_class)
        with self.assertRaises(base.NotRegistered):
            horizon.get_dashboard("fake")
        self.assertQuerysetEqual(horizon.get_dashboards(),
                                 ['<Dashboard: Project>',
                                  '<Dashboard: Admin>',
                                  '<Dashboard: Settings>',
                                  '<Dashboard: My Dashboard>'])

        # Removal
        self.assertEqual(len(Horizon._registry), 4)
        horizon.unregister(MyDash)
        self.assertEqual(len(Horizon._registry), 3)
        with self.assertRaises(base.NotRegistered):
            horizon.get_dashboard(MyDash)

    def test_site(self):
        self.assertEqual(unicode(Horizon), "Horizon")
        self.assertEqual(repr(Horizon), "<Site: Horizon>")
        dash = Horizon.get_dashboard('nova')
        self.assertEqual(Horizon.get_default_dashboard(), dash)
        user = users.User()
        self.assertEqual(Horizon.get_user_home(user), dash.get_absolute_url())

    def test_dashboard(self):
        syspanel = horizon.get_dashboard("syspanel")
        self.assertEqual(syspanel._registered_with, Horizon)
        self.assertQuerysetEqual(syspanel.get_panels()['System Panel'],
                                 ['<Panel: Overview>',
                                 '<Panel: Instances>',
                                 '<Panel: Services>',
                                 '<Panel: Flavors>',
                                 '<Panel: Images>',
                                 '<Panel: Tenants>',
                                 '<Panel: Users>',
                                 '<Panel: Quotas>'])
        self.assertEqual(syspanel.get_absolute_url(), "/syspanel/")
        # Test registering a module with a dashboard that defines panels
        # as a dictionary.
        syspanel.register(MyPanel)
        self.assertQuerysetEqual(syspanel.get_panels()['Other'],
                                 ['<Panel: My Panel>'])

        # Test registering a module with a dashboard that defines panels
        # as a tuple.
        settings_dash = horizon.get_dashboard("settings")
        settings_dash.register(MyPanel)
        self.assertQuerysetEqual(settings_dash.get_panels(),
                                 ['<Panel: User Settings>',
                                  '<Panel: Tenant Settings>',
                                  '<Panel: My Panel>'])

    def test_panels(self):
        syspanel = horizon.get_dashboard("syspanel")
        instances = syspanel.get_panel("instances")
        self.assertEqual(instances._registered_with, syspanel)
        self.assertEqual(instances.get_absolute_url(), "/syspanel/instances/")

    def test_index_url_name(self):
        syspanel = horizon.get_dashboard("syspanel")
        instances = syspanel.get_panel("instances")
        instances.index_url_name = "does_not_exist"
        with self.assertRaises(NoReverseMatch):
            instances.get_absolute_url()
        instances.index_url_name = "index"
        self.assertEqual(instances.get_absolute_url(), "/syspanel/instances/")

    def test_lazy_urls(self):
        urlpatterns = horizon.urls[0]
        self.assertTrue(isinstance(urlpatterns, base.LazyURLPattern))
        # The following two methods simply should not raise any exceptions
        iter(urlpatterns)
        reversed(urlpatterns)


class HorizonBaseViewTests(test.BaseViewTests):
    def setUp(self):
        super(HorizonBaseViewTests, self).setUp()
        users.get_user_from_request = self._real_get_user_from_request

    def test_public(self):
        settings = horizon.get_dashboard("settings")
        # Known to have no restrictions on it other than being logged in.
        user_panel = settings.get_panel("user")
        url = user_panel.get_absolute_url()
        client = Client()  # Get a clean, logged out client instance.
        client.logout()
        resp = client.get(url)
        self.assertRedirectsNoFollow(resp, '/accounts/login/?next=/settings/')
