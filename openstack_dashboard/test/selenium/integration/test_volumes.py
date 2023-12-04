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

import time

from oslo_utils import uuidutils
import pytest

from openstack_dashboard.test.selenium import widgets


@pytest.fixture(params=[1])
def volume_name(request):
    count = request.param
    vol_name_list = ['horizon_vol_%s' % uuidutils.generate_uuid(dashed=False)]
    if count > 1:
        vol_name_list = [f"{vol_name_list[0]}-{item}"
                         for item in range(1, count + 1)]
    return vol_name_list


@pytest.fixture
def new_volume_demo(volume_name, openstack_demo, config):

    for vol in volume_name:
        volume = openstack_demo.create_volume(
            name=vol,
            image=config.image.images_list[0],
            size=1,
            wait=True,
        )
    yield volume
    for vol in volume_name:
        openstack_demo.delete_volume(
            name_or_id=vol,
            wait=True,
        )


@pytest.fixture
def new_volume_admin(volume_name, openstack_admin, config):

    for vol in volume_name:
        volume = openstack_admin.create_volume(
            name=vol,
            image=config.image.images_list[0],
            size=1,
            wait=True,
        )
    yield volume
    for vol in volume_name:
        openstack_admin.delete_volume(
            name_or_id=vol,
            wait=True,
        )


@pytest.fixture
def clear_volume_demo(volume_name, openstack_demo):
    yield None
    wait_for_steady_state_of_volume(openstack_demo, volume_name[0])
    openstack_demo.delete_volume(
        volume_name[0],
        wait=True,
    )


@pytest.fixture
def clear_volume_admin(volume_name, openstack_admin):
    yield None
    wait_for_steady_state_of_volume(openstack_admin, volume_name[0])
    openstack_admin.delete_volume(
        volume_name[0],
        wait=True,
    )


def wait_for_steady_state_of_volume(openstack, volume_name):
    for attempt in range(10):
        if (openstack.block_storage.find_volume(volume_name).status in
            ["available", "error", "error_restoring", "error_extending",
             "error_managing"]):
            break
        else:
            time.sleep(3)


def wait_for_volume_is_deleted(openstack, volume_name):
    for attempt in range(10):
        if openstack.block_storage.find_volume(volume_name) is None:
            break
        else:
            time.sleep(3)


def test_create_empty_volume_demo(login, driver, volume_name, openstack_demo,
                                  clear_volume_demo, config):
    volume_name = volume_name[0]
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
    assert openstack_demo.block_storage.find_volume(volume_name) is not None


