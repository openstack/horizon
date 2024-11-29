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

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from openstack_dashboard.test.integration_tests import config

from openstack_dashboard import api
from openstack_dashboard.test.selenium import widgets

# Get browse_left_panel lists
conf = config.get_config()
t_b_p_m = conf.theme.browse_left_panel_main
t_b_p_s = conf.theme.browse_left_panel_sec


@pytest.mark.parametrize(
    "main_panel, sec_panel, link_text, title, h1_text",
    [
        (t_b_p_m[0], t_b_p_s[0], "API Access",
            "API Access - OpenStack Dashboard", "API Access"),
        (t_b_p_m[1], t_b_p_s[1], "Overview",
            "Instance Overview - OpenStack Dashboard", "Overview"),
        (t_b_p_m[2], t_b_p_s[2], "Instances",
            "Instances - OpenStack Dashboard", "Instances"),
        (t_b_p_m[3], t_b_p_s[3], "Images",
            "Images - OpenStack Dashboard", "Images"),
        (t_b_p_m[4], t_b_p_s[4], "Key Pairs",
            "Key Pairs - OpenStack Dashboard", "Key Pairs"),
        (t_b_p_m[5], t_b_p_s[5], "Server Groups",
            "Server Groups - OpenStack Dashboard", "Server Groups"),
        (t_b_p_m[6], t_b_p_s[6], "Volumes",
            "Volumes - OpenStack Dashboard", "Volumes"),
        (t_b_p_m[7], t_b_p_s[7], "Snapshots",
            "Volume Snapshots - OpenStack Dashboard", "Volume Snapshots"),
        (t_b_p_m[8], t_b_p_s[8], "Network Topology",
            "Network Topology - OpenStack Dashboard", "Network Topology"),
        (t_b_p_m[9], t_b_p_s[9], "Networks",
            "Networks - OpenStack Dashboard", "Networks"),
        (t_b_p_m[10], t_b_p_s[10], "Routers",
            "Routers - OpenStack Dashboard", "Routers"),
        (t_b_p_m[11], t_b_p_s[11], "Security Groups",
            "Security Groups - OpenStack Dashboard", "Security Groups"),
        (t_b_p_m[12], t_b_p_s[12], "Floating IPs",
            "Floating IPs - OpenStack Dashboard", "Floating IPs"),
        (t_b_p_m[13], t_b_p_s[13], "Trunks",
            "Trunks - OpenStack Dashboard", "Trunks"),
        (t_b_p_m[14], t_b_p_s[14], "Network QoS",
            "Network QoS Policies - OpenStack Dashboard", "QoS Policies"),
        (t_b_p_m[15], t_b_p_s[15], "Containers",
            "Containers - OpenStack Dashboard", "Containers"),
        (t_b_p_m[16], t_b_p_s[16], "Overview",
            "Usage Overview - OpenStack Dashboard", "Overview"),
        (t_b_p_m[17], t_b_p_s[17], "Hypervisors",
            "Hypervisors - OpenStack Dashboard", "All Hypervisors"),
        (t_b_p_m[18], t_b_p_s[18], "Host Aggregates",
            "Host Aggregates - OpenStack Dashboard", "Host Aggregates"),
        (t_b_p_m[19], t_b_p_s[19], "Instances",
            "Instances - OpenStack Dashboard", "Instances"),
        (t_b_p_m[20], t_b_p_s[20], "Flavors",
            "Flavors - OpenStack Dashboard", "Flavors"),
        (t_b_p_m[21], t_b_p_s[21], "Images",
            "Images - OpenStack Dashboard", "Images"),
        (t_b_p_m[22], t_b_p_s[22], "Volumes",
            "Volumes - OpenStack Dashboard", "Volumes"),
        (t_b_p_m[23], t_b_p_s[23], "Snapshots",
            "Volume Snapshots - OpenStack Dashboard", "Volume Snapshots"),
        (t_b_p_m[24], t_b_p_s[24], "Volume Types",
            "Volume Types - OpenStack Dashboard", "Volume Types"),
        (t_b_p_m[25], t_b_p_s[25], "Group Types",
            "Group Types - OpenStack Dashboard", "Group Types"),
        (t_b_p_m[26], t_b_p_s[26], "Networks",
            "Networks - OpenStack Dashboard", "Networks"),
        (t_b_p_m[27], t_b_p_s[27], "Routers",
            "Routers - OpenStack Dashboard", "Routers"),
        (t_b_p_m[28], t_b_p_s[28], "Floating IPs",
            "Floating IPs - OpenStack Dashboard", "Floating IPs"),
        (t_b_p_m[29], t_b_p_s[29], "Trunks",
            "Trunks - OpenStack Dashboard", "Trunks"),
        (t_b_p_m[30], t_b_p_s[30], "RBAC Policies",
            "RBAC Policies - OpenStack Dashboard", "RBAC Policies"),
        (t_b_p_m[31], t_b_p_s[31], "Defaults",
            "Defaults - OpenStack Dashboard", "Defaults"),
        (t_b_p_m[32], t_b_p_s[32], "Metadata Definitions",
            "Metadata Definitions - OpenStack Dashboard",
            "Metadata Definitions"),
        (t_b_p_m[33], t_b_p_s[33], "System Information",
            "System Information - OpenStack Dashboard", "System Information"),
        (t_b_p_m[34], t_b_p_s[34], "Projects",
            "Projects - OpenStack Dashboard", "Projects"),
        (t_b_p_m[35], t_b_p_s[35], "Users",
            "Users - OpenStack Dashboard", "Users"),
        (t_b_p_m[36], t_b_p_s[36], "Groups",
            "Groups - OpenStack Dashboard", "Groups"),
        (t_b_p_m[37], t_b_p_s[37], "Roles",
            "Roles - OpenStack Dashboard", "Roles"),
        (t_b_p_m[38], t_b_p_s[38], "Application Credentials",
            "Application Credentials - OpenStack Dashboard",
            "Application Credentials"),
    ]
)
def test_browse_left_panel(live_server, driver, user, dashboard_data,
                           main_panel, sec_panel, link_text, title,
                           h1_text, config):
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
                api.neutron, 'tenant_quota_detail_get') as mocked_t_q_d_g:
        mocked_i_q_e_s.return_value = True
        mocked_i_l_d.return_value = [dashboard_data.images.list()]
        mocked_f_l.return_value = dashboard_data.flavors.list()
        mocked_i_e_s.return_value = True
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

        driver.get(live_server.url + '/settings')
        # First scroll click
        driver.find_element_by_xpath(
            f".//a[normalize-space()='{main_panel.capitalize()}']").click()
        if sec_panel != 'None':
            sec_line_req_button = config.theme.b_l_p_sec_line_req_btn.format(
                main_panel=main_panel, sec_panel=sec_panel)
            # Second scroll click
            WebDriverWait(driver, config.selenium.implicit_wait).until(
                EC.element_to_be_clickable(
                    (By.XPATH, sec_line_req_button))).click()
            sidebar_xpath = config.theme.b_l_p_sidebar_xpath.format(
                main_panel=main_panel, sec_panel=sec_panel)
            # Get tab with output of second scroll
            sidebar = driver.find_element_by_xpath(sidebar_xpath)
        else:
            # In case there is not second scroll
            sec_line_xpath = config.theme.b_l_p_sec_line_xpath.format(
                main_panel=main_panel)
            sidebar = driver.find_element_by_xpath(sec_line_xpath)
        sidebar.find_element_by_link_text(link_text).click()
        assert driver.title == title
        assert driver.find_element_by_css_selector("h1").text == h1_text


def test_browse_user_setting_tab(live_server, driver, user, config):
    driver.get(live_server.url + '/project/api_access')
    user_button = driver.find_element_by_xpath(config.theme.user_name_xpath)
    widgets.select_from_dropdown(user_button, "Settings")
    assert driver.title == "User Settings - OpenStack Dashboard"
    assert driver.find_element_by_css_selector("h1").text == "User Settings"


def test_browse_change_password_tab(live_server, driver, user, config):
    driver.get(live_server.url + '/project/api_access')
    user_button = driver.find_element_by_xpath(config.theme.user_name_xpath)
    widgets.select_from_dropdown(user_button, "Settings")
    driver.find_element_by_link_text("Change Password").click()
    assert driver.title == "Change Password - OpenStack Dashboard"
    assert driver.find_element_by_css_selector("h1").text == "Change Password"
