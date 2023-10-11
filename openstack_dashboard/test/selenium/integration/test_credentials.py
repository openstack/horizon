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
import re
import shutil

import pytest

from selenium.webdriver.support.wait import WebDriverWait

from horizon.test import firefox_binary
from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def download_dir(driver):
    directory = firefox_binary.WebDriver.TEMPDIR
    yield directory
    shutil.rmtree(directory)


def test_download_rc_file_admin(login, driver, config, openstack_admin,
                                download_dir):

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'api_access',
    ))
    driver.get(url)
    openstack_file_dropdown = driver.find_element_by_class_name(
        "table_actions_menu")
    widgets.select_from_dropdown(openstack_file_dropdown, "OpenStack RC File")
    WebDriverWait(driver, config.selenium.page_timeout).until(
        lambda x: ((len(os.listdir(download_dir)) == 1) and
                   ("admin-openrc.sh" in os.listdir(download_dir))))
    with open(os.path.join(download_dir, "admin-openrc.sh")) as rc_file:
        content = rc_file.read()
    username = re.search(
        r'export OS_USERNAME="([^"]+)"', content).group(1)
    project_name = re.search(
        r'export OS_PROJECT_NAME="([^"]+)"', content).group(1)
    project_id = re.search(
        r'export OS_PROJECT_ID=(.+)', content).group(1)

    assert(config.identity.admin_username == username and
           config.identity.admin_home_project == project_name and
           openstack_admin.identity.find_project(
               config.identity.admin_home_project).id == project_id)


def test_download_rc_file_demo(login, driver, config, openstack_admin,
                               download_dir):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'api_access',
    ))
    driver.get(url)
    openstack_file_dropdown = driver.find_element_by_class_name(
        "table_actions_menu")
    widgets.select_from_dropdown(openstack_file_dropdown, "OpenStack RC File")
    WebDriverWait(driver, config.selenium.page_timeout).until(
        lambda x: ((len(os.listdir(download_dir)) == 1) and
                   ("demo-openrc.sh" in os.listdir(download_dir))))
    with open(os.path.join(download_dir, "demo-openrc.sh")) as rc_file:
        content = rc_file.read()
    username = re.search(
        r'export OS_USERNAME="([^"]+)"', content).group(1)
    project_name = re.search(
        r'export OS_PROJECT_NAME="([^"]+)"', content).group(1)
    project_id = re.search(
        r'export OS_PROJECT_ID=(.+)', content).group(1)

    assert(config.identity.username == username and
           config.identity.home_project == project_name and
           openstack_admin.identity.find_project(
               config.identity.home_project).id == project_id)
