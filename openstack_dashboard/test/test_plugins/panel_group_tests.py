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

from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_panels.another_panel \
    import panel as another_panel
from openstack_dashboard.test.test_panels.plugin_panel \
    import panel as plugin_panel
from openstack_dashboard.test.test_panels.second_panel \
    import panel as second_panel
import openstack_dashboard.test.test_plugins.panel_group_config
from openstack_dashboard.utils import settings as util_settings


PANEL_GROUP_SLUG = 'plugin_panel_group'
SECOND_PANEL_GROUP_SLUG = 'second_panel_group'
HORIZON_CONFIG = copy.deepcopy(settings.HORIZON_CONFIG)
INSTALLED_APPS = list(settings.INSTALLED_APPS)

# NOTE: Ensure dashboards and default_dashboard are not included in
# HORIZON_CONFIG to ensure warning messages from update_dashboards below.
HORIZON_CONFIG.pop('dashboards', None)
HORIZON_CONFIG.pop('default_dashboard', None)

util_settings.update_dashboards([
    openstack_dashboard.test.test_plugins.panel_group_config,
], HORIZON_CONFIG, INSTALLED_APPS)


@override_settings(HORIZON_CONFIG=HORIZON_CONFIG,
                   INSTALLED_APPS=INSTALLED_APPS)
class PanelGroupPluginTests(test.PluginTestCase):
    def test_add_panel_group(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertIsNotNone(dashboard.get_panel_group(PANEL_GROUP_SLUG))

    def test_add_second_panel_group(self):
        # Check that the second panel group was added to the dashboard.
        dashboard = horizon.get_dashboard("admin")
        self.assertIsNotNone(
            dashboard.get_panel_group(SECOND_PANEL_GROUP_SLUG))

    def test_add_panel(self):
        # Check that the panel is in its configured dashboard and panel group.
        dashboard = horizon.get_dashboard("admin")
        panel_group = dashboard.get_panel_group(PANEL_GROUP_SLUG)
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in dashboard.get_panels()])
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in panel_group])

    def test_add_second_panel(self):
        # Check that the second panel is in its configured dashboard and panel
        # group.
        dashboard = horizon.get_dashboard("admin")
        second_panel_group = dashboard.get_panel_group(SECOND_PANEL_GROUP_SLUG)
        self.assertIn(second_panel.SecondPanel,
                      [p.__class__ for p in dashboard.get_panels()])
        self.assertIn(second_panel.SecondPanel,
                      [p.__class__ for p in second_panel_group])

    def test_unregistered_panel_group(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertIsNone(dashboard.get_panel_group("nonexistent_panel"))

    def test_add_panel_to_default_panel_group(self):
        dashboard = horizon.get_dashboard('admin')
        default_panel_group = dashboard.get_panel_group('default')
        self.assertIsNotNone(default_panel_group)
        self.assertIn(another_panel.AnotherPanel,
                      [p.__class__ for p in default_panel_group])
