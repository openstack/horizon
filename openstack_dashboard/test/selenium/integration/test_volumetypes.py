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
def volume_type_name():
    return 'horizon_volume_type_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_volume_type(volume_type_name, openstack_admin):
    volume_type = openstack_admin.block_storage.create_type(
        name=volume_type_name
    )
    yield volume_type
    openstack_admin.block_storage.delete_type(volume_type)


@pytest.fixture
def clear_volume_type(volume_type_name, openstack_admin):
    yield None
    openstack_admin.block_storage.delete_type(
        openstack_admin.block_storage.find_type(volume_type_name))


@pytest.fixture
def qos_spec_name():
    return 'horizon_qos_spec_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_qos_spec(qos_spec_name, openstack_admin):
    qos_spec = openstack_admin.block_storage.post(
        "/qos-specs", json={"qos_specs": {"name": qos_spec_name}}).json()
    yield qos_spec
    openstack_admin.block_storage.delete(
        f"/qos-specs/{qos_spec['qos_specs']['id']}")


@pytest.fixture
def clear_qos_spec(qos_spec_name, openstack_admin):
    yield None
    qos_specs = openstack_admin.block_storage.get(
        "/qos-specs").json()['qos_specs']
    qos_spec_id = None
    for spec in qos_specs:
        if spec['name'] == qos_spec_name:
            qos_spec_id = spec['id']
            break
    openstack_admin.block_storage.delete(f"/qos-specs/{qos_spec_id}")


def test_create_volume_type(login, driver, volume_type_name, openstack_admin,
                            config, clear_volume_type):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Volume Type").click()
    volume_type_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_type_form.find_element_by_id("id_name").send_keys(volume_type_name)
    volume_type_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Successfully created volume '
           f'type: {volume_type_name}' in messages)
    assert openstack_admin.block_storage.find_type(volume_type_name) is not None


def test_delete_volume_type(login, driver, volume_type_name, openstack_admin,
                            config, new_volume_type):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_types tr[data-display='{volume_type_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Volume Type")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Volume Type: {volume_type_name}" in messages
    assert openstack_admin.block_storage.find_type(volume_type_name) is None


def test_create_qos_spec(login, driver, qos_spec_name, openstack_admin,
                         config, clear_qos_spec):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create QoS Spec").click()
    volume_qos_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_qos_form.find_element_by_id("id_name").send_keys(qos_spec_name)
    volume_qos_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Successfully created QoS '
           f'Spec: {qos_spec_name}' in messages)
    qos_specs = openstack_admin.block_storage.get(
        "/qos-specs").json()['qos_specs']
    assert(len([spec for spec in qos_specs if qos_spec_name ==
               spec['name']]) > 0)


def test_delete_qos_spec(login, driver, qos_spec_name, openstack_admin,
                         config, new_qos_spec):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#qos_specs tr[data-display='{qos_spec_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete QoS Spec")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted QoS Spec: {qos_spec_name}" in messages
    qos_specs = openstack_admin.block_storage.get(
        "/qos-specs").json()['qos_specs']
    assert(len([spec for spec in qos_specs if qos_spec_name ==
               spec['name']]) == 0)
