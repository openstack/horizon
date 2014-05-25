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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.pages import settingspage


class ProjectPage(basepage.BasePage):
    def __init__(self, driver, conf):
        super(ProjectPage, self).__init__(driver, conf)
        self._page_title = 'Instance Overview'

    def go_to_settings_page(self):
        self.topbar.user_dropdown_menu.click()
        self.topbar.settings_link.click()
        return settingspage.SettingsPage(self.driver, self.conf)
