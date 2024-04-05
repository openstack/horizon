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

from openstack_dashboard import api


def test_vcpu_pcpu_data_display(live_server, driver, user, dashboard_data):
    with mock.patch.object(api.nova, 'service_list') as mocked_s_l, \
            mock.patch.object(api.nova, 'hypervisor_list') as mocked_h_l, \
            mock.patch.object(api.nova, 'hypervisor_stats') as mocked_h_s, \
            mock.patch.object(api.placement, 'get_providers') as mocked_g_p:
        mocked_s_l.return_value = dashboard_data.services.list()
        mocked_h_l.return_value = dashboard_data.hypervisors.list()
        mocked_h_s.return_value = dashboard_data.hypervisors.stats

        providers = [{}]
        for p in providers:
            inventories = {'VCPU': {'total': 16, 'reserved': 4,
                                    'allocation_ratio': 4.0},
                           'PCPU': {'total': 4, 'reserved': 2,
                                    'allocation_ratio': 1.0}}
            usages = {'VCPU': 2, 'PCPU': 1}
            vcpus = inventories.get('VCPU')
            pcpus = inventories.get('PCPU')
            p['uuid'] = "test_provider"
            p['inventories'] = inventories
            p['usages'] = usages
            p['vcpus_used'] = usages.get('VCPU')
            p['vcpus_reserved'] = vcpus['reserved']
            p['vcpus'] = vcpus['total']
            p['vcpus_ar'] = vcpus['allocation_ratio']
            p['vcpus_capacity'] = int(vcpus['allocation_ratio'] *
                                      vcpus['total'])
            p['pcpus_used'] = usages.get('PCPU')
            p['pcpus_reserved'] = pcpus['reserved']
            p['pcpus'] = pcpus['total']
            p['pcpus_ar'] = pcpus['allocation_ratio']
            p['pcpus_capacity'] = int(pcpus['allocation_ratio'] *
                                      pcpus['total'])
        mocked_g_p.return_value = providers

        driver.get(live_server.url + '/admin/hypervisors')
        assert (driver.find_element_by_xpath(
            f"//*[normalize-space()='VCPU Usage']/"
            f"ancestor::div[contains(@class,'d3_quota_bar')]"
            f"/div[contains(@class,'h6')]/"
            f"span[1]").text == str(p['vcpus_used']))
        assert (driver.find_element_by_xpath(
            f"//*[normalize-space()='VCPU Usage']/"
            f"ancestor::div[contains(@class,'d3_quota_bar')]"
            f"/div[contains(@class,'h6')]/"
            f"span[2]").text == str(p['vcpus_capacity']))

        assert (driver.find_element_by_xpath(
            f"//*[normalize-space()='PCPU Usage']/"
            f"ancestor::div[contains(@class,'d3_quota_bar')]"
            f"/div[contains(@class,'h6')]/"
            f"span[1]").text == str(p['pcpus_used']))
        assert (driver.find_element_by_xpath(
            f"//*[normalize-space()='PCPU Usage']/"
            f"ancestor::div[contains(@class,'d3_quota_bar')]"
            f"/div[contains(@class,'h6')]/"
            f"span[2]").text == str(p['pcpus_capacity']))

        driver.find_element_by_link_text("Resource Provider").click()
        resource_provider_tab = driver.find_element_by_id(
            "hypervisor_info__provider")
        table_header = resource_provider_tab.find_elements_by_css_selector(
            ".table_column_header th")
        table_row_test_provider = (
            resource_provider_tab.find_elements_by_css_selector(
                "#providers__row__test_provider td"))
        table_providers = dict(zip((x.text for x in table_header),
                                   (x.text for x in table_row_test_provider)))

        want_to_check = {"VCPUs used": p['vcpus_used'],
                         "VCPUs reserved": p['vcpus_reserved'],
                         "VCPUs total": p['vcpus'],
                         "VCPUs allocation ratio": p['vcpus_ar'],
                         "PCPUs used": p['pcpus_used'],
                         "PCPUs reserved": p['pcpus_reserved'],
                         "PCPUs total": p['pcpus'],
                         "PCPUs allocation ratio": p['pcpus_ar']}

        for key, value in want_to_check.items():
            assert table_providers[key] == str(value)
