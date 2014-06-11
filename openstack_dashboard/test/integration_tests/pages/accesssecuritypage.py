# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
#
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
from openstack_dashboard.test.integration_tests.pages import keypairpage


class AccessSecurityPage(basepage.BasePage):

    _keypair_link_locator = (
        by.By.CSS_SELECTOR,
        'a[href*="?tab=access_security_tabs__keypairs_tab"]')

    def __init__(self, driver, conf):
        super(AccessSecurityPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    @property
    def keypair_link(self):
        return self.get_element(*self._keypair_link_locator)

    def _click_on_keypair_link(self):
        self.keypair_link.click()

    def go_to_keypair_page(self):
        self._click_on_keypair_link()
        return keypairpage.KeypairPage(self.driver, self.conf)
