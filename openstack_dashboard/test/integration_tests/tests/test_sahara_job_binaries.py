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

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.pages.project.data_processing\
    import jobbinariespage
from openstack_dashboard.test.integration_tests.tests import decorators


JOB_BINARY_INTERNAL = {
    # Size of binary name is limited to 50 characters
    jobbinariespage.JobbinariesPage.BINARY_NAME:
        helpers.gen_random_resource_name(resource='jobbinary',
                                         timestamp=False)[0:50],
    jobbinariespage.JobbinariesPage.BINARY_STORAGE_TYPE:
        "Internal database",
    jobbinariespage.JobbinariesPage.BINARY_URL: None,
    jobbinariespage.JobbinariesPage.INTERNAL_BINARY:
        "*Create a script",
    jobbinariespage.JobbinariesPage.BINARY_PATH: None,
    jobbinariespage.JobbinariesPage.SCRIPT_NAME:
        helpers.gen_random_resource_name(resource='scriptname',
                                         timestamp=False),
    jobbinariespage.JobbinariesPage.SCRIPT_TEXT: "test_script_text",
    jobbinariespage.JobbinariesPage.USERNAME: None,
    jobbinariespage.JobbinariesPage.PASSWORD: None,
    jobbinariespage.JobbinariesPage.DESCRIPTION: "test description"
}


@decorators.services_required("sahara")
class TestSaharaJobBinary(helpers.TestCase):

    def _sahara_create_delete_job_binary(self, job_binary_template):
        job_name = \
            job_binary_template[jobbinariespage.JobbinariesPage.BINARY_NAME]

        # create job binary
        job_binary_pg = self.home_pg.go_to_dataprocessing_jobbinariespage()
        self.assertFalse(job_binary_pg.is_job_binary_present(job_name),
                         "Job binary was present in the binaries table"
                         " before its creation.")
        job_binary_pg.create_job_binary(**job_binary_template)

        # verify that job is created without problems
        self.assertFalse(job_binary_pg.is_error_message_present(),
                         "Error message occurred during binary job creation.")
        self.assertTrue(job_binary_pg.is_job_binary_present(job_name),
                        "Job binary is not in the binaries job table after"
                        " its creation.")

        # delete binary job
        job_binary_pg.delete_job_binary(job_name)

        # verify that job was successfully deleted
        self.assertFalse(job_binary_pg.is_error_message_present(),
                         "Error message occurred during binary job deletion.")
        self.assertFalse(job_binary_pg.is_job_binary_present(job_name),
                         "Job binary was not removed from binaries job table.")

    def test_sahara_create_delete_job_binary_internaldb(self):
        """Test the creation of a Job Binary in the Internal DB."""
        self._sahara_create_delete_job_binary(JOB_BINARY_INTERNAL)
