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

from os import listdir
from os.path import join
from os import remove

from horizon.test import firefox_binary
from openstack_dashboard.test.integration_tests import helpers


class TestDownloadRCFile(helpers.AdminTestCase):

    _directory = firefox_binary.WebDriver.TEMPDIR
    _openrc_template = "-openrc.sh"

    def setUp(self):
        super(TestDownloadRCFile, self).setUp()
        username = self.TEST_USER_NAME
        tenant_name = self.HOME_PROJECT
        projects_page = self.home_pg.go_to_identity_projectspage()
        tenant_id = projects_page.get_project_id_from_row(tenant_name)
        self.actual_dict = {'OS_USERNAME': username,
                            'OS_TENANT_NAME': tenant_name,
                            'OS_TENANT_ID': tenant_id}

        def cleanup():
            temporary_files = listdir(self._directory)
            if len(temporary_files):
                remove(join(self._directory, temporary_files[0]))

        self.addCleanup(cleanup)

    def test_download_rc_v3_file(self):
        """This is a basic scenario test:

        Steps:
        1) Login to Horizon Dashboard as admin user
        2) Navigate to Project > API Access tab
        3) Click on "Download OpenStack RC File" dropdown button
        4) Click on "OpenStack RC File (Identity API v3" button
        5) File named by template "<tenant_name>-openrc.sh" must be downloaded
        6) Check that username, project name and project id correspond to
        current username, tenant name and tenant id
        """
        api_access_page = self.home_pg. \
            go_to_project_apiaccesspage()
        api_access_page.download_openstack_rc_file(
            3, self._directory, self._openrc_template)
        cred_dict = api_access_page.get_credentials_from_file(
            3, self._directory, self._openrc_template)
        self.assertEqual(cred_dict, self.actual_dict)
