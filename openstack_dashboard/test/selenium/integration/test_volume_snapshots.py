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
import test_volumes

from openstack_dashboard.test.selenium import widgets

# Imported fixtures
volume_name = test_volumes.volume_name
new_volume_demo = test_volumes.new_volume_demo
new_volume_admin = test_volumes.new_volume_admin


@pytest.fixture(params=[1])
def volume_snapshot_names(request):
    count = request.param
    snapshot_name_list = ['horizon_volume_snapshot_%s' %
                          uuidutils.generate_uuid(dashed=False)]
    if count > 1:
        snapshot_name_list = [f"{snapshot_name_list[0]}-{item}"
                              for item in range(1, count + 1)]
    return snapshot_name_list


@pytest.fixture
def new_volume_snapshot_demo(new_volume_demo, volume_snapshot_names,
                             openstack_demo):

    for volume_snapshot_name in volume_snapshot_names:
        volume_snapshot = openstack_demo.create_volume_snapshot(
            volume_id=new_volume_demo.id,
            name=volume_snapshot_name,
            wait=True,
        )
    yield volume_snapshot
    for volume_snapshot_name in volume_snapshot_names:
        openstack_demo.delete_volume_snapshot(
            name_or_id=volume_snapshot_name,
            wait=True,
        )


@pytest.fixture
def new_volume_snapshot_admin(new_volume_admin, volume_snapshot_names,
                              openstack_admin):

    for volume_snapshot_name in volume_snapshot_names:
        volume_snapshot = openstack_admin.create_volume_snapshot(
            volume_id=new_volume_admin.id,
            name=volume_snapshot_name,
            wait=True,
        )
    yield volume_snapshot
    for volume_snapshot_name in volume_snapshot_names:
        openstack_admin.delete_volume_snapshot(
            name_or_id=volume_snapshot_name,
            wait=True,
        )


@pytest.fixture
def clear_volume_snapshot_demo(volume_snapshot_names, openstack_demo):
    yield None
    wait_for_steady_state_of_volume_snapshot(openstack_demo,
                                             volume_snapshot_names[0])
    openstack_demo.delete_volume_snapshot(
        name_or_id=volume_snapshot_names[0],
        wait=True,
    )


@pytest.fixture
def clear_volume_snapshot_admin(volume_snapshot_names, openstack_admin):
    yield None
    wait_for_steady_state_of_volume_snapshot(openstack_admin,
                                             volume_snapshot_names[0])
    openstack_admin.delete_volume_snapshot(
        name_or_id=volume_snapshot_names[0],
        wait=True,
    )


def wait_for_steady_state_of_volume_snapshot(openstack, volume_snapshot_name):
    for attempt in range(10):
        if (openstack.block_storage.find_snapshot(
            volume_snapshot_name).status in ["available", "error",
                                             "error_deleting"]):
            break
        else:
            time.sleep(3)


def wait_for_volume_snapshot_is_deleted(openstack, volume_snapshot_name):
    for attempt in range(10):
        if (openstack.block_storage.find_snapshot(
                volume_snapshot_name) is None):
            break
        else:
            time.sleep(3)


def test_create_volume_snapshot_demo(login, driver, volume_name,
                                     new_volume_demo, volume_snapshot_names,
                                     config, clear_volume_snapshot_demo,
                                     openstack_demo):
    volume_snapshot_name = volume_snapshot_names[0]
    volume_name = volume_name[0]
    login('user')
    volumes_url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(volumes_url)
    row = driver.find_element_by_css_selector(
        f"table#volumes tr[data-display='{volume_name}']")
    actions_column = row.find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Create Snapshot")
    create_snap_form = driver.find_element_by_css_selector(
        "form[action*='create_snapshot']")
    create_snap_form.find_element_by_id("id_name").send_keys(
        volume_snapshot_name)
    create_snap_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Info: Creating volume snapshot "{volume_snapshot_name}".'
           in messages)
    assert (openstack_demo.block_storage.find_snapshot(volume_snapshot_name)
            is not None)


