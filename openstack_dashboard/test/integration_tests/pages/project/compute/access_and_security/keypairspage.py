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


class KeypairsTable(tables.TableRegion):
    name = "keypairs"
    CREATE_KEY_PAIR_FORM_FIELDS = ('name',)

    @tables.bind_table_action('create')
    def create_keypair(self, create_button):
        create_button.click()
        return forms.FormRegion(self.driver, self.conf, None,
                                self.CREATE_KEY_PAIR_FORM_FIELDS)

    @tables.bind_row_action('delete', primary=True)
    def delete_keypair(self, delete_button, row):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class KeypairsPage(basepage.BaseNavigationPage):

    KEY_PAIRS_TABLE_ACTIONS = ("create", "import", "delete")
    KEY_PAIRS_TABLE_ROW_ACTION = "delete"
    KEY_PAIRS_TABLE_NAME_COLUMN = 'name'

    def __init__(self, driver, conf):
        super(KeypairsPage, self).__init__(driver, conf)
        self._page_title = "Access & Security"

    def _get_row_with_keypair_name(self, name):
        return self.keypairs_table.get_row(self.KEY_PAIRS_TABLE_NAME_COLUMN,
                                           name)

    @property
    def keypairs_table(self):
        return KeypairsTable(self.driver, self.conf)

    @property
    def delete_keypair_form(self):
        return forms.BaseFormRegion(self.driver, self.conf, None)

    def is_keypair_present(self, name):
        return bool(self._get_row_with_keypair_name(name))

    def create_keypair(self, keypair_name):
        create_keypair_form = self.keypairs_table.create_keypair()
        create_keypair_form.name.text = keypair_name
        create_keypair_form.submit()

    def delete_keypair(self, name):
        row = self._get_row_with_keypair_name(name)
        delete_keypair_form = self.keypairs_table.delete_keypair(row)
        delete_keypair_form.submit()
