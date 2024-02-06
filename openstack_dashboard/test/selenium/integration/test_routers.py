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
import test_networks

from openstack_dashboard.test.selenium import widgets

# Imported fixtures
subnet_name = test_networks.subnet_name
network_name = test_networks.network_name
new_subnet_demo = test_networks.new_subnet_demo
new_network_demo = test_networks.new_network_demo


@pytest.fixture
def router_name():
    return 'horizon_router_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_router_admin(router_name, openstack_admin):
    router = openstack_admin.create_router(
        name=router_name
    )
    yield router
    openstack_admin.delete_router(router_name)


@pytest.fixture
def new_router_demo(router_name, openstack_demo):
    router = openstack_demo.create_router(
        name=router_name
    )
    yield router
    openstack_demo.delete_router(router_name)


@pytest.fixture
def clear_router_admin(router_name, openstack_admin):
    yield None
    openstack_admin.delete_router(router_name)


@pytest.fixture
def clear_router_demo(router_name, openstack_demo):
    yield None
    openstack_demo.delete_router(router_name)


@pytest.fixture
def clear_interface_from_router_demo(new_router_demo, new_subnet_demo,
                                     openstack_demo):
    yield None
    openstack_demo.network.remove_interface_from_router(
        router=new_router_demo.id,
        subnet_id=new_subnet_demo.id,
    )


@pytest.fixture
def new_interface(new_router_demo, new_network_demo, new_subnet_demo,
                  openstack_demo):
    interface = openstack_demo.network.add_interface_to_router(
        router=new_router_demo.id,
        subnet_id=new_subnet_demo.id,
    )
    yield interface


@pytest.fixture
def new_router_with_gateway(new_router_demo, openstack_demo, openstack_admin):
    network_id = openstack_admin.network.find_network('public').id
    subnet_id = openstack_admin.network.find_subnet('public-subnet').id
    ip_address = openstack_admin.network.find_subnet(
        'public-subnet').allocation_pools[0]['end']

    openstack_demo.network.put(
        f"/routers/{new_router_demo.id}/add_external_gateways",
        json={
            "router": {
                "external_gateways": [{
                    "enable_snat": False,
                    "external_fixed_ips": [{
                        "ip_address": f"{ip_address}",
                        "subnet_id": f"{subnet_id}"
                    }],
                    "network_id": f"{network_id}"
                }]
            }
        }
    ).json()
    yield new_router_demo


def test_create_router_demo(login, driver, router_name, openstack_demo,
                            config, clear_router_demo):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'routers',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Router").click()
    router_form = driver.find_element_by_css_selector(".modal-dialog form")
    router_form.find_element_by_id("id_name").send_keys(router_name)
    widgets.select_from_dropdown(router_form, "public")
    router_form.find_element_by_css_selector(
        ".btn-primary[value='Create Router']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Router {router_name} was successfully created.'
           in messages)
    assert openstack_demo.network.find_router(router_name) is not None


def test_delete_router_demo(login, driver, router_name, openstack_demo,
                            new_router_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'routers',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#routers tr[data-display='{router_name}']"
    )
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Router")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Router: {router_name}" in messages
    assert openstack_demo.network.find_router(router_name) is None


def test_router_add_interface_demo(login, driver, router_name, openstack_demo,
                                   new_router_demo, new_network_demo,
                                   clear_interface_from_router_demo,
                                   new_subnet_demo, config):
    fixed_ip_test = "10.11.1.33"

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'routers',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#routers tr[data-display='{router_name}']"
    )
    assert len(rows) == 1
    rows[0].find_element_by_link_text(router_name).click()
    driver.find_element_by_link_text("Interfaces").click()
    driver.find_element_by_id("interfaces__action_create").click()
    add_interface_form = driver.find_element_by_css_selector(
        ".modal-dialog form")
    widgets.select_from_dropdown(
        add_interface_form, f"{new_network_demo.name}: {new_subnet_demo.cidr} "
                            f"({new_subnet_demo.name})")
    add_interface_form.find_element_by_id(
        "id_ip_address").send_keys(fixed_ip_test)
    add_interface_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Interface added {fixed_ip_test}" in messages

    is_interface_added_sdk = False
    all_ports = openstack_demo.network.get("/ports").json()['ports']
    for port in all_ports:
        for fixed_ip in port['fixed_ips']:
            if fixed_ip['ip_address'] == fixed_ip_test:
                if port['device_id'] == new_router_demo.id:
                    is_interface_added_sdk = True
    assert is_interface_added_sdk


