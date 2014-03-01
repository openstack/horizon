# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import selenium.webdriver.common.keys as keys

from openstack_dashboard.test.integration_tests import helpers


class TestLoginPage(helpers.BaseTestCase):
    """This is a basic scenario test:
    * checks that the login page is available
    * logs in as a regular user
    * checks that the user home page loads without error

    FIXME(jpichon): This test will be rewritten using the Page Objects
    pattern, which is much more maintainable.

    """

    def test_login(self):
        self.driver.get(self.conf.dashboard.login_url)
        self.assertIn("Login", self.driver.title)

        username = self.driver.find_element_by_name("username")
        password = self.driver.find_element_by_name("password")

        username.send_keys(self.conf.identity.username)
        password.send_keys(self.conf.identity.password)
        username.send_keys(keys.Keys.RETURN)

        self.wait_for_title()
        self.assertIn("Instance Overview", self.driver.title)