def test_delete_volume_snapshot_demo(login, driver, volume_snapshot_names,
                                     new_volume_snapshot_demo, config,
                                     openstack_demo):
    volume_snapshot_name = volume_snapshot_names[0]
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_snapshots tr[data-display='{volume_snapshot_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Volume Snapshot")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Scheduled deletion of Volume Snapshot: "
           f"{volume_snapshot_name}" in messages)
    wait_for_volume_snapshot_is_deleted(openstack_demo, volume_snapshot_name)
    assert (openstack_demo.block_storage.find_snapshot(volume_snapshot_name)
            is None)


@pytest.mark.parametrize('volume_snapshot_names', [3], indirect=True)
def test_volume_snapshots_pagination_demo(login, driver, volume_snapshot_names,
                                          new_volume_snapshot_demo,
                                          change_page_size_demo, config):
    """This test checks volumes snapshot pagination for demo

    Steps:
    1) Login to Horizon Dashboard as demo user
    2) Create 1 Volume and 3 snapshot from that volume
    3) Navigate to user settings page
    4) Change 'Items Per Page' value to 1
    5) Go to Project -> Volume -> snapshots page
    6) Check that only 'Next' link is available, only one snapshot is
    available (and it has correct name) on the first page
    7) Click 'Next' and check that both 'Prev' and 'Next' links are
    available, only one snapshot is available (and it has correct name)
    8) Click 'Next' and check that only 'Prev' link is available,
    only one snapshot is visible (and it has correct name) on page 3
    9) Click 'Prev' and check result (should be the same as for step7)
    10) Click 'Prev' and check result (should be the same as for step6)
    11) Go to user settings page and restore 'Items Per Page'
    12) Delete created snapshots and volumes .
    """
    items_per_page = 1
    first_page_definition = widgets.TableDefinition(
        next=True, prev=False,
        count=items_per_page,
        names=[volume_snapshot_names[2]])
    second_page_definition = widgets.TableDefinition(
        next=True, prev=True,
        count=items_per_page,
        names=[volume_snapshot_names[1]])
    third_page_definition = widgets.TableDefinition(
        next=False, prev=True,
        count=items_per_page,
        names=[volume_snapshot_names[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots'
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


@pytest.mark.parametrize('volume_snapshot_names', [3], indirect=True)
def test_volume_snapshots_pagination_admin(login, driver, volume_snapshot_names,
                                           new_volume_snapshot_admin,
                                           change_page_size_admin, config):
    """This test checks volumes snapshot pagination for admin

    Steps:
    1) Login to Horizon Dashboard as admin user
    2) Create 1 Volume and 3 snapshot from that volume
    3) Navigate to user settings page
    4) Change 'Items Per Page' value to 1
    5) Go to Project -> Volume -> snapshots page
    6) Check that only 'Next' link is available, only one snapshot is
    available (and it has correct name) on the first page
    7) Click 'Next' and check that both 'Prev' and 'Next' links are
    available, only one snapshot is available (and it has correct name)
    8) Click 'Next' and check that only 'Prev' link is available,
    only one snapshot is visible (and it has correct name) on page 3
    9) Click 'Prev' and check result (should be the same as for step7)
    10) Click 'Prev' and check result (should be the same as for step6)
    11) Go to user settings page and restore 'Items Per Page'
    12) Delete created snapshots and volumes
    """
    items_per_page = 1
    first_page_definition = widgets.TableDefinition(
        next=True, prev=False,
        count=items_per_page,
        names=[volume_snapshot_names[2]])
    second_page_definition = widgets.TableDefinition(
        next=True, prev=True,
        count=items_per_page,
        names=[volume_snapshot_names[1]])
    third_page_definition = widgets.TableDefinition(
        next=False, prev=True,
        count=items_per_page,
        names=[volume_snapshot_names[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots'
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
