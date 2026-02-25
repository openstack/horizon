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

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def new_flavor_region_one(flavor_name, openstack_admin_region_one):
    flavor = openstack_admin_region_one.create_flavor(
        name=flavor_name,
        vcpus=1,
        ram=256,
        disk=1
    )
    yield flavor
    openstack_admin_region_one.delete_flavor(flavor_name)


@pytest.fixture
def new_flavor_region_two(flavor_name, openstack_admin_region_two):
    flavor = openstack_admin_region_two.create_flavor(
        name=flavor_name,
        vcpus=1,
        ram=256,
        disk=1
    )
    yield flavor
    openstack_admin_region_two.delete_flavor(flavor_name)


@pytest.fixture
def clear_flavor_region_one(flavor_name, openstack_admin_region_one):
    yield None
    openstack_admin_region_one.delete_flavor(flavor_name)


@pytest.fixture
def clear_flavor_region_two(flavor_name, openstack_admin_region_two):
    yield None
    openstack_admin_region_two.delete_flavor(flavor_name)


def switch_to_services_region(driver, config, services_region):
    wait_for_page_ready(driver, config)
    switch_services_region_name = driver.find_element(
        By.XPATH, config.services_regions.region_name_xpath)
    if (switch_services_region_name.text ==
            config.services_regions.region_btn_text_pattern.format(
                region=services_region)):
        return
    switch_services_region_btn = driver.find_element(
        By.XPATH, config.services_regions.region_dropdown_xpath)
    widgets.select_from_dropdown(switch_services_region_btn, services_region)
    wait_for_page_ready(driver, config)
    driver.find_element(
        By.XPATH, config.services_regions.region_name_xpath)


def wait_for_page_ready(driver, config):
    wait = WebDriverWait(driver, config.selenium.page_timeout)
    wait.until(lambda d: d.execute_script(
        "return document.readyState") == "complete")
    wait.until(lambda d: d.execute_script(
        "return (typeof jQuery === 'undefined') || (jQuery.active === 0)"
    ))


def test_services_regions_switch_admin(require_multiple_regions, login, driver,
                                       config, env_services_regions):
    login('admin')
    for services_region in env_services_regions:
        switch_to_services_region(driver, config, services_region.id)
        switch_services_region_btn = driver.find_element(
            By.XPATH, config.services_regions.region_name_xpath)
        assert (switch_services_region_btn.text ==
                config.services_regions.region_btn_text_pattern.format(
                    region=services_region.id))


def test_services_regions_switch_demo(require_multiple_regions, login,
                                      driver, config, env_services_regions):
    login('user')
    for services_region in env_services_regions:
        switch_to_services_region(driver, config, services_region.id)
        switch_services_region_btn = driver.find_element(
            By.XPATH, config.services_regions.region_name_xpath)
        assert (switch_services_region_btn.text ==
                config.services_regions.region_btn_text_pattern.format(
                    region=services_region.id))


def test_services_regions_endpoints_in_service_catalog(
        require_multiple_regions, login, driver, config,
        env_services_regions, openstack_admin):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'api_access',
    ))
    driver.get(url)

    available_regions = [region.id for region in env_services_regions]

    for region in available_regions:
        switch_to_services_region(driver, config, region)
        service_url_tuples = [
            (e.name, e.url)
            for e in openstack_admin.identity.endpoints()
            if (e.region_id == region and
                e.interface == 'public')
        ]
        for service, url in service_url_tuples:
            # OpenStackSDK returns none name for keystone url
            if service is None and "keystone-public" in url:
                service = "keystone"
            # Strip path suffixes after the API version
            # (e.g. Swift's /v1/AUTH_%(tenant_id)s) since
            # only the base endpoint URL matters here.
            re_pattern = r"(.*?/v[\d.]+)/"
            match = re.search(re_pattern, url)
            if match:
                url = match.group(1)
            service_row = driver.find_element(
                By.CSS_SELECTOR,
                f"table#endpoints"
                f" tr[data-display='{service}']")
            assert service_row.find_element(
                By.XPATH, f".//*[contains(normalize-space(), '{url}')]")


def test_services_regions_resource_availability_region_one(
        login, driver, config, new_flavor_region_one):
    """Check if the resource is available only in region one"""

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'flavors',
    ))
    driver.get(url)
    switch_to_services_region(
        driver, config, config.services_regions.region_one_name)
    rows = driver.find_elements(
        By.CSS_SELECTOR,
        f"table#flavors tr[data-display='{new_flavor_region_one.name}']")
    assert len(rows) == 1
    switch_to_services_region(
        driver, config, config.services_regions.region_two_name)
    with widgets.no_wait(driver, config):
        rows = driver.find_elements(
            By.CSS_SELECTOR,
            f"table#flavors tr[data-display='{new_flavor_region_one.name}']")
        assert len(rows) == 0


