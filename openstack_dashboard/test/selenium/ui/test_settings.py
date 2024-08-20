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

from unittest import mock

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from openstack_dashboard import api
from openstack_dashboard.test.selenium import widgets

import horizon


def test_login(live_server, driver, mock_openstack_auth, mock_keystoneclient):
    # We go to a page that doesn't do more api calls.
    driver.get(live_server.url + '/settings')
    assert driver.title == "Login - OpenStack Dashboard"
    user_field = driver.find_element_by_id('id_username')
    user_field.clear()
    user_field.send_keys("user")
    pass_field = driver.find_element_by_id('id_password')
    pass_field.clear()
    pass_field.send_keys("password")
    button = driver.find_element_by_css_selector('div.panel-footer button.btn')
    button.click()
    errors = [m.text for m in
              driver.find_elements_by_css_selector('div.alert-danger p')]
    assert errors == []
    assert driver.title != "Login - OpenStack Dashboard"


def test_languages(live_server, driver, user):
    driver.get(live_server.url + '/settings')
    user_settings = driver.find_element_by_id('user_settings_modal')
    language_options = user_settings.find_element_by_id('id_language')
    language_options.click()
    language_options.find_element_by_xpath("//option[@value='de']").click()
    user_settings.find_element_by_xpath('//*[@class="btn btn-primary"]').click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert "Success: Settings saved." in messages
    assert "Error" not in messages


def test_dashboard_help_redirection(live_server, driver, user, config):
    driver.get(live_server.url + '/settings')
    user_dropdown_menu = driver.find_element_by_css_selector(
        '.nav.navbar-nav.navbar-right')
    widgets.select_from_dropdown(user_dropdown_menu, "Help")
    available_windows = driver.window_handles
    assert len(available_windows) == 2
    driver.switch_to.window(available_windows[-1])
    WebDriverWait(driver, config.selenium.page_timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.navbar-brand')))
    assert config.dashboard.help_url in driver.current_url
    driver.close()
    driver.switch_to.window(available_windows[0])


def test_switch_to_material_theme(live_server, driver, user, config):
    driver.get(live_server.url + '/settings')
    user_dropdown_menu = driver.find_element_by_css_selector(
        '.nav.navbar-nav.navbar-right')
    user_dropdown_menu.click()
    assert ((user_dropdown_menu.find_element_by_css_selector(
        ".theme-default.dropdown-selected") and
        driver.find_element_by_css_selector(".navbar-default")))
    options = user_dropdown_menu.find_element_by_css_selector(
        "ul.dropdown-menu[id='editor_list']")
    options.find_element_by_xpath(f".//*[normalize-space()='Material']").click()
    WebDriverWait(driver, config.selenium.page_timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.material-header')))
    user_dropdown_menu = driver.find_element_by_css_selector(
        '.nav.navbar-nav.navbar-right')
    user_dropdown_menu.click()
    assert (user_dropdown_menu.find_element_by_css_selector(
        ".theme-material.dropdown-selected") and
        driver.find_element_by_css_selector(".material-header"))


def test_message_after_password_change(live_server, driver, user,
                                       dashboard_data):
    with mock.patch.object(
        api.neutron, 'is_quotas_extension_supported') as mocked_i_q_e_s, \
            mock.patch.object(
                api.glance, 'image_list_detailed') as mocked_i_l_d, \
            mock.patch.object(
                api.neutron, 'is_extension_supported') as mocked_i_e_s, \
            mock.patch.object(
                api.nova, 'flavor_list') as mocked_f_l, \
            mock.patch.object(
                api.nova, 'tenant_absolute_limits') as mocked_t_a_l, \
            mock.patch.object(
                api.neutron, 'tenant_quota_detail_get') as mocked_t_q_d_g, \
            mock.patch.object(
                horizon.utils.functions, 'add_logout_reason') as mocked_a_l_r:
        mocked_i_q_e_s.return_value = True
        mocked_i_l_d.return_value = [dashboard_data.images.list()]
        mocked_i_e_s.return_value = True
        mocked_f_l.return_value = dashboard_data.flavors.list()
        mocked_t_a_l.return_value = dashboard_data.limits['absolute']
        mocked_t_q_d_g.return_value = {
            "network": {
                'reserved': 0,
                'used': 0,
                'limit': 10
            }, "router": {
                'reserved': 0,
                'used': 0,
                'limit': 10
            }
        }
        mock_user = api.keystone.user_get(None, None)
        mock_user.options = {}
        driver.get(live_server.url + '/settings/password')
        driver.find_element_by_id("id_current_password").send_keys(
            dashboard_data.user.password)
        driver.find_element_by_id("id_new_password").send_keys("newpass")
        driver.find_element_by_id("id_confirm_password").send_keys("newpass")
        driver.find_element_by_css_selector(".btn-primary").click()
        mocked_a_l_r.assert_called_once()
        assert (mocked_a_l_r.call_args.args[2] ==
                'Password changed. Please log in again to continue.')
