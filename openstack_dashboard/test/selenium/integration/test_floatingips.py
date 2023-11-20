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

import re

from oslo_utils import uuidutils
import pytest
import test_instances

from openstack_dashboard.test.selenium import widgets

# Imported fixtures
instance_name = test_instances.instance_name
new_instance_demo = test_instances.new_instance_demo


@pytest.fixture
def floatingip_description():
    return('horizon_floatingip_description_%s'
           % uuidutils.generate_uuid(dashed=False))


@pytest.fixture
def new_floating_ip(openstack_demo, config):
    floatingip = openstack_demo.network.create_ip(
        floating_network_id=openstack_demo.network.find_network(
            config.network.external_network).id
    )
    yield floatingip
    openstack_demo.network.delete_ip(floatingip)


@pytest.fixture
def clear_floatingip_using_description(openstack_demo, floatingip_description):
    yield None
    floatingips_list = openstack_demo.network.get(
        "/floatingips").json()["floatingips"]
    ip_address = None
    for floatingip_data in floatingips_list:
        if floatingip_data['description'] == floatingip_description:
            ip_address = floatingip_data['floating_ip_address']
            break
    openstack_demo.network.delete_ip(
        openstack_demo.network.find_ip(ip_address))


@pytest.fixture
def clear_floatingip_using_ip(openstack_demo, new_instance_demo):
    yield None
    openstack_demo.network.delete_ip(
        openstack_demo.network.find_ip(new_instance_demo.public_v4))


def test_allocate_floatingip(login, driver, config, openstack_demo,
                             clear_floatingip_using_description,
                             floatingip_description):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'floating_ips',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Allocate IP To Project").click()
    floatingip_form = driver.find_element_by_css_selector(".modal-dialog form")
    floatingip_form.find_element_by_id("id_description").send_keys(
        floatingip_description)
    floatingip_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    if len(messages) > 1:
        message = [msg for msg in messages if
                   "Success: Allocated Floating IP" in msg][0]
    else:
        message = messages[0]
    assert 'Success: Allocated Floating IP' in message
    ip_address = re.search(r"\d+\.\d+\.\d+\.\d+", message)
    assert ip_address is not None
    floating_ip_address = ip_address.group()
    assert openstack_demo.network.find_ip(floating_ip_address) is not None


def test_release_floatingip(login, driver, openstack_demo, config,
                            new_floating_ip):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'floating_ips',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#floating_ips tr[data-display="
        f"'{new_floating_ip.floating_ip_address}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Release Floating IP")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Released Floating IP: "
           f"{new_floating_ip.floating_ip_address}" in messages)
    assert openstack_demo.network.find_ip(
        new_floating_ip.floating_ip_address) is None


def test_associate_floatingip(login, driver, openstack_demo, new_floating_ip,
                              config, instance_name, new_instance_demo):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'floating_ips',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#floating_ips tr[data-display="
        f"'{new_floating_ip.floating_ip_address}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    associateip_form = driver.find_element_by_css_selector(
        "form .modal-content")
    widgets.select_from_specific_dropdown_in_form(
        associateip_form, "id_ip_id", new_floating_ip.floating_ip_address)
    widgets.select_from_specific_dropdown_in_form(
        associateip_form, "id_port_id",
        f"{instance_name}: {new_instance_demo.private_v4}")
    associateip_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: IP address {new_floating_ip.floating_ip_address}"
           f" associated." in messages)
    assert(new_instance_demo.id == openstack_demo.network.find_ip(
           new_floating_ip.floating_ip_address).port_details['device_id'])


@pytest.mark.parametrize('new_instance_demo', [(1, True)],
                         indirect=True)
def test_disassociate_floatingip(login, driver, openstack_demo, config,
                                 instance_name, new_instance_demo,
                                 clear_floatingip_using_ip):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'floating_ips',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#floating_ips tr[data-display="
        f"'{new_instance_demo.public_v4}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector(".data-table-action").click()
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Successfully disassociated Floating IP: "
           f"{new_instance_demo.public_v4}" in messages)
    assert openstack_demo.compute.find_server(instance_name).public_v4 == ""
