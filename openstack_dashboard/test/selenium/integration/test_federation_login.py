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

import pytest
from selenium.common.exceptions import NoSuchElementException

from openstack_dashboard.test.selenium.conftest import Session


@pytest.fixture(scope='session')
def login_oidc(driver, config):
    session = Session(driver, config)
    return session.login_oidc


def test_federation_keystone_user_login(login, driver, config):
    login('user')
    try:
        driver.find_element_by_xpath(
            config.theme.user_name_xpath)
        assert True
    except NoSuchElementException:
        assert False


def test_federation_keystone_admin_login(login, driver, config):
    login('admin')
    try:
        driver.find_element_by_xpath(
            config.theme.user_name_xpath)
        assert True
    except NoSuchElementException:
        assert False


def test_federation_keycloak_test_user_login(login_oidc, driver, config):
    login_oidc('user')
    project = config.OIDC.keycloak_test_user_home_project
    username = config.OIDC.keycloak_test_user1_username
    # Check that expected project exists
    try:
        project_element = driver.find_element_by_xpath(
            config.theme.project_name_xpath)
        project_element.find_element_by_xpath(
            f'.//*[normalize-space()="{project}"]')
    except NoSuchElementException:
        assert False, f"Project name '{project}' isn't found"
    # Check that expected username exists
    try:
        username_element = driver.find_element_by_xpath(
            config.theme.user_name_xpath)
        username_element.find_element_by_xpath(
            f'.//*[normalize-space()="{username}"]')
    except NoSuchElementException:
        assert False, f"Username '{username}' isn't found"
