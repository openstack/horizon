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
def group_name():
    return 'horizon_group_name_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_group(group_name, openstack_admin):
    group = openstack_admin.identity.create_group(
        name=group_name,
        description=f"Description for: {group_name}",
    )
    yield group
    openstack_admin.identity.delete_group(group)


@pytest.fixture
def clear_group(group_name, openstack_admin):
    yield None
    openstack_admin.identity.delete_group(
        openstack_admin.identity.find_group(group_name))


def test_create_group(login, driver, group_name, openstack_admin, config,
                      clear_group):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'groups',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Group").click()
    group_form = driver.find_element_by_css_selector(".modal-dialog form")
    group_form.find_element_by_id("id_name").send_keys(group_name)
    group_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Group "{group_name}" was successfully created.'
           in messages)
    assert openstack_admin.identity.find_group(group_name) is not None


def test_delete_group(login, driver, group_name, openstack_admin, config,
                      new_group):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'groups',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#groups tr[data-display='{group_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Group")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Group: {group_name}" in messages
    assert openstack_admin.identity.find_group(group_name) is None


def test_edit_group_name_and_description(login, driver, group_name,
                                         openstack_admin, config, new_group):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'groups',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#groups tr[data-display='{group_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Edit Group")
    group_form = driver.find_element_by_css_selector(".modal-dialog form")
    group_form.find_element_by_id("id_name").clear()
    group_form.find_element_by_id("id_name").send_keys(f"EDITED_{group_name}")
    group_form.find_element_by_id("id_description").clear()
    group_form.find_element_by_id("id_description").send_keys(
        f"EDITED_Description for: {group_name}")
    group_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Group has been updated successfully." in messages
    assert(openstack_admin.identity.find_group(
           f"EDITED_{group_name}") is not None)
    assert(openstack_admin.identity.find_group(
           f"EDITED_{group_name}").description ==
           f"EDITED_Description for: {group_name}")
