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

import openstack as openstack_sdk
import pytest

from openstack_dashboard.test.selenium import widgets


def create_conn(username, password, project, domain, auth_url):
    if not domain:
        domain = 'default'
    conn = openstack_sdk.connection.Connection(
        auth={
            "auth_url": auth_url,
            "user_domain_id": domain,
            "project_domain_id": domain,
            "project_name": project,
            "username": username,
            "password": password,
        },
        compute_api_version='2',
        verify=False,
    )
    conn.authorize()
    return conn


@pytest.fixture(scope='session')
def openstack_admin(config):
    conn = create_conn(
        config.identity.admin_username,
        config.identity.admin_password,
        config.identity.admin_home_project,
        config.identity.domain,
        config.dashboard.auth_url,
    )
    yield conn
    conn.close()


@pytest.fixture(scope='session')
def openstack_demo(config):
    conn = create_conn(
        config.identity.username,
        config.identity.password,
        config.identity.home_project,
        config.identity.domain,
        config.dashboard.auth_url,
    )
    yield conn
    conn.close()


@pytest.fixture()
def change_page_size_admin(login, config, driver):
    default_page_size = 20
    new_page_size = 1
    def change_size(page_size):

        login('admin')
        url = '/'.join((
            config.dashboard.dashboard_url,
            'settings',
        ))
        driver.get(url)
        element = driver.find_element_by_xpath(
            ".//input[@id='id_pagesize']")
        element.clear()
        element.send_keys(page_size)
        driver.find_element_by_xpath(".//input[@value='Save']").click()

    change_size(new_page_size)
    yield
    change_size(default_page_size)


@pytest.fixture()
def change_page_size_demo(login, config, driver):
    default_page_size = 20
    new_page_size = 1
    def change_size(page_size):

        login('user')
        url = '/'.join((
            config.dashboard.dashboard_url,
            'settings',
        ))
        driver.get(url)
        element = driver.find_element_by_xpath(
            ".//input[@id='id_pagesize']")
        element.clear()
        element.send_keys(page_size)
        driver.find_element_by_xpath(".//input[@value='Save']").click()

    change_size(new_page_size)
    yield
    change_size(default_page_size)


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, widgets.TableDefinition) and \
            isinstance(right, widgets.TableDefinition) and op == "==":
        return [
            "Comparing TableDefinition instances:",
            "   vals: {} != {}".format(left, right),
        ]


# Create default test network (contains subnet and is connected to public
#                              network via router)

@pytest.fixture(scope='session')
def new_default_test_network(openstack_admin):
    network = openstack_admin.network.create_network(
        name="default_test_network",
        is_shared=True,
    )
    yield network
    openstack_admin.network.delete_network(network)


@pytest.fixture(scope='session')
def new_default_test_subnet(new_default_test_network, openstack_admin):
    subnet_name = "default_test_subnet"
    subnet = openstack_admin.network.create_subnet(
        name=subnet_name,
        network_id=new_default_test_network.id,
        ip_version=4,
        cidr="10.10.0.0/16",
    )
    yield subnet
    openstack_admin.delete_subnet(subnet)


@pytest.fixture(scope='session')
def new_default_test_router(openstack_admin):
    public_network = openstack_admin.network.find_network('public')
    public_subnet = openstack_admin.network.find_subnet('public-subnet')
    router = openstack_admin.network.post("/routers", json={
        "router": {
            "name": "default_test_router",
            "external_gateway_info": {
                "network_id": public_network.id,
                "enable_snat": True,
                "external_fixed_ips": [{
                    "subnet_id": public_subnet.id
                }]
            },
            "admin_state_up": True
        }
    }).json()
    yield router
    openstack_admin.network.delete_router(router['router']['id'])


@pytest.fixture(scope='session')
def new_default_test_interface_for_router(new_default_test_router,
                                          new_default_test_subnet,
                                          openstack_admin):
    interface = openstack_admin.network.add_interface_to_router(
        router=new_default_test_router['router']['id'],
        subnet_id=new_default_test_subnet.id,
    )
    yield interface
    openstack_admin.network.remove_interface_from_router(
        router=new_default_test_router['router']['id'],
        subnet_id=new_default_test_subnet.id)


@pytest.fixture(scope='session')
def complete_default_test_network(new_default_test_network,
                                  new_default_test_subnet,
                                  new_default_test_router,
                                  new_default_test_interface_for_router):
    yield new_default_test_network
