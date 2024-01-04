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

from oslo_utils import uuidutils
import pytest
import test_credentials

from openstack_dashboard.test.selenium import widgets


# Imported fixtures
download_dir = test_credentials.download_dir


@pytest.fixture
def keypair_name():
    return 'horizon_keypair_name_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_keypair_demo(keypair_name, openstack_demo):
    keypair = openstack_demo.create_keypair(keypair_name)
    yield keypair
    openstack_demo.delete_keypair(keypair)


@pytest.fixture
def clear_keypair_demo(keypair_name, openstack_demo):
    yield None
    openstack_demo.delete_keypair(keypair_name)


def test_create_keypair_demo(login, driver, openstack_demo, clear_keypair_demo,
                             config, keypair_name, download_dir):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'key_pairs',
    ))
    driver.get(url)
    driver.find_element_by_xpath(
        "//button[normalize-space()='Create Key Pair']").click()
    keypair_form = driver.find_element_by_css_selector(".modal-content")
    keypair_form.find_element_by_id("name").send_keys(keypair_name)
    type_options = keypair_form.find_element_by_css_selector(
        ".form-control.switchable")
    type_options.click()
    type_options.find_element_by_css_selector('option[label="SSH Key"]').click()
    keypair_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Key pair {keypair_name} was successfully created.'
           in messages)
    assert openstack_demo.compute.find_keypair(keypair_name) is not None


def test_delete_keypair_demo(login, driver, openstack_demo, config,
                             new_keypair_demo):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'key_pairs',
    ))
    driver.get(url)
    rows = driver.find_elements_by_xpath(
        f"//a[text()='{new_keypair_demo.name}']")
    assert len(rows) == 1
    rows[0].find_element_by_xpath(
        ".//ancestor::tr/td[contains(@class,'actions_column')]").click()
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Key Pair: {new_keypair_demo.name}." in messages
    assert openstack_demo.compute.find_keypair(new_keypair_demo.name) is None
