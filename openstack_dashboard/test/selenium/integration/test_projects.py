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
def project_name():
    return 'horizon_project_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_project(project_name, openstack_admin):
    project = openstack_admin.create_project(
        name=project_name,
        domain_id="default"
    )
    yield project
    openstack_admin.identity.delete_project(project)


@pytest.fixture
def clear_project(project_name, openstack_admin):
    yield None
    openstack_admin.delete_project(
        openstack_admin.identity.find_project(project_name).id)


@pytest.fixture
def new_project_with_admin(new_project, openstack_admin, config):
    """Provides a project with the admin user as a member."""

    openstack_admin.identity.assign_project_role_to_user(
        project=new_project,
        user=openstack_admin.identity.find_user(
            config.identity.admin_username).id,
        role=openstack_admin.identity.find_role(
            config.identity.default_keystone_role).id
    )
    yield new_project


@pytest.fixture
def new_project_with_group(new_project, openstack_admin, config):
    """Provides a project with the admins group as a member."""

    openstack_admin.identity.assign_project_role_to_group(
        project=new_project,
        group=openstack_admin.identity.find_group('admins').id,
        role=openstack_admin.identity.find_role(
            config.identity.default_keystone_role).id
    )
    yield new_project


def test_create_project(login, driver, project_name, openstack_admin,
                        config, clear_project):

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Project").click()
    project_form = driver.find_element_by_css_selector("form .modal-content")
    project_form.find_element_by_id("id_name").send_keys(project_name)
    project_form.find_element_by_css_selector(
        ".btn-primary[value='Create Project']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created new project "{project_name}".' in messages
    assert openstack_admin.identity.find_project(project_name) is not None


def test_delete_project(login, driver, project_name, openstack_admin,
                        new_project, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#tenants tr[data-display='{project_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Project")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Project: {project_name}" in messages
    assert openstack_admin.identity.find_project(project_name) is None


def test_add_member_to_project(login, driver, project_name, openstack_admin,
                               new_project, config):
    admin_name = config.identity.admin_username
    regular_role_name = config.identity.default_keystone_role

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#tenants tr[data-display='{project_name}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    project_form = driver.find_element_by_css_selector("form .modal-content")
    project_form.find_element_by_xpath(
        f".//*[text()='{admin_name}']//ancestor::li"
        f"/following-sibling::li/a[@href='#add_remove']").click()
    project_form.find_element_by_css_selector(
        ".btn-primary[value='Save']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Modified project "{project_name}".' in messages
    assert(openstack_admin.identity.validate_user_has_project_role(
        project=new_project,
        user=openstack_admin.identity.find_user(admin_name).id,
        role=openstack_admin.identity.find_role(regular_role_name).id,)
    )


def test_add_role_to_project_member(login, driver, openstack_admin, config,
                                    new_project_with_admin):
    admin_name = config.identity.admin_username
    regular_role_name = config.identity.default_keystone_role
    admin_role_name = config.identity.default_keystone_admin_role

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#tenants tr[data-display={new_project_with_admin.name}]")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    project_form = driver.find_element_by_css_selector("form .modal-content")
    select_roles_dropdown = project_form.find_element_by_xpath(
        f".//*[text()='{admin_name}']//ancestor::li"
        f"/following-sibling::li[@class='dropdown role_options']")
    widgets.select_from_dropdown(select_roles_dropdown, admin_role_name)
    project_form.find_element_by_css_selector(
        ".btn-primary[value='Save']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Modified project '
           f'"{new_project_with_admin.name}".' in messages)
    assert(openstack_admin.identity.validate_user_has_project_role(
        project=new_project_with_admin,
        user=openstack_admin.identity.find_user(admin_name).id,
        role=openstack_admin.identity.find_role(regular_role_name).id,) and
        openstack_admin.identity.validate_user_has_project_role(
        project=new_project_with_admin,
        user=openstack_admin.identity.find_user(admin_name).id,
        role=openstack_admin.identity.find_role(admin_role_name).id,)
    )


def test_add_group_to_project(login, driver, openstack_admin,
                              new_project, config):
    group_name = 'admins'
    regular_role_name = config.identity.default_keystone_role

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#tenants tr[data-display='{new_project.name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Modify Groups")
    project_form = driver.find_element_by_css_selector("form .modal-content")
    project_form.find_element_by_xpath(
        f".//*[text()='{group_name}']//ancestor::li"
        f"/following-sibling::li/a[@href='#add_remove']").click()
    project_form.find_element_by_css_selector(
        ".btn-primary[value='Save']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Modified project "{new_project.name}".' in messages
    assert(openstack_admin.identity.validate_group_has_project_role(
        project=new_project,
        group=openstack_admin.identity.find_group(group_name).id,
        role=openstack_admin.identity.find_role(regular_role_name).id,)
    )


def test_add_role_to_project_group(login, driver, openstack_admin, config,
                                   new_project_with_group):
    group_name = 'admins'
    regular_role_name = config.identity.default_keystone_role
    admin_role_name = config.identity.default_keystone_admin_role

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#tenants tr[data-display='{new_project_with_group.name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Modify Groups")
    project_form = driver.find_element_by_css_selector("form .modal-content")
    select_roles_dropdown = project_form.find_element_by_xpath(
        f".//*[text()='{group_name}']//ancestor::li"
        f"/following-sibling::li[@class='dropdown role_options']")
    widgets.select_from_dropdown(select_roles_dropdown, admin_role_name)
    project_form.find_element_by_css_selector(
        ".btn-primary[value='Save']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Modified project '
           f'"{new_project_with_group.name}".' in messages)
    assert(openstack_admin.identity.validate_group_has_project_role(
        project=new_project_with_group,
        group=openstack_admin.identity.find_group(group_name).id,
        role=openstack_admin.identity.find_role(regular_role_name).id,) and
        openstack_admin.identity.validate_group_has_project_role(
        project=new_project_with_group,
        group=openstack_admin.identity.find_group(group_name).id,
        role=openstack_admin.identity.find_role(admin_role_name).id,)
    )
