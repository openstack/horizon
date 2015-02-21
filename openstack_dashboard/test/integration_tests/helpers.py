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
import time
import uuid

import testtools
import xvfbwrapper

from openstack_dashboard.test.integration_tests import config
from openstack_dashboard.test.integration_tests.pages import loginpage
from openstack_dashboard.test.integration_tests import webdriver


def gen_random_resource_name(resource="", timestamp=True):
    """Generate random resource name using uuid and timestamp.

    Input fields are usually limited to 255 or 80 characters hence their
    provide enough space for quite long resource names, but it might be
    the case that maximum field length is quite restricted, it is then
    necessary to consider using shorter resource argument or avoid using
    timestamp by setting timestamp argument to False.
    """
    fields = ["horizon"]
    if resource:
        fields.append(resource)
    if timestamp:
        tstamp = time.strftime("%d-%m-%H-%M-%S")
        fields.append(tstamp)
    fields.append(str(uuid.uuid4()).replace("-", ""))
    return "_".join(fields)


class BaseTestCase(testtools.TestCase):

    def setUp(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            # Start a virtual display server for running the tests headless.
            if os.environ.get('SELENIUM_HEADLESS', False):
                self.vdisplay = xvfbwrapper.Xvfb(width=1280, height=720)
                # workaround for memory leak in Xvfb taken from: http://blog.
                # jeffterrace.com/2012/07/xvfb-memory-leak-workaround.html
                self.vdisplay.xvfb_cmd.append("-noreset")
                # disables X access control
                self.vdisplay.xvfb_cmd.append("-ac")
                self.vdisplay.start()
            # Start the Selenium webdriver and setup configuration.
            self.driver = webdriver.WebDriverWrapper()
            self.driver.maximize_window()
            self.conf = config.get_config()
            self.driver.implicitly_wait(self.conf.selenium.implicit_wait)
            self.driver.set_page_load_timeout(self.conf.selenium.page_timeout)
        else:
            msg = "The INTEGRATION_TESTS env variable is not set."
            raise self.skipException(msg)
        super(BaseTestCase, self).setUp()

    def tearDown(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            self.driver.quit()
        if hasattr(self, 'vdisplay'):
            self.vdisplay.stop()
        super(BaseTestCase, self).tearDown()


class TestCase(BaseTestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.login_pg = loginpage.LoginPage(self.driver, self.conf)
        self.login_pg.go_to_login_page()
        self.home_pg = self.login_pg.login()

    def tearDown(self):
        try:
            if self.home_pg.is_logged_in:
                self.home_pg.go_to_home_page()
                self.home_pg.log_out()
        finally:
            super(TestCase, self).tearDown()


class AdminTestCase(BaseTestCase):
    def setUp(self):
        super(AdminTestCase, self).setUp()
        self.login_pg = loginpage.LoginPage(self.driver, self.conf)
        self.login_pg.go_to_login_page()
        self.home_pg = self.login_pg.login(
            user=self.conf.identity.admin_username,
            password=self.conf.identity.admin_password)

    def tearDown(self):
        try:
            if self.home_pg.is_logged_in:
                self.home_pg.log_out()
        finally:
            super(AdminTestCase, self).tearDown()
