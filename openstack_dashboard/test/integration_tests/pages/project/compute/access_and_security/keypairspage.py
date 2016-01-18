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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class KeypairsPage(basepage.BaseNavigationPage):

    KEY_PAIRS_TABLE_NAME = "keypairs"
    KEY_PAIRS_TABLE_ACTIONS = ("create", "import", "delete")
    KEY_PAIRS_TABLE_ROW_ACTION = "delete"
    KEY_PAIRS_TABLE_NAME_COLUMN_INDEX = 0

    CREATE_KEY_PAIR_FORM_FIELDS = ('name',)

    def __init__(self, driver, conf):
        super(KeypairsPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    def _get_row_with_keypair_name(self, name):
        return self.keypairs_table.get_row(
            self.KEY_PAIRS_TABLE_NAME_COLUMN_INDEX, name)

    @property
    def keypairs_table(self):
        return tables.SimpleActionsTableRegion(self.driver, self.conf,
                                               self.KEY_PAIRS_TABLE_NAME,
                                               self.KEY_PAIRS_TABLE_ACTIONS,
                                               self.KEY_PAIRS_TABLE_ROW_ACTION)

    @property
    def create_keypair_form(self):
        return forms.FormRegion(self.driver, self.conf, None,
                                self.CREATE_KEY_PAIR_FORM_FIELDS)

    @property
    def delete_keypair_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def is_keypair_present(self, name):
        return bool(self._get_row_with_keypair_name(name))

    def create_keypair(self, keypair_name):
        self.keypairs_table.create.click()
        self.create_keypair_form.name.text = keypair_name
        self.create_keypair_form.submit.click()
        self.wait_till_popups_disappear()

    def delete_keypair(self, name):
        self._get_row_with_keypair_name(name).delete.click()
        self.delete_keypair_form.submit.click()
        self.wait_till_popups_disappear()
