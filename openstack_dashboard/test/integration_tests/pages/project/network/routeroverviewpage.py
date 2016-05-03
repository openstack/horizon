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
from openstack_dashboard.test.integration_tests.pages.project.network\
    .networkoverviewpage import NetworkOverviewPage


class RouterOverviewPage(basepage.BaseNavigationPage):

    _network_link_locator = (by.By.CSS_SELECTOR,
                             'hr+dl.dl-horizontal>dt:nth-child(3)+dd>a')

    def __init__(self, driver, conf, router_name):
        super(RouterOverviewPage, self).__init__(driver, conf)
        self._page_title = router_name

    def is_router_name_present(self, router_name):
        dd_text = self._get_element(by.By.XPATH,
                                    "//dd[.='{0}']".format(router_name)).text
        return dd_text == router_name

    def is_router_status(self, status):
        dd_text = self._get_element(by.By.XPATH,
                                    "//dd[.='{0}']".format(status)).text
        return dd_text == status

    def go_to_router_network(self):
        self._get_element(*self._network_link_locator).click()
        return NetworkOverviewPage(self.driver, self.conf)
