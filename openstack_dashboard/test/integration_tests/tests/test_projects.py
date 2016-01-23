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
from openstack_dashboard.test.integration_tests.regions import messages


PROJECT_NAME = helpers.gen_random_resource_name("project")


class TestCreateDeleteProject(helpers.AdminTestCase):

    def setUp(self):
        super(TestCreateDeleteProject, self).setUp()
        self.projects_page = self.home_pg.go_to_identity_projectspage()

    def test_create_delete_project(self):
        self.projects_page.create_project(PROJECT_NAME)
        self.assertTrue(
            self.projects_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.projects_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(self.projects_page.is_project_present(PROJECT_NAME))

        self.projects_page.delete_project(PROJECT_NAME)
        self.assertTrue(
            self.projects_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.projects_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(self.projects_page.is_project_present(PROJECT_NAME))