def test_services_regions_resource_availability_region_two(
        login, driver, config, new_flavor_region_two):
    """Check if the resource is available only in region two"""

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'flavors',
    ))
    driver.get(url)
    switch_to_services_region(
        driver, config, config.services_regions.region_two_name)
    rows = driver.find_elements(
        By.CSS_SELECTOR,
        f"table#flavors tr[data-display='{new_flavor_region_two.name}']")
    assert len(rows) == 1
    switch_to_services_region(
        driver, config, config.services_regions.region_one_name)
    with widgets.no_wait(driver, config):
        rows = driver.find_elements(
            By.CSS_SELECTOR,
            f"table#flavors tr[data-display='{new_flavor_region_two.name}']")
        assert len(rows) == 0


def test_services_regions_create_resource_region_one(
        login, driver, config, flavor_name, openstack_admin_region_one,
        openstack_admin_region_two, clear_flavor_region_one):

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
    switch_to_services_region(
        driver, config, config.services_regions.region_one_name)
    driver.find_element(By.LINK_TEXT, "Create Flavor").click()
    flavors_form = driver.find_element(By.CSS_SELECTOR, "form .modal-content")
    flavors_form.find_element(By.ID, "id_name").send_keys(flavor_name)
    flavors_form.find_element(By.ID, "id_vcpus").send_keys(flavor_vcpus)
    flavors_form.find_element(By.ID, "id_memory_mb").send_keys(flavor_ram)
    flavors_form.find_element(By.ID, "id_disk_gb").send_keys(flavor_disk)
    flavors_form.find_element(
        By.CSS_SELECTOR, ".btn-primary[value='Create Flavor']").click()
    messages = widgets.get_and_dismiss_messages(driver, config)
    assert f'Success: Created new flavor "{flavor_name}".' in messages
    rows = driver.find_elements(
        By.CSS_SELECTOR,
        f"table#flavors tr[data-display='{flavor_name}']")
    assert len(rows) == 1

    flavor_sdk_region_one = (
        openstack_admin_region_one.compute.find_flavor(flavor_name))
    assert flavor_sdk_region_one is not None
    assert (flavor_sdk_region_one.vcpus == flavor_vcpus and
            flavor_sdk_region_one.ram == flavor_ram and
            flavor_sdk_region_one.disk == flavor_disk)
    flavor_sdk_region_two = (
        openstack_admin_region_two.compute.find_flavor(flavor_name))
    assert flavor_sdk_region_two is None


def test_services_regions_create_resource_region_two(
        login, driver, config, flavor_name, openstack_admin_region_one,
        openstack_admin_region_two, clear_flavor_region_two):

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
    switch_to_services_region(
        driver, config, config.services_regions.region_two_name)
    driver.find_element(By.LINK_TEXT, "Create Flavor").click()
    flavors_form = driver.find_element(By.CSS_SELECTOR, "form .modal-content")
    flavors_form.find_element(By.ID, "id_name").send_keys(flavor_name)
    flavors_form.find_element(By.ID, "id_vcpus").send_keys(flavor_vcpus)
    flavors_form.find_element(By.ID, "id_memory_mb").send_keys(flavor_ram)
    flavors_form.find_element(By.ID, "id_disk_gb").send_keys(flavor_disk)
    flavors_form.find_element(
        By.CSS_SELECTOR, ".btn-primary[value='Create Flavor']").click()
    messages = widgets.get_and_dismiss_messages(driver, config)
    assert f'Success: Created new flavor "{flavor_name}".' in messages
    rows = driver.find_elements(
        By.CSS_SELECTOR,
        f"table#flavors tr[data-display='{flavor_name}']")
    assert len(rows) == 1

    flavor_sdk_region_two = (
        openstack_admin_region_two.compute.find_flavor(flavor_name))
    assert flavor_sdk_region_two is not None
    assert (flavor_sdk_region_two.vcpus == flavor_vcpus and
            flavor_sdk_region_two.ram == flavor_ram and
            flavor_sdk_region_two.disk == flavor_disk)
    flavor_sdk_region_one = (
        openstack_admin_region_one.compute.find_flavor(flavor_name))
    assert flavor_sdk_region_one is None
