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
def host_aggregate_name():
    return 'horizon_host_aggregate_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_host_aggregate(host_aggregate_name, openstack_admin):
    host_aggregate = openstack_admin.compute.post(
        "/os-aggregates",
        json={
            "aggregate": {
                "name": host_aggregate_name
            }
        }
    ).json()
    yield host_aggregate
    openstack_admin.compute.delete(
        f"/os-aggregates/{host_aggregate['aggregate']['id']}")


@pytest.fixture
def clear_host_aggregate(host_aggregate_name, openstack_admin):
    yield None
    host_aggregates_sdk = openstack_admin.compute.get(
        "/os-aggregates").json()['aggregates']
    host_aggregate_id = None
    for host_aggregate in host_aggregates_sdk:
        if host_aggregate['name'] == host_aggregate_name:
            host_aggregate_id = host_aggregate['id']
            break
    openstack_admin.compute.delete(f"/os-aggregates/{host_aggregate_id}")


def test_create_host_aggregate(login, driver, openstack_admin, config,
                               host_aggregate_name, clear_host_aggregate):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'aggregates',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Host Aggregate").click()
    host_aggregate_form = driver.find_element_by_css_selector(
        "form .modal-content")
    host_aggregate_form.find_element_by_id("id_name").send_keys(
        host_aggregate_name)
    host_aggregate_form.find_element_by_css_selector(
        ".btn-primary[value='Create Host Aggregate']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Created new host aggregate "{host_aggregate_name}".'
           in messages)
    is_host_aggregate_created_sdk = False
    host_aggregates_sdk = openstack_admin.compute.get(
        "/os-aggregates").json()['aggregates']
    for host_aggregate in host_aggregates_sdk:
        if host_aggregate['name'] == host_aggregate_name:
            is_host_aggregate_created_sdk = True
    assert is_host_aggregate_created_sdk


def test_delete_host_aggregate(login, driver, openstack_admin, config,
                               new_host_aggregate):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'aggregates'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#host_aggregates tr[data-display="
        f"'{new_host_aggregate['aggregate']['name']}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Host Aggregate")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Deleted Host Aggregate: "
           f"{new_host_aggregate['aggregate']['name']}" in messages)
    is_host_aggregate_deleted_sdk = True
    host_aggregates_sdk = openstack_admin.compute.get(
        "/os-aggregates").json()['aggregates']
    for host_aggregate in host_aggregates_sdk:
        if host_aggregate['name'] == new_host_aggregate['aggregate']['name']:
            is_host_aggregate_deleted_sdk = False
    assert is_host_aggregate_deleted_sdk
