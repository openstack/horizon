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
import copy

from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class JobbinariesPage(basepage.BaseNavigationPage):

    _job_binaries_table_locator = (by.By.CSS_SELECTOR, 'table#job_binaries')
    _create_job_binary_form_locator = (by.By.CSS_SELECTOR, 'div.modal-dialog')
    _confirm_job_binary_deletion_form =\
        (by.By.CSS_SELECTOR, 'div.modal-dialog')

    JOB_BINARIES_TABLE_ACTIONS = ("create_job_binary", "delete_job_binaries")
    JOB_BINARIES_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "delete_job_binary",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS:
            ("download_job_binary",)
    }

    BINARY_NAME = "name"
    BINARY_STORAGE_TYPE = "storage_type"
    BINARY_URL = "url"
    INTERNAL_BINARY = "internal_binary"
    BINARY_PATH = "upload_file"
    SCRIPT_NAME = "script_name"
    SCRIPT_TEXT = "script_text"
    USERNAME = "username"
    PASSWORD = "password"
    DESCRIPTION = "description"

    CREATE_BINARY_FORM_FIELDS = (
        BINARY_NAME,
        BINARY_STORAGE_TYPE,
        BINARY_URL,
        INTERNAL_BINARY,
        BINARY_PATH,
        SCRIPT_NAME,
        SCRIPT_TEXT,
        USERNAME,
        PASSWORD,
        DESCRIPTION
    )

    # index of name column in binary jobs table
    JOB_BINARIES_TABLE_NAME_COLUMN = 0

    # fields that are set via text setter
    _TEXT_FIELDS = (BINARY_NAME, BINARY_STORAGE_TYPE, INTERNAL_BINARY)

    def __init__(self, driver, conf):
        super(JobbinariesPage, self).__init__(driver, conf)
        self._page_title = "Data Processing"

    def _get_row_with_job_binary_name(self, name):
        return self.job_binaries_table.get_row(
            self.JOB_BINARIES_TABLE_NAME_COLUMN, name)

    @property
    def job_binaries_table(self):
        src_elem = self._get_element(*self._job_binaries_table_locator)
        return tables.ComplexActionTableRegion(self.driver,
                                               self.conf, src_elem,
                                               self.JOB_BINARIES_TABLE_ACTIONS,
                                               self.JOB_BINARIES_ROW_ACTIONS
                                               )

    @property
    def create_job_binary_form(self):
        src_elem = self._get_element(*self._create_job_binary_form_locator)
        return forms.FormRegion(self.driver, self.conf, src_elem,
                                self.CREATE_BINARY_FORM_FIELDS)

    @property
    def confirm_delete_job_binaries_form(self):
        src_elem = self._get_element(*self._confirm_job_binary_deletion_form)
        return forms.BaseFormRegion(self.driver, self.conf, src_elem)

    def delete_job_binary(self, name):
        row = self._get_row_with_job_binary_name(name)
        row.mark()
        self.job_binaries_table.delete_job_binaries.click()
        self.confirm_delete_job_binaries_form.submit.click()

    def create_job_binary(self, name, storage_type, url, internal_binary,
                          upload_file, script_name, script_text, username,
                          password, description):
        self.job_binaries_table.create_job_binary.click()
        job_data = copy.copy(locals())
        del job_data["self"]
        self.create_job_binary_form.set_field_values(job_data)
        self.create_job_binary_form.submit.click()

    def is_job_binary_present(self, name):
        return bool(self._get_row_with_job_binary_name(name))
