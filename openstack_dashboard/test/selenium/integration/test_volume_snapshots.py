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
import test_volumes

from openstack_dashboard.test.selenium import widgets

# Imported fixtures
volume_name = test_volumes.volume_name
new_volume_demo = test_volumes.new_volume_demo


@pytest.fixture
def volume_snapshot_name():
    return 'horizon_volume_snapshot_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_volume_snapshot_demo(new_volume_demo, volume_snapshot_name,
                             openstack_demo):
    volume_snapshot = openstack_demo.create_volume_snapshot(
        volume_id=new_volume_demo.id,
        name=volume_snapshot_name,
        wait=True,
    )
    yield volume_snapshot
    openstack_demo.delete_volume_snapshot(volume_snapshot_name)


@pytest.fixture
def clear_volume_snapshot_demo(volume_snapshot_name, openstack_demo):
    yield None
    openstack_demo.delete_volume_snapshot(
        name_or_id=volume_snapshot_name,
        wait=True,
    )


def test_create_volume_snapshot_demo(login, driver, volume_name,
                                     new_volume_demo, volume_snapshot_name,
                                     config, clear_volume_snapshot_demo,
                                     openstack_demo):

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


def test_delete_volume_snapshot_demo(login, driver, volume_snapshot_name,
                                     new_volume_snapshot_demo, config,
                                     openstack_demo):
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
    assert (openstack_demo.block_storage.find_snapshot(volume_snapshot_name)
            is None)
