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
