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
from openstack_dashboard.test.integration_tests.pages import loginpage


class TestLogin(helpers.BaseTestCase):
    """This is a basic scenario test:
    * checks that the login page is available
    * logs in as a regular user
    * checks that the user home page loads without error
    """
    def test_login(self):
        login_pg = loginpage.LoginPage(self.driver, self.CONFIG)
        login_pg.go_to_login_page()
        home_pg = login_pg.login()
        if not home_pg.is_logged_in:
            self.fail("Could not determine if logged in")
        home_pg.log_out()
