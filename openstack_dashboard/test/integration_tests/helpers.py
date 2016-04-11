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

import contextlib
import datetime
import os
import socket
import tempfile
import time
import traceback
import uuid

from selenium.webdriver.common import action_chains
from selenium.webdriver.common import by
from selenium.webdriver.common import keys
import testtools
import xvfbwrapper

from horizon.test import webdriver
from openstack_dashboard.test.integration_tests import config
from openstack_dashboard.test.integration_tests.pages import loginpage
from openstack_dashboard.test.integration_tests.regions import messages

ROOT_PATH = os.path.dirname(os.path.abspath(config.__file__))


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


@contextlib.contextmanager
def gen_temporary_file(name='', suffix='.qcow2', size=10485760):
    """Generate temporary file with provided parameters.

    :param name: file name except the extension /suffix
    :param suffix: file extension/suffix
    :param size: size of the file to create, bytes are generated randomly
    :return: path to the generated file
    """
    with tempfile.NamedTemporaryFile(prefix=name, suffix=suffix) as tmp_file:
        tmp_file.write(os.urandom(size))
        yield tmp_file.name


class BaseTestCase(testtools.TestCase):

    CONFIG = config.get_config()

    def setUp(self):
        if not os.environ.get('INTEGRATION_TESTS', False):
            msg = "The INTEGRATION_TESTS env variable is not set."
            raise self.skipException(msg)

        # Start a virtual display server for running the tests headless.
        if os.environ.get('SELENIUM_HEADLESS', False):
            self.vdisplay = xvfbwrapper.Xvfb(width=1920, height=1080)
            args = []

            # workaround for memory leak in Xvfb taken from:
            # http://blog.jeffterrace.com/2012/07/xvfb-memory-leak-workaround.html
            args.append("-noreset")

            # disables X access control
            args.append("-ac")

            if hasattr(self.vdisplay, 'extra_xvfb_args'):
                # xvfbwrapper 0.2.8 or newer
                self.vdisplay.extra_xvfb_args.extend(args)
            else:
                self.vdisplay.xvfb_cmd.extend(args)
            self.vdisplay.start()
        # Increase the default Python socket timeout from nothing
        # to something that will cope with slow webdriver startup times.
        # This *just* affects the communication between this test process
        # and the webdriver.
        socket.setdefaulttimeout(60)
        # Start the Selenium webdriver and setup configuration.
        desired_capabilities = dict(webdriver.desired_capabilities)
        desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}
        self.driver = webdriver.WebDriverWrapper(
            desired_capabilities=desired_capabilities
        )
        if self.CONFIG.selenium.maximize_browser:
            self.driver.maximize_window()
        self.driver.implicitly_wait(self.CONFIG.selenium.implicit_wait)
        self.driver.set_page_load_timeout(
            self.CONFIG.selenium.page_timeout)
        self.addOnException(self._dump_page_html_source)
        self.addOnException(self._dump_browser_log)
        self.addOnException(self._save_screenshot)

        super(BaseTestCase, self).setUp()

    @contextlib.contextmanager
    def exceptions_captured(self, label):
        contents = []
        try:
            yield contents
        except Exception:
            exc_traceback = traceback.format_exc()
            contents.append(testtools.content.text_content(exc_traceback))
        finally:
            self.addDetail(label, contents[0])

    @staticmethod
    def _unwrap_browser_log(_log):
        def rec(log):
            if isinstance(log, dict):
                return log['message'].encode('utf-8')
            elif isinstance(log, list):
                return '\n'.join([rec(item) for item in log])
            else:
                return log.encode('utf-8')
        return rec(_log)

    def _dump_browser_log(self, exc_info):
        with self.exceptions_captured("BrowserLog.text") as contents:
            log = self.driver.get_log('browser')
            contents.append(testtools.content.Content(
                testtools.content_type.UTF8_TEXT,
                lambda: self._unwrap_browser_log(log)))

    def _dump_page_html_source(self, exc_info):
        with self.exceptions_captured("PageHTMLSource.html") as contents:
            pg_source = self._get_page_html_source()
            contents.append(testtools.content.Content(
                testtools.content_type.ContentType('text', 'html'),
                lambda: pg_source))

    def zoom_out(self, times=3):
        """Zooming out prevents different elements being driven out of xvfb
        viewport (which in Selenium>=2.50.1 prevents interaction with them.
        """
        html = self.driver.find_element(by.By.TAG_NAME, 'html')
        html.send_keys(keys.Keys.NULL)
        zoom_out_keys = (keys.Keys.SUBTRACT,) * times
        action_chains.ActionChains(self.driver).key_down(
            keys.Keys.CONTROL).send_keys(*zoom_out_keys).key_up(
            keys.Keys.CONTROL).perform()

    def _save_screenshot(self, exc_info):
        with self.exceptions_captured("Screenshot") as contents:
            filename = self._get_screenshot_filename()
            self.driver.get_screenshot_as_file(filename)
            contents.append(testtools.content.text_content(filename))

    def _get_screenshot_filename(self):
        screenshot_dir = os.path.join(
            ROOT_PATH,
            self.CONFIG.selenium.screenshots_directory)
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        date_string = datetime.datetime.now().strftime(
            '%Y.%m.%d-%H%M%S')
        test_name = self._testMethodName
        name = '%s_%s.png' % (test_name, date_string)
        return os.path.join(screenshot_dir, name)

    def _get_page_html_source(self):
        """Gets html page source.

        self.driver.page_source is not used on purpose because it does not
        display html code generated/changed by javascript.
        """
        html_elem = self.driver.find_element_by_tag_name("html")
        return html_elem.get_attribute("innerHTML").encode("UTF-8")

    def tearDown(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            self.driver.quit()
        if hasattr(self, 'vdisplay'):
            self.vdisplay.stop()
        super(BaseTestCase, self).tearDown()


class TestCase(BaseTestCase):

    TEST_USER_NAME = BaseTestCase.CONFIG.identity.username
    TEST_PASSWORD = BaseTestCase.CONFIG.identity.password
    HOME_PROJECT = BaseTestCase.CONFIG.identity.home_project

    def setUp(self):
        super(TestCase, self).setUp()
        self.login_pg = loginpage.LoginPage(self.driver, self.CONFIG)
        self.login_pg.go_to_login_page()
        self.zoom_out()
        self.home_pg = self.login_pg.login(self.TEST_USER_NAME,
                                           self.TEST_PASSWORD)
        self.home_pg.change_project(self.HOME_PROJECT)
        self.assertTrue(
            self.home_pg.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.home_pg.find_message_and_dismiss(messages.ERROR))

    def tearDown(self):
        try:
            if self.home_pg.is_logged_in:
                self.home_pg.go_to_home_page()
                self.home_pg.log_out()
        finally:
            super(TestCase, self).tearDown()


class AdminTestCase(TestCase):

    TEST_USER_NAME = TestCase.CONFIG.identity.admin_username
    TEST_PASSWORD = TestCase.CONFIG.identity.admin_password
    HOME_PROJECT = BaseTestCase.CONFIG.identity.admin_home_project
