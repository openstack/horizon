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

from openstack_dashboard.test.integration_tests import decorators
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


@decorators.skip_because(bugs=['1777359'])
class TestModifyProject(helpers.AdminTestCase):

    def setUp(self):
        super(TestModifyProject, self).setUp()
        self.projects_page = self.home_pg.go_to_identity_projectspage()
        self.projects_page.create_project(PROJECT_NAME)
        self.assertTrue(
            self.projects_page.find_message_and_dismiss(messages.SUCCESS))

        def cleanup():
            if not self.projects_page.is_the_current_page():
                self.home_pg.go_to_identity_projectspage()
            self.projects_page.delete_project(PROJECT_NAME)

        self.addCleanup(cleanup)

    @decorators.skip_because(bugs=['1774697'])
    def test_add_member(self):
        admin_name = self.CONFIG.identity.admin_username
        regular_role_name = self.CONFIG.identity.default_keystone_role
        admin_role_name = self.CONFIG.identity.default_keystone_admin_role
        roles2add = {regular_role_name, admin_role_name}

        self.projects_page.allocate_user_to_project(
            admin_name, roles2add, PROJECT_NAME)
        self.assertTrue(
            self.projects_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.projects_page.find_message_and_dismiss(messages.ERROR))

        user_roles = self.projects_page.get_user_roles_at_project(
            admin_name, PROJECT_NAME)
        self.assertEqual(roles2add, user_roles,
                         "The requested roles haven't been set for the user!")
