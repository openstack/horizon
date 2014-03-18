# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from django.core import urlresolvers
from django.test.utils import override_settings
from django.utils.importlib import import_module  # noqa

import horizon
from horizon import base
from horizon import conf

from openstack_dashboard.dashboards.admin.info import panel as info_panel
from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_panels.plugin_panel \
    import panel as plugin_panel
import openstack_dashboard.test.test_plugins.panel_config
from openstack_dashboard.utils import settings as util_settings


HORIZON_CONFIG = copy.copy(settings.HORIZON_CONFIG)
INSTALLED_APPS = list(settings.INSTALLED_APPS)

util_settings.update_dashboards([
    openstack_dashboard.test.test_plugins.panel_config,
], HORIZON_CONFIG, INSTALLED_APPS)


@override_settings(HORIZON_CONFIG=HORIZON_CONFIG,
                   INSTALLED_APPS=INSTALLED_APPS)
class PanelPluginTests(test.TestCase):

    def setUp(self):
        super(PanelPluginTests, self).setUp()
        self.old_horizon_config = conf.HORIZON_CONFIG
        conf.HORIZON_CONFIG = conf.LazySettings()
        base.Horizon._urls()
        # Trigger discovery, registration, and URLconf generation if it
        # hasn't happened yet.
        self.client.get("/")

    def tearDown(self):
        super(PanelPluginTests, self).tearDown()
        conf.HORIZON_CONFIG = self.old_horizon_config
        # Destroy our singleton and re-create it.
        base.HorizonSite._instance = None
        del base.Horizon
        base.Horizon = base.HorizonSite()
        self._reload_urls()

    def _reload_urls(self):
        """Clears out the URL caches, reloads the root urls module, and
        re-triggers the autodiscovery mechanism for Horizon. Allows URLs
        to be re-calculated after registering new dashboards. Useful
        only for testing and should never be used on a live site.
        """
        urlresolvers.clear_url_caches()
        reload(import_module(settings.ROOT_URLCONF))
        base.Horizon._urls()

    def test_add_panel(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in dashboard.get_panels()])

    def test_remove_panel(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertNotIn(info_panel.Info,
                         [p.__class__ for p in dashboard.get_panels()])

    def test_default_panel(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertEqual('instances', dashboard.default_panel)
