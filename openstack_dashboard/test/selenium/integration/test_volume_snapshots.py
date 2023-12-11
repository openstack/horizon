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


@pytest.fixture
def volume_from_snapshot_name():
    return 'horizon_volume_from_snapshot_%s' % uuidutils.generate_uuid(
        dashed=False)


@pytest.fixture
def new_volume_from_snapshot_demo(new_volume_demo, new_volume_snapshot_demo,
                                  openstack_demo, volume_from_snapshot_name):

    volume_from_snapshot = openstack_demo.create_volume(
        name=volume_from_snapshot_name,
        snapshot_id=new_volume_snapshot_demo.id,
        size=1,
        wait=True,
    )
    yield volume_from_snapshot
    openstack_demo.delete_volume(
        name_or_id=volume_from_snapshot_name,
        wait=True,
    )


@pytest.fixture
def clear_volume_from_snapshot(volume_from_snapshot_name, openstack_demo):
    yield None
    test_volumes.wait_for_steady_state_of_volume(
        openstack_demo, volume_from_snapshot_name)
    openstack_demo.delete_volume(
        volume_from_snapshot_name,
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


def test_edit_volume_snapshot_description_demo(login, driver, openstack_demo,
                                               new_volume_snapshot_demo,
                                               config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_snapshots tr[data-display"
        f"='{new_volume_snapshot_demo.name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Edit Snapshot")
    snapshot_form = driver.find_element_by_css_selector(".modal-dialog form")
    snapshot_form.find_element_by_id("id_description").clear()
    snapshot_form.find_element_by_id("id_description").send_keys(
        f"EDITED_Description for: {new_volume_snapshot_demo.name}")
    snapshot_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Info: Updating volume snapshot '
           f'"{new_volume_snapshot_demo.name}"' in messages)
    assert(openstack_demo.block_storage.find_snapshot(
        new_volume_snapshot_demo.name).description ==
        f"EDITED_Description for: {new_volume_snapshot_demo.name}")


def test_create_volume_from_volume_snapshot_demo(login, driver, openstack_demo,
                                                 new_volume_snapshot_demo,
                                                 volume_from_snapshot_name,
                                                 clear_volume_from_snapshot,
                                                 config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_snapshots tr[data-display"
        f"='{new_volume_snapshot_demo.name}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    volume_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_form.find_element_by_id("id_name").clear()
    volume_form.find_element_by_id("id_name").send_keys(
        volume_from_snapshot_name)
    volume_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Info: Creating volume "{volume_from_snapshot_name}"' in messages)
    assert(openstack_demo.block_storage.find_volume(
        volume_from_snapshot_name) is not None)


def test_delete_volume_from_volume_snapshot_demo(login, driver, openstack_demo,
                                                 new_volume_from_snapshot_demo,
                                                 config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volumes tr[data-display="
        f"'{new_volume_from_snapshot_demo.name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Volume")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Info: Scheduled deletion of Volume: "
           f"{new_volume_from_snapshot_demo.name}" in messages)
    test_volumes.wait_for_volume_is_deleted(
        openstack_demo, new_volume_from_snapshot_demo.name)
    assert (openstack_demo.block_storage.find_volume(
        new_volume_from_snapshot_demo.name)is None)


def test_delete_snapshot_before_volume_demo(login, driver, openstack_demo,
                                            new_volume_from_snapshot_demo,
                                            volume_snapshot_names,
                                            config):
    if not config.volume.allow_delete_snapshot_before_volume:
        pytest.skip("Delete snapshot before volume not allowed")

    volume_snapshot_name = volume_snapshot_names[0]

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots',
    ))
    driver.get(url)
    rows_snapshots = driver.find_elements_by_css_selector(
        f"table#volume_snapshots tr[data-display='{volume_snapshot_name}']")
    assert len(rows_snapshots) == 1
    actions_column_snapshot = rows_snapshots[0].find_element_by_css_selector(
        "td.actions_column")
    widgets.select_from_dropdown(actions_column_snapshot,
                                 "Delete Volume Snapshot")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Scheduled deletion of Volume Snapshot: "
           f"{volume_snapshot_name}" in messages)
    wait_for_volume_snapshot_is_deleted(openstack_demo, volume_snapshot_name)
    assert (openstack_demo.block_storage.find_snapshot(volume_snapshot_name)
            is None)
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(url)
    rows_volumes = driver.find_elements_by_css_selector(
        f"table#volumes tr[data-display='"
        f"{new_volume_from_snapshot_demo.name}']")
    assert len(rows_volumes) == 1
    actions_column_volume = rows_volumes[0].find_element_by_css_selector(
        "td.actions_column")
    widgets.select_from_dropdown(actions_column_volume, "Delete Volume")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Info: Scheduled deletion of Volume: "
           f"{new_volume_from_snapshot_demo.name}" in messages)
    test_volumes.wait_for_volume_is_deleted(
        openstack_demo, new_volume_from_snapshot_demo.name)
    assert (openstack_demo.block_storage.find_volume(
        new_volume_from_snapshot_demo.name) is None)


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


def test_create_volume_snapshot_admin(login, driver, new_volume_admin,
                                      volume_snapshot_names, config,
                                      clear_volume_snapshot_admin,
                                      openstack_admin):
    volume_snapshot_name = volume_snapshot_names[0]

    login('admin')
    volumes_url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'volumes',
    ))
    driver.get(volumes_url)
    row = driver.find_element_by_css_selector(
        f"table#volumes tr[data-display='{new_volume_admin.name}']")
    actions_column = row.find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Create Snapshot")
    snapshot_form = driver.find_element_by_css_selector(
        ".modal-dialog form")
    snapshot_form.find_element_by_id("id_name").send_keys(
        volume_snapshot_name)
    snapshot_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Info: Creating volume snapshot "{volume_snapshot_name}".'
           in messages)
    assert (openstack_admin.block_storage.find_snapshot(volume_snapshot_name)
            is not None)


def test_delete_volume_snapshot_admin(login, driver, openstack_admin,
                                      new_volume_snapshot_admin, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_snapshots tr[data-display="
        f"'{new_volume_snapshot_admin.name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Volume Snapshot")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Scheduled deletion of Volume Snapshot: "
           f"{new_volume_snapshot_admin.name}" in messages)
    wait_for_volume_snapshot_is_deleted(openstack_admin,
                                        new_volume_snapshot_admin.name)
    assert (openstack_admin.block_storage.find_snapshot(
            new_volume_snapshot_admin.name)is None)


def test_edit_volume_snapshot_description_admin(login, driver, openstack_admin,
                                                new_volume_snapshot_admin,
                                                config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'snapshots',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_snapshots tr[data-display"
        f"='{new_volume_snapshot_admin.name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Edit Snapshot")
    snapshot_form = driver.find_element_by_css_selector(".modal-dialog form")
    snapshot_form.find_element_by_id("id_description").clear()
    snapshot_form.find_element_by_id("id_description").send_keys(
        f"EDITED_Description for: {new_volume_snapshot_admin.name}")
    snapshot_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Info: Updating volume snapshot '
           f'"{new_volume_snapshot_admin.name}"' in messages)
    assert(openstack_admin.block_storage.find_snapshot(
        new_volume_snapshot_admin.name).description ==
        f"EDITED_Description for: {new_volume_snapshot_admin.name}")


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
