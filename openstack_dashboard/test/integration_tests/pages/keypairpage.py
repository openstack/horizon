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


class KeypairPage(basepage.BasePage):

    _keypair_create_button_locator = (by.By.CSS_SELECTOR,
                                      '#keypairs__action_create')
    _keypair_name_field_locator = (by.By.CSS_SELECTOR, '#id_name')
    _keypair_submit_button_locator = (by.By.CSS_SELECTOR,
                                      '.btn.btn-primary.pull-right')
    _keypair_delete_cnf_button_locator = (by.By.CSS_SELECTOR,
                                          '.btn.btn-primary')

    def __init__(self, driver, conf):
        super(KeypairPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    @property
    def keypair_create(self):
        return self.get_element(*self._keypair_create_button_locator)

    @property
    def keypair_name_field(self):
        return self.get_element(*self._keypair_name_field_locator)

    @property
    def keypair_submit_button(self):
        return self.get_element(*self._keypair_submit_button_locator)

    @property
    def keypair_delete_cnf_button(self):
        return self.get_element(*self._keypair_delete_cnf_button_locator)

    def _click_on_keypair_create(self):
        self.keypair_create.click()

    def _click_on_keypair_submit_button(self):
        self.keypair_submit_button.click()

    def _click_on_keypair_delete_cnf_button(self):
        self.keypair_delete_cnf_button.click()

    def get_keypair_status(self, keypair_name):
        keypair_locator = (by.By.CSS_SELECTOR,
                           '#keypairs__row__%s' % keypair_name)
        keypair_status = self.is_element_present(*keypair_locator)
        return keypair_status

    def create_keypair(self, keypair_name):
        self._click_on_keypair_create()
        self.keypair_name_field.send_keys(keypair_name)
        self._click_on_keypair_submit_button()

    def delete_keypair(self, keypair_name):
        keypair_delete_check_locator = (
            by.By.CSS_SELECTOR,
            "#keypairs__row_%s__action_delete" % keypair_name)
        self.driver.find_element(
            *keypair_delete_check_locator).click()
        self._click_on_keypair_delete_cnf_button()
