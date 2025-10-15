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

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select


@pytest.fixture(scope='session')
def env_identity_providers(openstack_admin):
    identity_providers_sdk = list(openstack_admin.identity.identity_providers())
    yield identity_providers_sdk


def test_federation_keystone_user_login(login, driver, config,
                                        env_identity_providers):
    if len(env_identity_providers) == 0:
        pytest.skip("Test required only when federation is enabled.")

    login('user')
    try:
        driver.find_element_by_xpath(
            config.theme.user_name_xpath)
        assert True
    except NoSuchElementException:
        assert False


def test_federation_keystone_admin_login(login, driver, config,
                                         env_identity_providers):
    if len(env_identity_providers) == 0:
        pytest.skip("Test required only when federation is enabled.")

    login('admin')
    try:
        driver.find_element_by_xpath(
            config.theme.user_name_xpath)
        assert True
    except NoSuchElementException:
        assert False


@pytest.fixture(scope='session')
def idps_oidc_credentials(config):
    idps_oidc_credentials = {
        'user1': (
            config.IdPsOIDC.keycloak_test_user1_username,
            config.IdPsOIDC.keycloak_test_user1_password,
            config.IdPsOIDC.keycloak_test_user_home_project,
            config.IdPsOIDC.web_sso_choice_value1,
            config.IdPsOIDC.identity_provider1,
        ),
        'user2': (
            config.IdPsOIDC.keycloak_test_user2_username,
            config.IdPsOIDC.keycloak_test_user2_password,
            config.IdPsOIDC.keycloak_test_user_home_project,
            config.IdPsOIDC.web_sso_choice_value1,
            config.IdPsOIDC.identity_provider1,
        ),
        'user3': (
            config.IdPsOIDC.keycloak_test_user3_username,
            config.IdPsOIDC.keycloak_test_user3_password,
            config.IdPsOIDC.keycloak_test_user_home_project2,
            config.IdPsOIDC.web_sso_choice_value2,
            config.IdPsOIDC.identity_provider2,
        ),
        'user4': (
            config.IdPsOIDC.keycloak_test_user4_username,
            config.IdPsOIDC.keycloak_test_user4_password,
            config.IdPsOIDC.keycloak_test_user_home_project2,
            config.IdPsOIDC.web_sso_choice_value2,
            config.IdPsOIDC.identity_provider2,
        ),
    }
    return idps_oidc_credentials


def start_common_federation_login(driver, openstack_admin,
                                  idps_oidc_credentials):
    (_, _, _, web_sso_choice_value,
        identity_provider) = idps_oidc_credentials
    idp_url = (
        openstack_admin.identity
        .find_identity_provider(identity_provider)['remote_ids'][0]
    )
    select_auth = driver.find_element_by_id('id_auth_type')
    select_auth.click()
    select_opt = Select(select_auth)
    select_opt.select_by_value(web_sso_choice_value)
    button = driver.find_element_by_css_selector('.btn-primary')
    button.click()
    keycloak_url_field = driver.find_element_by_css_selector(
        'input[type="text"][name="iss"]')
    keycloak_url_field.send_keys(idp_url)
    submit_button = driver.find_element_by_css_selector(
        'input[type="submit"][value="Submit"]')
    submit_button.click()


def logged_in_as(driver, config, idps_oidc_credentials):
    (username, _, home_project, _, _) = idps_oidc_credentials
    try:
        project_element = driver.find_element_by_xpath(
            config.theme.project_name_xpath)
        try:
            project_element.find_element_by_xpath(
                f'.//*[normalize-space()="{home_project}"]')
        except NoSuchElementException:
            return False, f"Project '{home_project}' not found on page"
    except NoSuchElementException:
        return False, (
            f"Project xpath not found: "
            f"{config.theme.project_name_xpath}"
        )
    try:
        username_element = driver.find_element_by_xpath(
            config.theme.user_name_xpath)
        try:
            username_element.find_element_by_xpath(
                f'.//*[normalize-space()="{username}"]')
        except NoSuchElementException:
            return False, f"Username '{username}' not found on page"
    except NoSuchElementException:
        return False, (
            f"Username xpath not found: "
            f"{config.theme.user_name_xpath}"
        )
    return True, "Login fully verified"


