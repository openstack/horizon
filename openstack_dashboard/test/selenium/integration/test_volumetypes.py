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
def new_volume_type_with_encryption(new_volume_type, openstack_admin):
    openstack_admin.block_storage.create_type_encryption(
        volume_type=new_volume_type,
        control_location="front-end",
        provider="plain",
    )
    yield new_volume_type


@pytest.fixture
def qos_spec_name():
    return 'horizon_qos_spec_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_qos_spec(qos_spec_name, openstack_admin):
    qos_spec = openstack_admin.block_storage.post(
        "/qos-specs",
        json={
            "qos_specs": {
                "name": qos_spec_name,
                "consumer": "back-end",
            }
        }
    ).json()
    yield qos_spec['qos_specs']
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


@pytest.fixture
def new_qos_spec_with_extra_specs(new_qos_spec, openstack_admin):
    openstack_admin.block_storage.put(
        f"/qos-specs/{new_qos_spec['id']}",
        json={
            "qos_specs": {
                "maxIOPS": "5000"
            }
        }
    ).json()
    yield new_qos_spec


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


def test_volume_type_create_encryption(login, driver, openstack_admin, config,
                                       new_volume_type):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_types tr[data-display='{new_volume_type.name}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    volume_type_form = driver.find_element_by_css_selector(".modal-dialog form")
    volume_type_form.find_element_by_id("id_provider").send_keys("plain")
    volume_type_form.find_element_by_css_selector(
        ".btn-primary[value='Create Volume Type Encryption']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Successfully created encryption for "
           f"volume type: {new_volume_type.name}" in messages)
    assert(openstack_admin.block_storage.get_type_encryption(
        new_volume_type.id).provider == 'plain')


def test_volume_type_delete_encryption(login, driver, openstack_admin, config,
                                       new_volume_type_with_encryption):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#volume_types tr[data-display="
        f"'{new_volume_type_with_encryption.name}']")
    assert len(rows) == 1
    assert(openstack_admin.block_storage.get_type_encryption(
        new_volume_type_with_encryption.id).provider == 'plain')
    rows[0].find_element_by_css_selector(".data-table-action")
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Encryption")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Deleted Encryption: "
           f"{new_volume_type_with_encryption.name}" in messages)
    assert(openstack_admin.block_storage.get_type_encryption(
        new_volume_type_with_encryption.id).provider is None)


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


def test_edit_qos_spec_consumer(login, driver, openstack_admin, config,
                                new_qos_spec):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#qos_specs tr[data-display='{new_qos_spec['name']}']")
    assert len(rows) == 1
    assert(openstack_admin.block_storage.get(
        f"/qos-specs/{new_qos_spec['id']}").json()['qos_specs']['consumer'] ==
        'back-end')
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Edit Consumer")
    volume_qos_form = driver.find_element_by_css_selector(".modal-dialog form")
    widgets.select_from_dropdown(volume_qos_form, 'front-end')
    volume_qos_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Successfully modified QoS Spec consumer." in messages
    assert(openstack_admin.block_storage.get(
        f"/qos-specs/{new_qos_spec['id']}").json()['qos_specs']['consumer'] ==
        'front-end')


def test_qos_spec_create_extra_specs(login, driver, openstack_admin, config,
                                     new_qos_spec):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#qos_specs tr[data-display='{new_qos_spec['name']}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    driver.find_element_by_id("specs__action_create").click()
    extra_specs_form = driver.find_element_by_css_selector(
        ".modal-dialog form[id='extra_spec_create_form']")
    extra_specs_form.find_element_by_id("id_key").send_keys('minIOPS')
    extra_specs_form.find_element_by_id("id_value").send_keys(20)
    extra_specs_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created spec "minIOPS".' in messages
    assert(openstack_admin.block_storage.get(
        f"/qos-specs/{new_qos_spec['id']}").json()['qos_specs']['specs'] ==
        {'minIOPS': '20'})


def test_qos_spec_delete_extra_specs(login, driver, openstack_admin, config,
                                     new_qos_spec_with_extra_specs):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'volume_types'
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f'table#qos_specs tr[data-display="'
        f'{new_qos_spec_with_extra_specs["name"]}"]')
    assert len(rows) == 1
    assert(openstack_admin.block_storage.get(
        f"/qos-specs/{new_qos_spec_with_extra_specs['id']}").json()
        ['qos_specs']['specs'] == {'maxIOPS': '5000'})
    rows[0].find_element_by_css_selector(".data-table-action").click()
    volume_qos_form = driver.find_element_by_css_selector(".modal-dialog form")
    rows_extra = volume_qos_form.find_elements_by_css_selector(
        f"table#specs tr[data-display='maxIOPS']")
    assert len(rows_extra) == 1
    actions_column = rows_extra[0].find_element_by_css_selector(
        "td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Spec")
    driver.find_element_by_css_selector(
        ".modal-dialog .modal-footer .btn-danger").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Spec: maxIOPS" in messages
    assert(openstack_admin.block_storage.get(
        f"/qos-specs/{new_qos_spec_with_extra_specs['id']}").json()
        ['qos_specs']['specs'] == {})
