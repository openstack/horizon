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

import os

import selenium
from selenium.webdriver.support import ui
import testtools
import xvfbwrapper

from openstack_dashboard.test.integration_tests import config
from openstack_dashboard.test.integration_tests.pages import loginpage


class BaseTestCase(testtools.TestCase):

    def setUp(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            # Start a virtual display server for running the tests headless.
            if os.environ.get('SELENIUM_HEADLESS', False):
                self.vdisplay = xvfbwrapper.Xvfb(width=1280, height=720)
                self.vdisplay.start()
            # Start the Selenium webdriver and setup configuration.
            self.driver = selenium.webdriver.Firefox()
            self.driver.maximize_window()
            self.conf = config.get_config()
            self.driver.implicitly_wait(self.conf.dashboard.page_timeout)
        else:
            msg = "The INTEGRATION_TESTS env variable is not set."
            raise self.skipException(msg)
        super(BaseTestCase, self).setUp()

    def tearDown(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            self.driver.close()
        if hasattr(self, 'vdisplay'):
            self.vdisplay.stop()
        super(BaseTestCase, self).tearDown()

    def wait_for_title(self):
        timeout = self.conf.dashboard.page_timeout
        ui.WebDriverWait(self.driver, timeout).until(lambda d:
                                                     self.driver.title)


class TestCase(BaseTestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.login_pg = loginpage.LoginPage(self.driver, self.conf)
        self.login_pg.go_to_login_page()
        self.home_pg = self.login_pg.login()

    def tearDown(self):
        self.home_pg.go_to_home_page()
        self.home_pg.log_out()
        super(TestCase, self).tearDown()
