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

from openstack_dashboard.test.integration_tests import helpers


class TestDashboardHelp(helpers.TestCase):

    def test_dashboard_help_redirection(self):
        """Verifies Help link redirects to the right URL."""

        self.home_pg.go_to_help_page()
        self.home_pg._wait_until(
            lambda _: self.home_pg.is_nth_window_opened(2))
        self.home_pg.switch_window()

        self.assertEqual(self.CONFIG.dashboard.help_url,
                         self.home_pg.get_url_current_page(),
                         "help link did not redirect to the right URL")

        self.home_pg.close_window()
        self.home_pg.switch_window()
