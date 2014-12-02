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
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.pages.project.compute.\
    access_and_security import accesssecuritypage
from openstack_dashboard.test.integration_tests.pages.settings import \
    settingspage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class OverviewPage(basepage.BasePage):
    _usage_table_locator = (by.By.CSS_SELECTOR, 'table#project_usage')
    _date_form_locator = (by.By.CSS_SELECTOR, 'form#date_form')

    USAGE_TABLE_ACTIONS = ("download_csv",)

    def __init__(self, driver, conf):
        super(OverviewPage, self).__init__(driver, conf)
        self._page_title = 'Instance Overview'

    def go_to_settings_page(self):
        self.topbar.user_dropdown_menu.click_on_settings()
        return settingspage.SettingsPage(self.driver, self.conf)

    def go_to_accesssecurity_page(self):
        access_security_locator_flag = self._is_element_visible(
            *self.navaccordion._project_access_security_locator)
        if not access_security_locator_flag:
            self.navaccordion.project_bar.click()
        self.navaccordion.access_security.click()
        return accesssecuritypage.AccessSecurityPage(
            self.driver, self.conf)

    @property
    def usage_table(self):
        src_elem = self._get_element(*self._usage_table_locator)
        return tables.ActionsTableRegion(self.driver, self.conf, src_elem,
                                         self.USAGE_TABLE_ACTIONS)

    @property
    def date_form(self):
        src_elem = self._get_element(*self._date_form_locator)
        return forms.DateFormRegion(self.driver, self.conf, src_elem)
