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
def flavor_name():
    return 'horizon_flavor_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_flavor(flavor_name, openstack_admin):
    flavor = openstack_admin.create_flavor(
        name=flavor_name,
        vcpus=1,
        ram=256,
        disk=1
    )
    yield flavor
    openstack_admin.delete_flavor(flavor_name)


@pytest.fixture
def clear_flavor(flavor_name, openstack_admin):
    yield None
    openstack_admin.delete_flavor(flavor_name)


def test_create_flavor(login, driver, flavor_name, openstack_admin,
                       config, clear_flavor):
    flavor_vcpus = 1
    flavor_ram = 256
    flavor_disk = 1

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'flavors',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Create Flavor").click()
    flavors_form = driver.find_element_by_css_selector("form .modal-content")
    flavors_form.find_element_by_id("id_name").send_keys(flavor_name)
    flavors_form.find_element_by_id("id_vcpus").send_keys(flavor_vcpus)
    flavors_form.find_element_by_id("id_memory_mb").send_keys(flavor_ram)
    flavors_form.find_element_by_id("id_disk_gb").send_keys(flavor_disk)
    flavors_form.find_element_by_css_selector(
        ".btn-primary[value='Create Flavor']").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Created new flavor "{flavor_name}".' in messages
    flavor_sdk = openstack_admin.compute.find_flavor(flavor_name)
    assert flavor_sdk is not None
    assert (flavor_sdk.vcpus == flavor_vcpus and
            flavor_sdk.ram == flavor_ram and
            flavor_sdk.disk == flavor_disk)


def test_delete_flavor(login, driver, flavor_name, new_flavor, config,
                       openstack_admin):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'flavors',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#flavors tr[data-display='{flavor_name}']")
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Flavor")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Success: Deleted Flavor: {flavor_name}" in messages
    assert openstack_admin.compute.find_flavor(flavor_name) is None