def test_federation_keycloak_test_user_login(driver, login,
                                             config,
                                             env_identity_providers,
                                             idps_oidc_credentials):
    if len(env_identity_providers) != 1:
        pytest.skip("Test requires exactly one IdP.")

    login(None)
    (username, password, _, _, _) = idps_oidc_credentials['user1']
    select_auth = driver.find_element_by_id('id_auth_type')
    select_auth.click()
    select_opt = Select(select_auth)
    select_opt.select_by_visible_text('OpenID Connect')
    button = driver.find_element_by_css_selector(
        '.btn-primary')
    button.click()
    keycloak_user_field = driver.find_element_by_id('username')
    keycloak_user_field.send_keys(username)
    keycloak_pass_field = driver.find_element_by_id('password')
    keycloak_pass_field.send_keys(password)
    kc_login_button = driver.find_element_by_id('kc-login')
    kc_login_button.click()
    success, message = logged_in_as(
        driver, config, idps_oidc_credentials['user1'])
    assert success, message


def test_multi_realm_IdP1_login_full_flow(
        driver, config, login, openstack_admin,
        env_identity_providers,
        idps_oidc_credentials):
    """3 tests are combined into one full_flow test.

    The tests are testing specific sequence full_authorization ->
    reauthorization -> reset login (to login using different user
    under the same IdP).
    The tests can not run independently because since one user is logged in
    using full_auth, there is no possibility use full_auth steps again
    and we need to keep order of the tests and their dependencies.
    Test complete login flow for IdP1: full_auth -> reauth -> reset_login.
    """
    if len(env_identity_providers) < 2:
        pytest.skip("Environment has less than 2 IdPs, "
                    "Multi-Realm test disabled.")

    login(None)
    start_common_federation_login(
        driver, openstack_admin, idps_oidc_credentials['user1'])
    # Step 1: Full authentication (creates Keycloak session)
    # username + password required
    (username, password, _, _, _) = idps_oidc_credentials['user1']
    keycloak_user_field = driver.find_element_by_id('username')
    keycloak_user_field.send_keys(username)
    keycloak_pass_field = driver.find_element_by_id('password')
    keycloak_pass_field.send_keys(password)
    kc_login_button = driver.find_element_by_id('kc-login')
    kc_login_button.click()
    success, message = logged_in_as(
        driver, config, idps_oidc_credentials['user1'])
    assert success, message

    # Step 2: Re-authentication (uses existing session, only password required)
    login(None)
    start_common_federation_login(
        driver, openstack_admin, idps_oidc_credentials['user1'])
    driver.find_element_by_xpath(
        "//span[text()='Please re-authenticate to continue']")
    keycloak_pass_field = driver.find_element_by_id('password')
    keycloak_pass_field.send_keys(password)
    kc_login_button = driver.find_element_by_id('kc-login')
    kc_login_button.click()
    success, message = logged_in_as(
        driver, config, idps_oidc_credentials['user1'])
    assert success, message

    # Step 3: Login after clicking reset-login to log in using
    # different user under the same IdP. Username + password required.
    login(None)
    start_common_federation_login(
        driver, openstack_admin, idps_oidc_credentials['user2'])
    (username, password, _, _, _) = idps_oidc_credentials['user2']
    driver.find_element_by_id('reset-login').click()
    keycloak_user_field = driver.find_element_by_id('username')
    keycloak_user_field.send_keys(username)
    keycloak_pass_field = driver.find_element_by_id('password')
    keycloak_pass_field.send_keys(password)
    kc_login_button = driver.find_element_by_id('kc-login')
    kc_login_button.click()
    success, message = logged_in_as(
        driver, config, idps_oidc_credentials['user2'])
    assert success, message


def test_multi_realm_IdP2_login_full_auth(driver, config, login,
                                          openstack_admin,
                                          env_identity_providers,
                                          idps_oidc_credentials):
    if len(env_identity_providers) < 2:
        pytest.skip("Environment has less than 2 IdPs, "
                    "Multi-Realm test disabled.")

    login(None)
    start_common_federation_login(
        driver, openstack_admin, idps_oidc_credentials['user3'])
    (username, password, _, _, _) = idps_oidc_credentials['user3']
    keycloak_user_field = driver.find_element_by_id('username')
    keycloak_user_field.send_keys(username)
    keycloak_pass_field = driver.find_element_by_id('password')
    keycloak_pass_field.send_keys(password)
    kc_login_button = driver.find_element_by_id('kc-login')
    kc_login_button.click()
    success, message = logged_in_as(
        driver, config, idps_oidc_credentials['user3'])
    assert success, message