def test_router_delete_interface_demo(login, driver, router_name,
                                      openstack_demo, new_interface, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'routers',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#routers tr[data-display='{router_name}']"
    )
    assert len(rows) == 1
    rows[0].find_element_by_link_text(router_name).click()
    driver.find_element_by_link_text("Interfaces").click()
    port_id = new_interface['port_id']
    extracted_port_name = f"({port_id[:13]})"
    rows = driver.find_elements_by_css_selector(
        f"table#interfaces tr[data-display='{extracted_port_name}']"
    )
    assert len(rows) == 1
    rows[0].find_element_by_css_selector("td.actions_column").click()
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Interface: {extracted_port_name}" in messages
    assert(openstack_demo.network.find_port(
        new_interface['port_id']) is None)


def test_router_set_gateway_demo(login, driver, new_router_demo,
                                 openstack_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'routers',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#routers tr[data-display='{new_router_demo.name}']"
    )
    assert len(rows) == 1
    router_sdk = openstack_demo.network.get(
        f"/routers/{new_router_demo.id}"
        f"?fields=id&fields=name&fields="
        f"external_gateway_info").json()['router']
    assert(router_sdk["external_gateway_info"] is None)
    rows[0].find_element_by_css_selector(".data-table-action").click()
    gateway_form = driver.find_element_by_css_selector(".modal-dialog form")
    widgets.select_from_specific_dropdown_in_form(
        gateway_form, 'id_network_id', 'public')
    gateway_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Gateway interface is added" in messages
    router_sdk = openstack_demo.network.get(
        f"/routers/{new_router_demo.id}"
        f"?fields=id&fields=name&fields="
        f"external_gateway_info").json()['router']
    assert(router_sdk["external_gateway_info"]["network_id"] ==
           openstack_demo.network.find_network('public').id)


def test_router_clear_gateway_demo(login, driver, new_router_with_gateway,
                                   openstack_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'routers',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#routers tr[data-display='{new_router_with_gateway.name}']"
    )
    assert len(rows) == 1
    router_sdk = openstack_demo.network.get(
        f"/routers/{new_router_with_gateway.id}"
        f"?fields=id&fields=name&fields="
        f"external_gateway_info").json()['router']
    assert(router_sdk["external_gateway_info"]["network_id"] ==
           openstack_demo.network.find_network('public').id)
    rows[0].find_element_by_css_selector(".data-table-action").click()
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Cleared Gateway: {new_router_with_gateway.name}" in
           messages)
    router_sdk = openstack_demo.network.get(
        f"/routers/{new_router_with_gateway.id}"
        f"?fields=id&fields=name&fields="
        f"external_gateway_info").json()['router']
    assert(router_sdk["external_gateway_info"] is None)


def test_create_router_admin(login, driver, router_name, openstack_admin,
                             config, clear_router_admin):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'routers',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Router").click()
    router_form = driver.find_element_by_css_selector(".modal-dialog form")
    router_form.find_element_by_id("id_name").send_keys(router_name)
    widgets.select_from_specific_dropdown_in_form(
        router_form, "id_tenant_id", "admin")
    widgets.select_from_specific_dropdown_in_form(
        router_form, "id_external_network", "public")
    router_form.find_element_by_css_selector(
        ".btn-primary[value='Create Router']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Router {router_name} was successfully created.'
           in messages)
    assert openstack_admin.network.find_router(router_name) is not None


def test_delete_router_admin(login, driver, router_name, openstack_admin,
                             new_router_admin, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'routers',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#routers tr[data-display='{router_name}']"
    )
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Router")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Router: {router_name}" in messages
    assert openstack_admin.network.find_router(router_name) is None
