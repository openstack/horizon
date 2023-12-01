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
def network_name():
    return 'horizon_network_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def subnet_name():
    return 'horizon_subnet_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_network_demo(network_name, openstack_demo):
    network = openstack_demo.create_network(
        name=network_name,
    )
    yield network
    openstack_demo.delete_network(network_name)


@pytest.fixture
def clear_network_demo(network_name, openstack_demo):
    yield None
    openstack_demo.delete_network(
        network_name,
    )


@pytest.fixture
def new_network_admin(network_name, openstack_admin):
    network = openstack_admin.create_network(
        name=network_name,
    )
    yield network
    openstack_admin.delete_network(network_name)


@pytest.fixture
def clear_network_admin(network_name, openstack_admin):
    yield None
    openstack_admin.delete_network(
        network_name,
    )


# required_state: True/False (marked/unmarked)
def ensure_checkbox(required_state, element):
    current_state = element.is_selected()
    if required_state != current_state:
        element.find_element_by_xpath(
            f".//following-sibling::label").click()


def test_create_network_without_subnet_demo(login, openstack_demo, driver,
                                            network_name, config,
                                            clear_network_demo):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'networks',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Network").click()
    network_form = driver.find_element_by_css_selector("form .modal-content")
    network_form.find_element_by_id("id_net_name").send_keys(network_name)
    checkbox_element = network_form.find_element_by_id("id_with_subnet")
    ensure_checkbox(False, checkbox_element)
    network_form.find_element_by_css_selector(
        ".btn-primary.button-final").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created network "{network_name}".' in messages
    assert openstack_demo.network.find_network(network_name) is not None


def test_create_network_with_subnet_demo(login, driver, openstack_demo,
                                         network_name, config, subnet_name,
                                         clear_network_demo):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'networks',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Network").click()
    network_form = driver.find_element_by_css_selector("form .modal-content")
    network_form.find_element_by_id("id_net_name").send_keys(network_name)
    network_form.find_element_by_css_selector(
        ".btn-primary.button-next").click()
    network_form.find_element_by_id("id_subnet_name").send_keys(subnet_name)
    network_form.find_element_by_id(
        "id_cidr").send_keys(config.network.network_cidr)
    network_form.find_element_by_css_selector(
        ".btn-primary.button-next").click()
    network_form.find_element_by_css_selector(
        ".btn-primary.button-final").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created network "{network_name}".' in messages
    specified_network_sdk = openstack_demo.network.find_network(network_name)
    assert specified_network_sdk is not None
    assert (openstack_demo.network.find_subnet(subnet_name).id in
            specified_network_sdk.subnet_ids)


def test_delete_network_demo(login, driver, network_name, openstack_demo,
                             new_network_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'networks',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#networks tr[data-display='{network_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Network")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Network: {network_name}" in messages
    assert openstack_demo.network.find_network(network_name) is None


def test_create_network_without_subnet_admin(login, openstack_admin, driver,
                                             network_name, config,
                                             clear_network_admin):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'networks',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Network").click()
    network_form = driver.find_element_by_css_selector("form .modal-content")
    network_form.find_element_by_id("id_name").send_keys(network_name)
    checkbox_element = network_form.find_element_by_id("id_with_subnet")
    ensure_checkbox(False, checkbox_element)
    widgets.select_from_specific_dropdown_in_form(
        network_form, 'id_tenant_id', 'admin')
    network_form.find_element_by_css_selector(
        ".btn-primary.button-final").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created network "{network_name}".' in messages
    assert openstack_admin.network.find_network(network_name) is not None


def test_create_network_with_subnet_admin(login, driver, openstack_admin,
                                          network_name, config, subnet_name,
                                          clear_network_admin):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'networks',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Network").click()
    network_form = driver.find_element_by_css_selector("form .modal-content")
    network_form.find_element_by_id("id_name").send_keys(network_name)
    widgets.select_from_specific_dropdown_in_form(
        network_form, 'id_tenant_id', 'admin')
    network_form.find_element_by_css_selector(
        ".btn-primary.button-next").click()
    network_form.find_element_by_id("id_subnet_name").send_keys(subnet_name)
    network_form.find_element_by_id(
        "id_cidr").send_keys(config.network.network_cidr)
    network_form.find_element_by_css_selector(
        ".btn-primary.button-next").click()
    network_form.find_element_by_css_selector(
        ".btn-primary.button-final").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created network "{network_name}".' in messages
    specified_network_sdk = openstack_admin.network.find_network(network_name)
    assert specified_network_sdk is not None
    assert (openstack_admin.network.find_subnet(subnet_name).id in
            specified_network_sdk.subnet_ids)


def test_delete_network_admin(login, driver, network_name, openstack_admin,
                              new_network_admin, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'networks',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#networks tr[data-display='{network_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Network")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Network: {network_name}" in messages
    assert openstack_admin.network.find_network(network_name) is None
