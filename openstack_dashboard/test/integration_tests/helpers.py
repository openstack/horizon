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

import os

import selenium
from selenium.webdriver.support import ui
import testtools

from openstack_dashboard.test.integration_tests import config


class BaseTestCase(testtools.TestCase):

    def setUp(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            self.driver = selenium.webdriver.Firefox()
            self.conf = config.get_config()
        else:
            msg = "The INTEGRATION_TESTS env variable is not set."
            raise self.skipException(msg)
        super(BaseTestCase, self).setUp()

    def tearDown(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            self.driver.close()
        super(BaseTestCase, self).tearDown()

    def wait_for_title(self):
        timeout = self.conf.dashboard.page_timeout
        ui.WebDriverWait(self.driver, timeout).until(lambda d:
                                                     self.driver.title)
