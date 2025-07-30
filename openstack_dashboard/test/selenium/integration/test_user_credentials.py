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
from selenium.common import exceptions

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def user_credential_blob():
    return 'blob_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_user_credential_TOTP(user_credential_blob, openstack_admin):
    user_credential = openstack_admin.identity.create_credential(
        type='totp',
        blob=user_credential_blob,
        user_id=openstack_admin.identity.find_user('admin').id
    )
    yield user_credential
    openstack_admin.identity.delete_credential(user_credential)


@pytest.fixture
def clear_user_credentials(openstack_admin):
    yield None
    user_credentials_sdk = openstack_admin.identity.credentials()
    for cred in user_credentials_sdk:
        openstack_admin.identity.delete_credential(cred)


def test_create_user_credential_totp(login, driver, openstack_admin, config,
                                     clear_user_credentials):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'credentials',
    ))
    driver.get(url)
    credentials_sdk_before = list(openstack_admin.identity.credentials())
    assert (len(credentials_sdk_before) == 0)
    driver.find_element_by_link_text("Create User Credential").click()
    user_credential_form = driver.find_element_by_css_selector(
        ".modal-dialog form")
    widgets.select_from_specific_dropdown_in_form(
        user_credential_form, 'id_cred_type', 'TOTP')
    user_credential_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver, config)
    assert 'Success: User credential created successfully.' in messages
    credentials_sdk_after = list(openstack_admin.identity.credentials())
    assert (len(credentials_sdk_after) == 1 and
            credentials_sdk_after[0]['type'] == 'totp')


def test_create_user_credential_ec2(login, driver, openstack_admin, config,
                                    clear_user_credentials):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'credentials',
    ))
    driver.get(url)
    credentials_sdk_before = list(openstack_admin.identity.credentials())
    assert (len(credentials_sdk_before) == 0)
    driver.find_element_by_link_text("Create User Credential").click()
    user_credential_form = driver.find_element_by_css_selector(
        ".modal-dialog form")
    widgets.select_from_specific_dropdown_in_form(
        user_credential_form, 'id_cred_type', 'EC2')
    user_credential_form.find_element_by_id("id_data").clear()
    user_credential_form.find_element_by_id("id_data").send_keys(
        '{"access": "acs", "secret": "scrt"}')
    widgets.select_from_specific_dropdown_in_form(
        user_credential_form, 'id_project', 'admin')
    user_credential_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver, config)
    assert 'Success: User credential created successfully.' in messages
    credentials_sdk_after = list(openstack_admin.identity.credentials())
    assert (len(credentials_sdk_after) == 1 and
            credentials_sdk_after[0]['type'] == 'ec2' and
            (credentials_sdk_after[0]['blob'] ==
             '{"access": "acs", "secret": "scrt"}') and
            (credentials_sdk_after[0]['project_id'] ==
             openstack_admin.identity.find_project('admin').id))


def test_delete_user_credential(login, driver, openstack_admin, config,
                                user_credential_blob, new_user_credential_TOTP):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'credentials',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#credentialstable tr[data-display='{user_credential_blob}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete User Credential")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver, config)
    assert (f"Success: Deleted User Credential: {user_credential_blob}" in
            messages)
    credentials_sdk_after = list(openstack_admin.identity.credentials())
    assert (len(credentials_sdk_after) == 0)


def test_edit_user_credential(login, driver, openstack_admin, config,
                              user_credential_blob, new_user_credential_TOTP):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'credentials',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#credentialstable tr[data-display='{user_credential_blob}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    user_credential_form = driver.find_element_by_css_selector(
        ".modal-dialog form")
    user_credential_form.find_element_by_id("id_data").clear()
    user_credential_form.find_element_by_id("id_data").send_keys(
        f"EDITED_{user_credential_blob}")
    user_credential_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver, config)
    assert ("Success: User credential updated successfully." in messages)
    credentials_sdk = list(openstack_admin.identity.credentials())
    assert (len(credentials_sdk) == 1 and
            credentials_sdk[0]['blob'] == f'EDITED_{user_credential_blob}')


def test_user_credential_filtration(login, driver, openstack_admin,
                                    new_user_credential_TOTP, config,
                                    clear_user_credentials):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'identity',
        'credentials',
    ))
    driver.get(url)
    filter_input_field = driver.find_element_by_css_selector(".form-control")
    filter_input_field.clear()
    filter_input_field.send_keys('demo')
    driver.find_element_by_id("credentialstable__action_filter").click()
    try:
        driver.find_element_by_xpath(
            "//td[text()='No items to display.']")
    except exceptions.NoSuchElementException:
        assert False, "Message 'No items to display' not found"
    filter_input_field = driver.find_element_by_css_selector(".form-control")
    filter_input_field.clear()
    filter_input_field.send_keys('admin')
    driver.find_element_by_id("credentialstable__action_filter").click()
    rows = driver.find_elements_by_css_selector(
        "table#credentialstable tr[data-display]")
    assert len(rows) == 1