def test_create_volume_from_image_demo(login, driver, volume_name, config,
                                       clear_volume_demo, openstack_demo):
    image_source_name = config.launch_instances.image_name
    volume_name = volume_name[0]
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
    widgets.select_from_specific_dropdown_in_form(
        volume_form, 'id_volume_source_type', 'Image')
    widgets.select_from_specific_dropdown_in_form(
        volume_form, 'id_image_source', image_source_name)
    volume_form.find_element_by_css_selector(
        ".btn-primary[value='Create Volume']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Info: Creating volume "{volume_name}"' in messages
    assert openstack_demo.block_storage.find_volume(volume_name) is not None


def test_delete_volume_demo(login, driver, volume_name, openstack_demo,
                            new_volume_demo, config):
    volume_name = volume_name[0]
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
    wait_for_volume_is_deleted(openstack_demo, volume_name)
    assert (openstack_demo.block_storage.find_volume(volume_name) is None)


def test_edit_volume_description_demo(login, driver, volume_name, config,
                                      openstack_demo, new_volume_demo):
    volume_name = volume_name[0]
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
    rows[0].find_element_by_css_selector(".data-table-action").click()
    volume_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_form.find_element_by_id("id_description").clear()
    volume_form.find_element_by_id("id_description").send_keys(
        f"EDITED_Description for: {volume_name}")
    volume_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Info: Updating volume "{volume_name}"' in messages
    assert(openstack_demo.block_storage.find_volume(
           volume_name).description == f"EDITED_Description for: {volume_name}")


@pytest.mark.parametrize('volume_name', [3], indirect=True)
def test_volumes_pagination_demo(login, driver, volume_name,
                                 change_page_size_demo,
                                 new_volume_demo, config):
    """This test checks volumes pagination for demo

            Steps:
            1) Login to Horizon Dashboard as demo user
            2) create 3 Volumes
            3) Navigate to user settings page
            4) Change 'Items Per Page' value to 1
            5) Go to Project -> Volumes page
            6) Check that only 'Next' link is available, only one volume is
            available (and it has correct name) on the first page
            7) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one volume is available (and it has correct name)
            8) Click 'Next' and check that only 'Prev' link is available,
            only one volume is visible (and it has correct name) on page 3
            9) Click 'Prev' and check result (should be the same as for step7)
            10) Click 'Prev' and check result (should be the same as for step6)
            11) Go to user settings page and restore 'Items Per Page'
            12) Delete created volumes
            """
    items_per_page = 1
    first_page_definition = widgets.TableDefinition(next=True, prev=False,
                                                    count=items_per_page,
                                                    names=[volume_name[2]])
    second_page_definition = widgets.TableDefinition(next=True, prev=True,
                                                     count=items_per_page,
                                                     names=[volume_name[1]])
    third_page_definition = widgets.TableDefinition(next=False, prev=True,
                                                    count=items_per_page,
                                                    names=[volume_name[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes'
    ))
    driver.get(url)
    actual_page1_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert first_page_definition == actual_page1_definition
    # Turning to next page(page2)
    driver.find_element_by_link_text("Next »").click()
    actual_page2_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert second_page_definition == actual_page2_definition
    # Turning to next page(page3)
    driver.find_element_by_link_text("Next »").click()
    actual_page3_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert third_page_definition == actual_page3_definition
    # Turning back to previous page(page2)
    driver.find_element_by_link_text("« Prev").click()
    actual_page2_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert second_page_definition == actual_page2_definition
    # Turning back to previous page(page1)
    driver.find_element_by_link_text("« Prev").click()
    actual_page1_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert first_page_definition == actual_page1_definition


# Admin tests


def test_create_empty_volume_admin(login, driver, volume_name, openstack_admin,
                                   clear_volume_admin, config):
    volume_name = volume_name[0]
    login('admin')
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
    assert openstack_admin.block_storage.find_volume(volume_name) is not None


def test_create_volume_from_image_admin(login, driver, volume_name, config,
                                        clear_volume_admin, openstack_admin):
    image_source_name = config.launch_instances.image_name
    volume_name = volume_name[0]
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Volume").click()
    volume_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_form.find_element_by_id("id_name").send_keys(volume_name)
    widgets.select_from_specific_dropdown_in_form(
        volume_form, 'id_volume_source_type', 'Image')
    widgets.select_from_specific_dropdown_in_form(
        volume_form, 'id_image_source', image_source_name)
    volume_form.find_element_by_css_selector(
        ".btn-primary[value='Create Volume']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Info: Creating volume "{volume_name}"' in messages
    assert openstack_admin.block_storage.find_volume(volume_name) is not None


def test_delete_volume_admin(login, driver, volume_name, openstack_admin,
                             new_volume_admin, config):
    volume_name = volume_name[0]
    login('admin')
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
    wait_for_volume_is_deleted(openstack_admin, volume_name)
    assert (openstack_admin.block_storage.find_volume(volume_name) is None)


def test_edit_volume_description_admin(login, driver, volume_name, config,
                                       openstack_admin, new_volume_admin):
    volume_name = volume_name[0]
    login('admin')
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
    rows[0].find_element_by_css_selector(".data-table-action").click()
    volume_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_form.find_element_by_id("id_description").clear()
    volume_form.find_element_by_id("id_description").send_keys(
        f"EDITED_Description for: {volume_name}")
    volume_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Info: Updating volume "{volume_name}"' in messages
    assert(openstack_admin.block_storage.find_volume(
           volume_name).description == f"EDITED_Description for: {volume_name}")


@pytest.mark.parametrize('volume_name', [3], indirect=True)
def test_volumes_pagination_admin(login, driver, volume_name,
                                  change_page_size_admin,
                                  new_volume_admin, config):
    """This test checks volumes pagination for demo

            Steps:
            1) Login to Horizon Dashboard as admin user
            2) create 3 Volumes
            3) Navigate to user settings page
            4) Change 'Items Per Page' value to 1
            5) Go to Project -> Volumes page
            6) Check that only 'Next' link is available, only one volume is
            available (and it has correct name) on the first page
            7) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one volume is available (and it has correct name)
            8) Click 'Next' and check that only 'Prev' link is available,
            only one volume is visible (and it has correct name) on page 3
            9) Click 'Prev' and check result (should be the same as for step7)
            10) Click 'Prev' and check result (should be the same as for step6)
            11) Go to user settings page and restore 'Items Per Page'
            12) Delete created volumes
            """
    items_per_page = 1
    first_page_definition = widgets.TableDefinition(next=True, prev=False,
                                                    count=items_per_page,
                                                    names=[volume_name[2]])
    second_page_definition = widgets.TableDefinition(next=True, prev=True,
                                                     count=items_per_page,
                                                     names=[volume_name[1]])
    third_page_definition = widgets.TableDefinition(next=False, prev=True,
                                                    count=items_per_page,
                                                    names=[volume_name[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes'
    ))
    driver.get(url)
    actual_page1_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert first_page_definition == actual_page1_definition
    # Turning to next page(page2)
    driver.find_element_by_link_text("Next »").click()
    actual_page2_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert second_page_definition == actual_page2_definition
    # Turning to next page(page3)
    driver.find_element_by_link_text("Next »").click()
    actual_page3_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert third_page_definition == actual_page3_definition
    # Turning back to previous page(page2)
    driver.find_element_by_link_text("« Prev").click()
    actual_page2_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert second_page_definition == actual_page2_definition
    # Turning back to previous page(page1)
    driver.find_element_by_link_text("« Prev").click()
    actual_page1_definition = widgets.get_table_definition(driver,
                                                           sorting=True)
    assert first_page_definition == actual_page1_definition
