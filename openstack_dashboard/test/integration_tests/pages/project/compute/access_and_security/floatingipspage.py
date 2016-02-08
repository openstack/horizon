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


class FloatingIPTable(tables.TableRegion):
    name = 'floating_ips'
    FLOATING_IP_ASSOCIATIONS = (
        ("ip_id", "instance_id"))

    @tables.bind_table_action('allocate')
    def allocate_ip(self, allocate_button):
        allocate_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_table_action('release')
    def release_ip(self, release_button):
        release_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('associate', primary=True)
    def associate_ip(self, associate_button, row):
        associate_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.FLOATING_IP_ASSOCIATIONS)

    @tables.bind_row_action('disassociate', primary=True)
    def disassociate_ip(self, disassociate_button, row):
        disassociate_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class FloatingipsPage(basepage.BaseNavigationPage):
    FLOATING_IPS_TABLE_IP_COLUMN = 'ip'
    FLOATING_IPS_TABLE_FIXED_IP_COLUMN = 'fixed_ip'

    _floatingips_fadein_popup_locator = (
        by.By.CSS_SELECTOR, '.alert.alert-success.alert-dismissable.fade.in>p')

    def __init__(self, driver, conf):
        super(FloatingipsPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    def _get_row_with_floatingip(self, floatingip):
        return self.floatingips_table.get_row(
            self.FLOATING_IPS_TABLE_IP_COLUMN, floatingip)

    @property
    def floatingips_table(self):
        return FloatingIPTable(self.driver, self.conf)

    def allocate_floatingip(self):
        floatingip_form = self.floatingips_table.allocate_ip()
        floatingip_form.submit()
        ip = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)'
                        + '|([0-1]?[0-9]?[0-9]\.)){3}(([2][5][0-5])|'
                        '([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
        match = ip.search((self._get_element(
            *self._floatingips_fadein_popup_locator)).text)
        floatingip = str(match.group())
        return floatingip

    def release_floatingip(self, floatingip):
        row = self._get_row_with_floatingip(floatingip)
        row.mark()
        modal_confirmation_form = self.floatingips_table.release_ip()
        modal_confirmation_form.submit()

    def is_floatingip_present(self, floatingip):
        return bool(self._get_row_with_floatingip(floatingip))

    def associate_floatingip(self, floatingip, instance_name=None,
                             instance_ip=None):
        row = self._get_row_with_floatingip(floatingip)
        floatingip_form = self.floatingips_table.associate_ip(row)
        floatingip_form.instance_id.text = "{}: {}".format(instance_name,
                                                           instance_ip)
        floatingip_form.submit()

    def disassociate_floatingip(self, floatingip):
        row = self._get_row_with_floatingip(floatingip)
        floatingip_form = self.floatingips_table.disassociate_ip(row)
        floatingip_form.submit()

    def get_fixed_ip(self, floatingip):
        row = self._get_row_with_floatingip(floatingip)
        return row.cells[self.FLOATING_IPS_TABLE_FIXED_IP_COLUMN].text
