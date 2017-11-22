# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from openstack_dashboard import settings
from openstack_dashboard.templatetags import themes
from openstack_dashboard.test import helpers as test


class SelectableThemeTest(test.TestCase):
    def test_selectable_theme_defaults(self):
        selectable = settings.SELECTABLE_THEMES
        available = settings.AVAILABLE_THEMES
        # NOTE(e0ne): veryfy that by default 'selectable' are the same as
        # 'available' list
        self.assertEqual(selectable, available)

    def test_selectable_override(self):
        selectable = themes.themes()
        available = themes.settings.AVAILABLE_THEMES
        self.assertNotEqual(selectable, available)
