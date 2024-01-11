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

import os
import signal
import socket
import subprocess
from threading import Thread
import time

import pytest
import xvfbwrapper

from horizon.test import webdriver
from openstack_dashboard.test.integration_tests import config as horizon_config


STASH_FAILED = pytest.StashKey[bool]()


class Session:
    def __init__(self, driver, config):
        self.current_user = None
        self.current_project = None
        self.driver = driver
        self.credentials = {
            'user': (
                config.identity.username,
                config.identity.password,
                config.identity.home_project,
            ),
            'admin': (
                config.identity.admin_username,
                config.identity.admin_password,
                config.identity.admin_home_project,
            ),
        }
        self.logout_url = '/'.join((
            config.dashboard.dashboard_url,
            'auth',
            'logout',
        ))

    def login(self, user, project=None):
        if project is None:
            project = self.credentials[user][2]
        if self.current_user != user:
            username, password, home_project = self.credentials[user]
            self.driver.get(self.logout_url)
            user_field = self.driver.find_element_by_id('id_username')
            user_field.send_keys(username)
            pass_field = self.driver.find_element_by_id('id_password')
            pass_field.send_keys(password)
            button = self.driver.find_element_by_css_selector(
                'div.panel-footer button.btn')
            button.click()
            self.current_user = user
            self.current_project = self.driver.find_element_by_class_name(
                'context-project').text
        if self.current_project != project:
            dropdown_project = self.driver.find_element_by_xpath(
                '//*[@class="context-project"]//ancestor::ul')
            dropdown_project.click()
            selection = dropdown_project.find_element_by_xpath(
                f'.//*[normalize-space()="{project}"]')
            selection.click()
            self.current_project = self.driver.find_element_by_class_name(
                'context-project').text


@pytest.fixture(scope='session')
def login(driver, config):
    session = Session(driver, config)
    return session.login


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """A hook to save the failure state of a test."""
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    item.stash[STASH_FAILED] = item.stash.get(STASH_FAILED, False) or rep.failed


@pytest.fixture(scope='function', autouse=True)
def save_screenshot(request, report_dir, driver):
    yield None
    if not request.node.stash.get(STASH_FAILED, False):
        return
    screen_path = os.path.join(report_dir, 'screenshot.png')
    driver.get_screenshot_as_file(screen_path)


@pytest.fixture(scope='function', autouse=True)
def save_page_source(request, report_dir, driver):
    yield None
    if not request.node.stash.get(STASH_FAILED, False):
        return
    source_path = os.path.join(report_dir, 'page.html')
    html_elem = driver.find_element_by_tag_name("html")
    page_source = html_elem.get_property("innerHTML")
    with open(source_path, 'w') as f:
        f.write(page_source)


@pytest.fixture(scope='function', autouse=True)
def record_video(request, report_dir, xdisplay):
    if not os.environ.get('FFMPEG_INSTALLED', False):
        yield None
        return
    filepath = os.path.join(report_dir, 'video.mp4')
    frame_rate = 15
    display, width, height = xdisplay
    command = [
        'ffmpeg',
        '-video_size', f'{width}x{height}',
        '-framerate', str(frame_rate),
        '-f', 'x11grab',
        '-i', f':{display}',
        filepath,
    ]
    fnull = open(os.devnull, 'w')
    popen = subprocess.Popen(command, stdout=fnull, stderr=fnull)
    yield None
    popen.send_signal(signal.SIGINT)

    def terminate_process():
        limit = time.time() + 10
        while time.time() < limit:
            time.sleep(0.1)
            if popen.poll() is not None:
                return
        os.kill(popen.pid, signal.SIGTERM)

    thread = Thread(target=terminate_process)
    thread.start()
    popen.communicate()
    thread.join()
    if not request.node.stash.get(STASH_FAILED, False):
        try:
            os.remove(filepath)
        except OSError:
            pass


@pytest.fixture(scope='session')
def xdisplay():
    IS_SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', False)
    if IS_SELENIUM_HEADLESS:
        width, height = 1920, 1080
        vdisplay = xvfbwrapper.Xvfb(width=width, height=height)
        args = []

        # workaround for memory leak in Xvfb taken from:
        # http://blog.jeffterrace.com/2012/07/xvfb-memory-leak-workaround.html
        args.append("-noreset")

        # disables X access control
        args.append("-ac")

        if hasattr(vdisplay, 'extra_xvfb_args'):
            # xvfbwrapper 0.2.8 or newer
            vdisplay.extra_xvfb_args.extend(args)
        else:
            vdisplay.xvfb_cmd.extend(args)
        vdisplay.start()
        display = vdisplay.new_display
    else:
        width, height = subprocess.check_output(
            'xdpyinfo | grep "dimensions:"', shell=True
        ).decode().split(':', 1)[1].split()[0].strip().split('x')
        vdisplay = None
        display = subprocess.check_output(
            'xdpyinfo | grep "name of display:"', shell=True
        ).decode().split(':', 1)[1].strip()
    yield display, width, height
    if vdisplay:
        vdisplay.stop()


@pytest.fixture(scope='session')
def config():
    return horizon_config.get_config()


@pytest.fixture(scope='function')
def report_dir(request, config):
    root_path = os.path.dirname(os.path.abspath(horizon_config.__file__))
    test_name = request.node.nodeid.rsplit('/', 1)[1]
    report_dir = os.path.join(
        root_path, config.selenium.screenshots_directory, test_name)
    if not os.path.isdir(report_dir):
        os.makedirs(report_dir)
    yield report_dir
    try:
        os.rmdir(report_dir)  # delete if empty
    except OSError:
        pass


@pytest.fixture(scope='session')
def driver(config, xdisplay):
    # Start a virtual display server for running the tests headless.
    IS_SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', False)
    # Increase the default Python socket timeout from nothing
    # to something that will cope with slow webdriver startup times.
    # This *just* affects the communication between this test process
    # and the webdriver.
    socket.setdefaulttimeout(60)
    # Start the Selenium webdriver and setup configuration.
    desired_capabilities = dict(webdriver.desired_capabilities)
    desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}
    driver = webdriver.WebDriver(
        desired_capabilities=desired_capabilities
    )
    if config.selenium.maximize_browser:
        driver.maximize_window()
        if IS_SELENIUM_HEADLESS:  # force full screen in xvfb
            display, width, height = xdisplay
            driver.set_window_size(width, height)

    driver.implicitly_wait(config.selenium.implicit_wait)
    driver.set_page_load_timeout(config.selenium.page_timeout)
    yield driver
    driver.quit()
