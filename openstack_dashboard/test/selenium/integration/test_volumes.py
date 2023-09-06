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

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def volume_name():
    return 'horizon_volume_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_volume_demo(volume_name, openstack_demo, config):

    volume = openstack_demo.create_volume(
        name=volume_name,
        image=config.image.images_list[0],
        size=1,
        wait=True,
    )
    yield volume
    openstack_demo.delete_volume(volume_name)


@pytest.fixture
def new_volume_admin(volume_name, openstack_admin, config):

    volume = openstack_admin.create_volume(
        name=volume_name,
        image=config.image.images_list[0],
        size=1,
        wait=True,
    )
    yield volume
    openstack_admin.delete_volume(volume_name)


@pytest.fixture
def clear_volume_demo(volume_name, openstack_demo):
    yield None
    openstack_demo. delete_volume(
        volume_name,
        wait=True,
    )


@pytest.fixture
def clear_volume_admin(volume_name, openstack_admin):
    yield None
    openstack_admin. delete_volume(
        volume_name,
        wait=True,
    )


def select_from_dropdown_volume_tab(driver, dropdown_id, label):
    volume_dropdown = driver.find_element_by_xpath(
        f".//*[@for='{dropdown_id}']/following-sibling::div")
    volume_dropdown.click()
    volume_dropdown_tab = volume_dropdown.find_element_by_css_selector(
        "ul.dropdown-menu")
    volume_dropdown_tab.find_element_by_xpath(f".//*[text()='{label}']").click()


def test_create_empty_volume_demo(login, driver, volume_name,
                                  clear_volume_demo, config):

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Volume").click()
    volume_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_form.find_element_by_id("id_name").send_keys(volume_name)
    volume_form.find_element_by_css_selector(
        ".btn-primary[value='Create Volume']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Info: Creating volume "{volume_name}"' in messages
    widgets.find_already_visible_element_by_xpath(
        f"//*[text()='{volume_name}']//ancestor::tr/td"
        f"[normalize-space()='Available']", driver)


def test_create_volume_from_image_demo(login, driver, volume_name,
                                       clear_volume_demo, config):
    image_source_name = config.launch_instances.image_name

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Volume").click()
    volume_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_form.find_element_by_id("id_name").send_keys(volume_name)
    select_from_dropdown_volume_tab(
        volume_form, 'id_volume_source_type', 'Image')
    select_from_dropdown_volume_tab(
        volume_form, 'id_image_source', image_source_name)
    volume_form.find_element_by_css_selector(
        ".btn-primary[value='Create Volume']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Info: Creating volume "{volume_name}"' in messages
    widgets.find_already_visible_element_by_xpath(
        f"//*[text()='{volume_name}']//ancestor::tr/td"
        f"[normalize-space()='Available']", driver)


def test_delete_volume_demo(login, driver, volume_name,
                            new_volume_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volumes tr[data-display='{volume_name}']"
    )
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Volume")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Info: Scheduled deletion of Volume: {volume_name}" in messages
