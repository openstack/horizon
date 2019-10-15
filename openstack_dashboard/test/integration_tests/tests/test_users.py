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


class TestUser(helpers.AdminTestCase):

    USER_NAME = helpers.gen_random_resource_name("user")

    def test_create_delete_user(self):
        users_page = self.home_pg.go_to_identity_userspage()
        password = self.TEST_PASSWORD

        users_page.create_user(self.USER_NAME, password=password,
                               project='admin', role='admin')
        self.assertTrue(users_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(users_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(users_page.is_user_present(self.USER_NAME))

        users_page.delete_user(self.USER_NAME)
        self.assertTrue(users_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(users_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(users_page.is_user_present(self.USER_NAME))
