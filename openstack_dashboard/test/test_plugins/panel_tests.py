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
from openstack_dashboard.test.test_panels.nonloading_panel \
    import panel as nonloading_panel
from openstack_dashboard.test.test_plugins import panel_config
from openstack_dashboard.utils import settings as util_settings


HORIZON_CONFIG = copy.deepcopy(settings.HORIZON_CONFIG)
INSTALLED_APPS = list(settings.INSTALLED_APPS)

# NOTE: Ensure dashboards and default_dashboard are not included in
# HORIZON_CONFIG to ensure warning messages from update_dashboards below.
HORIZON_CONFIG.pop('dashboards', None)
HORIZON_CONFIG.pop('default_dashboard', None)
HORIZON_CONFIG.pop('js_files', None)
HORIZON_CONFIG.pop('js_spec_files', None)
HORIZON_CONFIG.pop('scss_files', None)
HORIZON_CONFIG.pop('xstatic_modules', None)

util_settings.update_dashboards([panel_config,], HORIZON_CONFIG, INSTALLED_APPS)


@override_settings(HORIZON_CONFIG=HORIZON_CONFIG,
                   INSTALLED_APPS=INSTALLED_APPS)
class PanelPluginTests(test.PluginTestCase):
    urls = 'openstack_dashboard.test.extensible_header_urls'

    def test_add_panel(self):
        dashboard = horizon.get_dashboard("admin")
        panel_group = dashboard.get_panel_group('admin')
        # Check that the panel is in its configured dashboard.
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in dashboard.get_panels()])
        # Check that the panel is in its configured panel group.
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in panel_group])
        # Ensure that static resources are properly injected
        pc = panel_config._10_admin_add_panel
        self.assertEqual(pc.ADD_JS_FILES, HORIZON_CONFIG['js_files'])
        self.assertEqual(pc.ADD_JS_SPEC_FILES, HORIZON_CONFIG['js_spec_files'])
        self.assertEqual(pc.ADD_SCSS_FILES, HORIZON_CONFIG['scss_files'])
        self.assertEqual(pc.ADD_XSTATIC_MODULES,
                         HORIZON_CONFIG['xstatic_modules'])
        self.assertEqual(pc.ADD_HEADER_SECTIONS,
                         HORIZON_CONFIG['header_sections'])

    def test_extensible_header(self):
        with self.settings(ROOT_URLCONF=self.urls):
            response = self.client.get('/header/')
            self.assertIn('sample context', response.content.decode('utf-8'))

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

    def test_panel_not_added(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertNotIn(nonloading_panel.NonloadingPanel,
                         [p.__class__ for p in dashboard.get_panels()])
