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

default_password = "12345"


@pytest.fixture
def user_name():
    return 'horizon_user_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_user(user_name, openstack_admin):
    user = openstack_admin.create_user(
        name=user_name,
        password=default_password,
        domain_id="default",
    )
    yield user
    openstack_admin.delete_user(user)


@pytest.fixture
def clear_user(user_name, openstack_admin):
    yield None
    openstack_admin.delete_user(
        openstack_admin.identity.find_user(user_name))


def test_create_user(login, driver, user_name, openstack_admin,
                     config, clear_user):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'users',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create User").click()
    user_form = driver.find_element_by_css_selector(".modal-dialog form")
    user_form.find_element_by_id("id_name").send_keys(user_name)
    user_form.find_element_by_id("id_password").send_keys(default_password)
    user_form.find_element_by_id(
        "id_confirm_password").send_keys(default_password)
    user_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: User "{user_name}" was successfully created.' in messages
    assert openstack_admin.identity.find_user(user_name) is not None


def test_delete_user(login, driver, user_name, openstack_admin,
                     new_user, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'users',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#users tr[data-display='{user_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete User")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted User: {user_name}" in messages
    assert openstack_admin.identity.find_user(user_name) is None


def test_change_user_password(login, driver, user_name, new_user, config):
    new_password = f"Password_{user_name}"
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'users',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#users tr[data-display='{user_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Change Password")
    password_form = driver.find_element_by_css_selector(".modal-dialog form")
    password_form.find_element_by_id("id_password").send_keys(new_password)
    password_form.find_element_by_id(
        "id_confirm_password").send_keys(new_password)
    password_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: User password has been updated successfully." in messages
