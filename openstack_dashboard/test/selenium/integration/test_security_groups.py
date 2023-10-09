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

import random

from oslo_utils import uuidutils
import pytest

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def sec_group_name():
    return 'sec_group_name_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_sec_group_demo(sec_group_name, openstack_demo):
    sec_group = openstack_demo.create_security_group(
        name=sec_group_name,
        description=f"Description for {sec_group_name}"
    )
    yield sec_group
    openstack_demo.delete_security_group(sec_group_name)


@pytest.fixture
def clear_sec_group_demo(sec_group_name, openstack_demo):
    yield None
    openstack_demo.delete_security_group(sec_group_name)


@pytest.fixture
def new_sec_group_rule_demo(new_sec_group_demo, openstack_demo):
    rule_port = random.randint(9000, 9999)
    sec_group_rule = openstack_demo.network.create_security_group_rule(
        security_group_id=new_sec_group_demo.id,
        direction="ingress",
        port_range_max=rule_port,
        port_range_min=rule_port,
        protocol="tcp"
    )
    yield sec_group_rule
    openstack_demo.network.delete_security_group_rule(sec_group_rule)


def test_create_sec_group_demo(login, driver, config, sec_group_name,
                               openstack_demo, clear_sec_group_demo):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'security_groups',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Security Group").click()
    sec_group_form = driver.find_element_by_css_selector(".modal-dialog form")
    sec_group_form.find_element_by_id("id_name").send_keys(sec_group_name)
    sec_group_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f'Success: Successfully created security group: {sec_group_name}'
           in messages)
    assert(openstack_demo.network.find_security_group(sec_group_name)
           is not None)


def test_delete_sec_group_demo(login, driver, sec_group_name, openstack_demo,
                               new_sec_group_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'security_groups',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#security_groups tr[data-display='{sec_group_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Security Group")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Security Group: {sec_group_name}" in messages
    assert openstack_demo.network.find_security_group(sec_group_name) is None


def test_add_rule_sec_group_demo(login, driver, sec_group_name, openstack_demo,
                                 new_sec_group_demo, config):
    rule_port = random.randint(9000, 9999)
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'security_groups',
        new_sec_group_demo.id,
    ))
    driver.get(url)
    driver.find_element_by_id("rules__action_add_rule").click()
    rule_form = driver.find_element_by_css_selector(".modal-dialog form")
    rule_form.find_element_by_id("id_port").send_keys(rule_port)
    rule_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Successfully added rule: ALLOW IPv4 {rule_port}"
           f"/tcp from 0.0.0.0/0" in messages)
    sec_group_rules_sdk = openstack_demo.network.find_security_group(
        sec_group_name).security_group_rules
    rule_port_found = False
    for rule_sdk in sec_group_rules_sdk:
        if(rule_sdk['port_range_min'] == rule_port and
                rule_sdk['port_range_max'] == rule_port):
            rule_port_found = True
    assert rule_port_found


def test_delete_rule_sec_group_demo(login, driver, sec_group_name,
                                    openstack_demo, new_sec_group_demo,
                                    new_sec_group_rule_demo, config):
    rule_port = new_sec_group_rule_demo.port_range_max
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'security_groups',
        new_sec_group_demo.id,
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#rules tr[data-object-id='{new_sec_group_rule_demo.id}']")
    assert len(rows) == 1
    rows[0].find_element_by_css_selector("td.actions_column").click()
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Deleted Rule: ALLOW IPv4 {rule_port}/tcp from 0.0.0.0/0"
           in messages)
    sec_group_rules_sdk = openstack_demo.network.find_security_group(
        sec_group_name).security_group_rules
    rule_port_found = False
    for rule_sdk in sec_group_rules_sdk:
        if (rule_sdk['port_range_min'] == rule_port and
                rule_sdk['port_range_max'] == rule_port):
            rule_port_found = True
    assert not(rule_port_found)
