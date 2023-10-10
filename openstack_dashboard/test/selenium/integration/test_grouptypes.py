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
def grouptype_name():
    return 'horizon_grouptype_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_grouptype(grouptype_name, openstack_admin):
    grouptype = openstack_admin.block_storage.create_group_type(
        name=grouptype_name,
    )
    yield grouptype
    openstack_admin.block_storage.delete_group_type(grouptype)


@pytest.fixture
def clear_grouptype(grouptype_name, openstack_admin):
    yield None
    openstack_admin.block_storage.delete_group_type(
        openstack_admin.block_storage.find_group_type(grouptype_name))


def test_create_grouptype(login, driver, grouptype_name, openstack_admin,
                          config, clear_grouptype):

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'group_types',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Group Type").click()
    grouptype_form = driver.find_element_by_css_selector(".modal-content form")
    grouptype_form.find_element_by_id("id_name").send_keys(grouptype_name)
    grouptype_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Successfully created group type: {grouptype_name}'
           in messages)
    assert(openstack_admin.block_storage.find_group_type(grouptype_name)
           is not None)


def test_delete_grouptype(login, driver, grouptype_name, openstack_admin,
                          new_grouptype, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'group_types',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#group_types tr[data-display='{grouptype_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Group Type")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Group Type: {grouptype_name}" in messages
    assert openstack_admin.block_storage.find_group_type(grouptype_name) is None
