# Copyrigh:t 2015 Hewlett-Packard Development Company, L.P
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

import re

from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class FloatingipsPage(basepage.BaseNavigationPage):
    FLOATING_IPS_TABLE_NAME_COLUMN_INDEX = 0

    _floating_ips_table_locator = (by.By.ID, 'floating_ips')

    _floatingips_fadein_popup_locator = (
        by.By.CSS_SELECTOR, '.alert.alert-success.alert-dismissable.fade.in>p')

    FLOATING_IPS_TABLE_NAME = 'floating_ips'
    FLOATING_IPS_TABLE_ACTIONS = ("allocate", "release")
    FLOATING_IPS_TABLE_ROW_ACTION = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "associate",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: (
            "release_floating_ip",)
    }

    def __init__(self, driver, conf):
        super(FloatingipsPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    def _get_row_with_floatingip(self, floatingip):
        return self.floatingips_table.get_row(
            self.FLOATING_IPS_TABLE_NAME_COLUMN_INDEX, floatingip)

    @property
    def floatingips_table(self):
        src_elem = self._get_element(*self._floating_ips_table_locator)
        return tables.ComplexActionTableRegion(
            self.driver, self.conf, src_elem,
            self.FLOATING_IPS_TABLE_NAME,
            self.FLOATING_IPS_TABLE_ACTIONS,
            self.FLOATING_IPS_TABLE_ROW_ACTION)

    @property
    def floatingip_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def allocate_floatingip(self):
        self.floatingips_table.allocate.click()
        self.floatingip_form.submit.click()
        ip = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)'
                        + '|([0-1]?[0-9]?[0-9]\.)){3}(([2][5][0-5])|'
                        '([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
        match = ip.search((self._get_element(
            *self._floatingips_fadein_popup_locator)).text)
        floatingip = str(match.group())
        self.wait_till_popups_disappear()
        return floatingip

    def release_floatingip(self, floatingip):
        row = self._get_row_with_floatingip(floatingip)
        row.mark()
        self.floatingips_table.release.click()
        self.floatingip_form.submit.click()
        self.wait_till_popups_disappear()

    def is_floatingip_present(self, floatingip):
        return bool(self._get_row_with_floatingip(floatingip))
