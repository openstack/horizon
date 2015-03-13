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
from django.test.utils import override_settings

import horizon

from openstack_dashboard.dashboards.admin.info import panel as info_panel
from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_panels.plugin_panel \
    import panel as plugin_panel
import openstack_dashboard.test.test_plugins.panel_config
from openstack_dashboard.utils import settings as util_settings


HORIZON_CONFIG = copy.deepcopy(settings.HORIZON_CONFIG)
INSTALLED_APPS = list(settings.INSTALLED_APPS)

# NOTE: Ensure dashboards and default_dashboard are not included in
# HORIZON_CONFIG to ensure warning messages from update_dashboards below.
HORIZON_CONFIG.pop('dashboards', None)
HORIZON_CONFIG.pop('default_dashboard', None)

util_settings.update_dashboards([
    openstack_dashboard.test.test_plugins.panel_config,
], HORIZON_CONFIG, INSTALLED_APPS)


@override_settings(HORIZON_CONFIG=HORIZON_CONFIG,
                   INSTALLED_APPS=INSTALLED_APPS)
class PanelPluginTests(test.PluginTestCase):
    def test_add_panel(self):
        dashboard = horizon.get_dashboard("admin")
        panel_group = dashboard.get_panel_group('admin')
        # Check that the panel is in its configured dashboard.
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in dashboard.get_panels()])
        # Check that the panel is in its configured panel group.
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in panel_group])

    def test_remove_panel(self):
        dashboard = horizon.get_dashboard("admin")
        panel_group = dashboard.get_panel_group('admin')
        # Check that the panel is no longer in the configured dashboard.
        self.assertNotIn(info_panel.Info,
                         [p.__class__ for p in dashboard.get_panels()])
        # Check that the panel is no longer in the configured panel group.
        self.assertNotIn(info_panel.Info,
                         [p.__class__ for p in panel_group])

    def test_default_panel(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertEqual('defaults', dashboard.default_panel)
