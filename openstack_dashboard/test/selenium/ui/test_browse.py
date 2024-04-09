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

from openstack_dashboard import api


@pytest.mark.parametrize(
    "main_panel, sec_panel, link_text, title, h1_text",
    [
        ("project", None, "API Access", "API Access - OpenStack Dashboard",
            "API Access"),
        ("project", "compute", "Overview",
            "Instance Overview - OpenStack Dashboard", "Overview"),
        ("project", "compute", "Instances",
            "Instances - OpenStack Dashboard", "Instances"),
        ("project", "compute", "Images",
            "Images - OpenStack Dashboard", "Images"),
        ("project", "compute", "Key Pairs",
            "Key Pairs - OpenStack Dashboard", "Key Pairs"),
        ("project", "compute", "Server Groups",
            "Server Groups - OpenStack Dashboard", "Server Groups"),
        ("project", "volumes", "Volumes",
            "Volumes - OpenStack Dashboard", "Volumes"),
        ("project", "volumes", "Snapshots",
            "Volume Snapshots - OpenStack Dashboard", "Volume Snapshots"),
        ("project", "network", "Network Topology",
            "Network Topology - OpenStack Dashboard", "Network Topology"),
        ("project", "network", "Networks",
            "Networks - OpenStack Dashboard", "Networks"),
        ("project", "network", "Routers",
            "Routers - OpenStack Dashboard", "Routers"),
        ("project", "network", "Security Groups",
            "Security Groups - OpenStack Dashboard", "Security Groups"),
        ("project", "network", "Floating IPs",
            "Floating IPs - OpenStack Dashboard", "Floating IPs"),
        ("project", "network", "Trunks",
            "Trunks - OpenStack Dashboard", "Trunks"),
        ("project", "network", "Network QoS",
            "Network QoS Policies - OpenStack Dashboard", "QoS Policies"),
        ("project", "object_store", "Containers",
            "Containers - OpenStack Dashboard", "Containers"),
        ("admin", None, "Overview",
            "Usage Overview - OpenStack Dashboard", "Overview"),
        ("admin", "compute", "Hypervisors",
            "Hypervisors - OpenStack Dashboard", "All Hypervisors"),
        ("admin", "compute", "Host Aggregates",
            "Host Aggregates - OpenStack Dashboard", "Host Aggregates"),
        ("admin", "compute", "Instances",
            "Instances - OpenStack Dashboard", "Instances"),
        ("admin", "compute", "Flavors",
            "Flavors - OpenStack Dashboard", "Flavors"),
        ("admin", "compute", "Images",
            "Images - OpenStack Dashboard", "Images"),
        ("admin", "volume", "Volumes",
            "Volumes - OpenStack Dashboard", "Volumes"),
        ("admin", "volume", "Snapshots",
            "Volume Snapshots - OpenStack Dashboard", "Volume Snapshots"),
        ("admin", "volume", "Volume Types",
            "Volume Types - OpenStack Dashboard", "Volume Types"),
        ("admin", "volume", "Group Types",
            "Group Types - OpenStack Dashboard", "Group Types"),
        ("admin", "network", "Networks",
            "Networks - OpenStack Dashboard", "Networks"),
        ("admin", "network", "Routers",
            "Routers - OpenStack Dashboard", "Routers"),
        ("admin", "network", "Floating IPs",
            "Floating IPs - OpenStack Dashboard", "Floating IPs"),
        ("admin", "network", "Trunks",
            "Trunks - OpenStack Dashboard", "Trunks"),
        ("admin", "network", "RBAC Policies",
            "RBAC Policies - OpenStack Dashboard", "RBAC Policies"),
        ("admin", "admin", "Defaults",
            "Defaults - OpenStack Dashboard", "Defaults"),
        ("admin", "admin", "Metadata Definitions",
            "Metadata Definitions - OpenStack Dashboard",
            "Metadata Definitions"),
        ("admin", "admin", "System Information",
            "System Information - OpenStack Dashboard", "System Information"),
        ("identity", None, "Projects",
            "Projects - OpenStack Dashboard", "Projects"),
        ("identity", None, "Users",
            "Users - OpenStack Dashboard", "Users"),
        ("identity", None, "Groups",
            "Groups - OpenStack Dashboard", "Groups"),
        ("identity", None, "Roles",
            "Roles - OpenStack Dashboard", "Roles"),
        ("identity", None, "Application Credentials",
            "Application Credentials - OpenStack Dashboard",
            "Application Credentials"),
    ]
)
def test_browse_left_panel(live_server, driver, user, dashboard_data,
                           main_panel, sec_panel, link_text, title,
                           h1_text):
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
        driver.find_element_by_css_selector(
            f"a[data-target='#sidebar-accordion-{main_panel}']").click()
        if sec_panel is not None:
            driver.find_element_by_css_selector(
                f"a[data-target='#sidebar-accordion"
                f"-{main_panel}-{sec_panel}']").click()
            sidebar = driver.find_element_by_id(
                f"sidebar-accordion-{main_panel}-{sec_panel}")
        else:
            sidebar = driver.find_element_by_id(
                f"sidebar-accordion-{main_panel}")
        sidebar.find_element_by_link_text(link_text).click()
        assert driver.title == title
        assert driver.find_element_by_css_selector("h1").text == h1_text
