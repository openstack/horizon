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
import tempfile

import pytest

from oslo_utils import uuidutils

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def image_name():
    return 'horizon_image_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_image_demo(image_name, temporary_file, openstack_demo):
    image = openstack_demo.create_image(
        image_name,
        disk_format="qcow2",
        filename=temporary_file,
        wait=True,
    )
    yield image
    openstack_demo.delete_image(image_name)


@pytest.fixture
def clear_image_demo(image_name, openstack_demo):
    yield None
    openstack_demo.delete_image(
        image_name,
        wait=True,
    )


@pytest.fixture
def temporary_file(tmp_path, name='', suffix='.qcow2', size=5000):
    """Generate temporary file with provided parameters.

    :param name: file name except the extension /suffix
    :param suffix: file extension/suffix
    :param size: size of the file to create, bytes are generated randomly
    :return: path to the generated file
    """
    with tempfile.NamedTemporaryFile(prefix=name, suffix=suffix,
                                     dir=tmp_path) as tmp_file:
        tmp_file.write(os.urandom(size))
        yield tmp_file.name


def test_image_create_from_local_file_demo(login, driver, image_name,
                                           temporary_file, clear_image_demo,
                                           config):
    login('user', 'demo')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'images',
    ))
    driver.get(url)
    driver.find_element_by_xpath(
        "//button[normalize-space()='Create Image']").click()
    wizard = driver.find_element_by_css_selector("wizard")
    wizard.find_element_by_id("imageForm-name").send_keys(image_name)
    select_element = wizard.find_element_by_xpath(
        ".//*[@name='image_file']")
    select_element.send_keys(temporary_file)
    wizard.find_element_by_id("imageForm-format").click()
    wizard.find_element_by_xpath(
        ".//*[@label='QCOW2 - QEMU Emulator']").click()
    wizard.find_element_by_css_selector("button.btn-primary.finish").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Image {image_name} was successfully"
           f" created." in messages)
    widgets.find_already_visible_element_by_xpath(
        f"//*[text()='{image_name}']//ancestor::tr/td"
        f"//*[text()='Active']", driver)


def test_image_delete_demo(login, driver, image_name,
                           new_image_demo, config):
    login('user', 'demo')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'images',
    ))
    driver.get(url)
    rows = driver.find_elements_by_xpath(f"//a[text()='{image_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_xpath(
        ".//ancestor::tr/td[contains(@class,'actions_column')]")
    widgets.select_from_dropdown(actions_column, "Delete Image")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Image: {image_name}." in messages
