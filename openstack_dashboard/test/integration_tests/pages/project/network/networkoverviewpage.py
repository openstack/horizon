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


class NetworkOverviewPage(basepage.BaseNavigationPage):

    DEFAULT_NETWORK_NAME = 'public'

    _network_dd_name_locator = (by.By.CSS_SELECTOR,
                                'dt[title*="Name"]+dd')

    _network_dd_status_locator = (by.By.CSS_SELECTOR,
                                  'dt[title*="Status"]+dd')

    def __init__(self, driver, conf):
        super(NetworkOverviewPage, self).__init__(driver, conf)
        self._page_title = 'Network Details'

    def is_network_name_present(self, network_name=DEFAULT_NETWORK_NAME):
        dd_text = self._get_element(*self._network_dd_name_locator).text
        return dd_text == network_name

    def is_network_status(self, status):
        dd_text = self._get_element(*self._network_dd_status_locator).text
        return dd_text == status
