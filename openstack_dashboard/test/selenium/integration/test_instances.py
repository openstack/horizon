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

import time

import pytest
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from oslo_utils import uuidutils

from openstack_dashboard.test.selenium import widgets


@pytest.fixture(params=[(1, False)])
def new_instance_admin(complete_default_test_network, request, instance_name,
                       openstack_admin, config):

    count = request.param[0]
    auto_ip_param = request.param[1]
    instance = openstack_admin.create_server(
        instance_name,
        image=config.image.images_list[0],
        flavor=config.launch_instances.flavor,
        availability_zone=config.launch_instances.available_zone,
        network=complete_default_test_network.name,
        auto_ip=auto_ip_param,
        wait=True,
        max_count=count,
    )
    yield instance
    if count > 1:
        for instance in range(0, count):
            openstack_admin.delete_server(f"{instance_name}-{instance+1}")
    else:
        openstack_admin.delete_server(instance_name)


@pytest.fixture
def clear_instance_admin(instance_name, openstack_admin):
    yield None
    openstack_admin.delete_server(
        instance_name,
        wait=True,
    )


def wait_for_angular_readiness_instance_source(driver):
    driver.set_script_timeout(10)
    driver.execute_async_script("""
    var callback = arguments[arguments.length - 1];
    var element = document.querySelector(\
    'div[ng-if="model.newInstanceSpec.vol_create == true"] .btn-group');
    if (!window.angular) {
    callback(false)
    }
    if (angular.getTestability) {
    angular.getTestability(element).whenStable(function(){callback(true)});
    } else {
    if (!angular.element(element).injector()) {
    callback(false)
    }
    var browser = angular.element(element).injector().get('$browser');
    browser.notifyWhenNoOutstandingRequests(function(){callback(true)});
    };""")


def create_new_volume_during_create_instance(driver, required_state):
    create_new_volume_btn = widgets.find_already_visible_element_by_xpath(
        f".//*[@id='vol-create'][text()='{required_state}']", driver
    )
    create_new_volume_btn.click()


def delete_volume_on_instance_delete(driver, required_state):
    delete_volume_btn = widgets.find_already_visible_element_by_xpath(
        f".//label[contains(@ng-model, 'vol_delete_on_instance_delete')]"
        f"[text()='{required_state}']", driver)
    delete_volume_btn.click()


def apply_instance_name_filter(driver, config, name_pattern):
    # the text in filter field is rewritten after fully loaded page
    # repeated check
    for attempt in range(3):
        filter_field = driver.find_element_by_css_selector(
            "input[name='instances__filter__q']")
        filter_field.clear()
        filter_field.send_keys(name_pattern)
        driver.find_element_by_id("instances__action_filter").click()
        WebDriverWait(driver, config.selenium.page_timeout).until(
            EC.invisibility_of_element_located(filter_field))
        try:
            driver.find_element_by_css_selector(
                f".table_search input[value='{name_pattern}']")
            break
        except(exceptions.NoSuchElementException):
            time.sleep(3)


def wait_for_instance_is_deleted(openstack, instance_name):
    for attempt in range(10):
        if openstack.compute.find_server(instance_name) is None:
            break
        else:
            time.sleep(3)


def test_create_instance_demo(complete_default_test_network, login, driver,
                              instance_name, openstack_demo,
                              clear_instance_demo, config):
    image = config.image.images_list[0]
    network = complete_default_test_network.name
    flavor = config.launch_instances.flavor

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    launch_instance_btn = driver.find_element_by_link_text(
        "Launch Instance")
    launch_instance_btn.click()
    wizard = driver.find_element_by_css_selector("wizard")
    navigation = wizard.find_element_by_css_selector("div.wizard-nav")
    widgets.find_already_visible_element_by_xpath(
        ".//*[@id='name']", wizard).send_keys(instance_name)
    navigation.find_element_by_link_text("Networks").click()
    network_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceNetworkForm]"
    )
    widgets.select_from_transfer_table(network_table, network)
    navigation.find_element_by_link_text("Flavor").click()
    flavor_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceFlavorForm]"
    )
    widgets.select_from_transfer_table(flavor_table, flavor)
    navigation.find_element_by_link_text("Source").click()
    wait_for_angular_readiness_instance_source(driver)
    source_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceSourceForm]"
    )
#   create_new_volume_during_create_instance(source_table, "No")
    delete_volume_on_instance_delete(source_table, "Yes")
    widgets.select_from_transfer_table(source_table, image)
    wizard.find_element_by_css_selector(
        "button.btn-primary.finish").click()

#   For create instance - message appears earlier than the page is refreshed.
#   We are unable to ensure that the message will be captured.
#   Checking of message is skipped, we wait for refresh page
#   and then result is checked.
#    JJ

    WebDriverWait(driver, config.selenium.page_timeout).until(
        EC.invisibility_of_element_located(launch_instance_btn))
    assert openstack_demo.compute.find_server(instance_name) is not None


def test_create_instance_from_volume_demo(complete_default_test_network, login,
                                          driver, volume_name, new_volume_demo,
                                          clear_instance_demo, config,
                                          openstack_demo, instance_name):
    network = complete_default_test_network.name
    flavor = config.launch_instances.flavor
    volume_name = volume_name[0]

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    launch_instance_btn = driver.find_element_by_link_text(
        "Launch Instance")
    launch_instance_btn.click()
    wizard = driver.find_element_by_css_selector("wizard")
    navigation = wizard.find_element_by_css_selector("div.wizard-nav")
    widgets.find_already_visible_element_by_xpath(
        ".//*[@id='name']", wizard).send_keys(instance_name)
    navigation.find_element_by_link_text("Networks").click()
    network_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceNetworkForm]"
    )
    widgets.select_from_transfer_table(network_table, network)
    navigation.find_element_by_link_text("Flavor").click()
    flavor_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceFlavorForm]"
    )
    widgets.select_from_transfer_table(flavor_table, flavor)
    navigation.find_element_by_link_text("Source").click()
    wait_for_angular_readiness_instance_source(driver)
    source_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceSourceForm]"
    )
    select_boot_sources_type_tab = source_table.find_element_by_id(
        "boot-source-type")
    select_boot_sources_type_tab.click()
    select_boot_sources_type_tab.find_element_by_css_selector(
        "option[value='volume']").click()
    delete_volume_on_instance_delete(source_table, "No")
    widgets.select_from_transfer_table(source_table, volume_name)
    wizard.find_element_by_css_selector("button.btn-primary.finish").click()
    WebDriverWait(driver, config.selenium.page_timeout).until(
        EC.invisibility_of_element_located(launch_instance_btn))
    assert openstack_demo.compute.find_server(instance_name) is not None


def test_delete_instance_demo(login, driver, instance_name, openstack_demo,
                              new_instance_demo, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#instances tr[data-display='{instance_name}']"
    )
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Instance")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Info: Scheduled deletion of Instance: {instance_name}" in messages
    wait_for_instance_is_deleted(openstack_demo, instance_name)
    assert openstack_demo.compute.find_server(instance_name) is None


@pytest.mark.parametrize('new_instance_demo', [(2, False)],
                         indirect=True)
def test_instance_pagination_demo(login, driver, instance_name,
                                  new_instance_demo, change_page_size_demo,
                                  config):
    """This test checks instance pagination for demo user

    Steps:
    1) Login to Horizon Dashboard as demo user
    2) Create 2 instances
    3) Navigate to user settings page
    4) Change 'Items Per Page' value to 1
    5) Go to Instances page
    6) Check that only 'Next' link is available, only one instance is
       available (and it has correct name) on the first page
    7) Click 'Next' and check that on the second page only one instance is
       available (and it has correct name), there is no 'Next' link on page
    8) Click 'Prev' and check result (should be the same as for step6)
    9) Go to user settings page and restore 'Items Per Page' to default
    10) Delete created instances
    """
    items_per_page = 1
    instance_count = 2
    instance_list = [f"{instance_name}-{item}"
                     for item in range(1, instance_count + 1)]
    first_page_definition = widgets.TableDefinition(next=True, prev=False,
                                                    count=items_per_page,
                                                    names=[instance_list[1]])
    second_page_definition = widgets.TableDefinition(next=False, prev=True,
                                                     count=items_per_page,
                                                     names=[instance_list[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances'
    ))
    driver.get(url)
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert first_page_definition == current_table_status
    # Turning to next page
    driver.find_element_by_link_text("Next »").click()
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[0],
                                                    sorting=True)
    assert second_page_definition == current_table_status
    # Turning back to previous page
    driver.find_element_by_link_text("« Prev").click()
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert first_page_definition == current_table_status


@pytest.mark.parametrize('new_instance_demo', [(2, False)],
                         indirect=True)
def test_instances_pagination_and_filtration_demo(login, driver, instance_name,
                                                  new_instance_demo,
                                                  change_page_size_demo,
                                                  config):
    """This test checks instance pagination and filtration

        Steps:
        1) Login to Horizon Dashboard as demo user
        2) Create 2 instances
        3) Go to user settings page
        4) Change 'Items Per Page' value to 1
        5) Go to Instances page
        6) Check filter by Name of the first and the second instance in order
           to have one instance in the list (and it should have correct name)
           and no 'Next' link is available
        7) Check filter by common part of Name of in order to have one instance
           in the list (and it should have correct name) and 'Next' link is
           available on the first page and is not available on the second page
        9) Go to user settings page and restore 'Items Per Page'
        10) Delete created instances

        """
    items_per_page = 1
    instance_count = 2
    instance_list = [f"{instance_name}-{item}"
                     for item in range(1, instance_count + 1)]
    filter_instance1_def = widgets.TableDefinition(next=False, prev=False,
                                                   count=items_per_page,
                                                   names=[instance_list[1]])
    filter_instance2_def = widgets.TableDefinition(next=False, prev=False,
                                                   count=items_per_page,
                                                   names=[instance_list[0]])
    common_filter_page1_def = widgets.TableDefinition(next=True, prev=False,
                                                      count=items_per_page,
                                                      names=[instance_list[1]])
    common_filter_page2_def = widgets.TableDefinition(next=False, prev=True,
                                                      count=items_per_page,
                                                      names=[instance_list[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances'
    ))
    driver.get(url)
    driver.find_element_by_css_selector(
        "button[class='btn btn-default dropdown-toggle']").click()
    # set filter by instance_name
    driver.find_element_by_css_selector(
        "a[data-select-value='name']").click()
    apply_instance_name_filter(driver, config, instance_list[1])
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert filter_instance1_def == current_table_status
    apply_instance_name_filter(driver, config, instance_list[0])
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[0],
                                                    sorting=True)
    assert filter_instance2_def == current_table_status
    apply_instance_name_filter(driver, config, instance_name)
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert common_filter_page1_def == current_table_status
    # Turning to next page
    driver.find_element_by_link_text("Next »").click()
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[0],
                                                    sorting=True)
    assert common_filter_page2_def == current_table_status


@pytest.mark.parametrize('new_instance_demo', [(2, False)],
                         indirect=True)
def test_filter_instances_demo(login, driver, instance_name,
                               new_instance_demo, config):
    """This test checks filtering of instances by Instance Name

        Steps:
        1) Login to Horizon dashboard as regular user
        2) Create 2 instances
        3) Go to Instances Page
        5) Use filter by Instance Name
        6) Check that filtered table has one instance only (which name is equal
           to filter value) and no other instances in the table
        7) Set nonexistent instance name. Check that 0 rows are displayed
        8) Delete both instances
        """
    instance_count = 2
    instance_list = [f"{instance_name}-{item}"
                     for item in range(1, instance_count + 1)]
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances'
    ))
    driver.get(url)
    driver.find_element_by_css_selector(
        "button[class='btn btn-default dropdown-toggle']").click()
    # set filter by instance_name
    driver.find_element_by_css_selector(
        "a[data-select-value='name']").click()
    apply_instance_name_filter(driver, config, instance_list[1])
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert (vars(current_table_status)['names'][0] == instance_list[1] and
            vars(current_table_status)['count'] == 1)
    # Generate random non existent image name
    random_instance_name = 'horizon_instance_%s' % \
                           uuidutils.generate_uuid(dashed=False)
    apply_instance_name_filter(driver, config, random_instance_name)
    no_items_present = driver.find_element_by_xpath(
        "//td[text()='No items to display.']")
    assert no_items_present


# Admin tests


def test_create_instance_admin(complete_default_test_network, login, driver,
                               instance_name, openstack_admin,
                               clear_instance_admin, config):
    image = config.image.images_list[0]
    network = complete_default_test_network.name
    flavor = config.launch_instances.flavor

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    launch_instance_btn = driver.find_element_by_link_text(
        "Launch Instance")
    launch_instance_btn.click()
    wizard = driver.find_element_by_css_selector("wizard")
    navigation = wizard.find_element_by_css_selector("div.wizard-nav")
    widgets.find_already_visible_element_by_xpath(
        ".//*[@id='name']", wizard).send_keys(instance_name)
    navigation.find_element_by_link_text("Networks").click()
    network_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceNetworkForm]"
    )
    widgets.select_from_transfer_table(network_table, network)
    navigation.find_element_by_link_text("Flavor").click()
    flavor_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceFlavorForm]"
    )
    widgets.select_from_transfer_table(flavor_table, flavor)
    navigation.find_element_by_link_text("Source").click()
    wait_for_angular_readiness_instance_source(driver)
    source_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceSourceForm]"
    )
#   create_new_volume_during_create_instance(source_table, "No")
    delete_volume_on_instance_delete(source_table, "Yes")
    widgets.select_from_transfer_table(source_table, image)
    wizard.find_element_by_css_selector(
        "button.btn-primary.finish").click()
    WebDriverWait(driver, config.selenium.page_timeout).until(
        EC.invisibility_of_element_located(launch_instance_btn))
    assert openstack_admin.compute.find_server(instance_name) is not None


def test_delete_instance_admin(login, driver, instance_name, openstack_admin,
                               new_instance_admin, config):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#instances tr[data-display='{instance_name}']"
    )
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Instance")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Info: Scheduled deletion of Instance: {instance_name}" in messages
    wait_for_instance_is_deleted(openstack_admin, instance_name)
    assert openstack_admin.compute.find_server(instance_name) is None


@pytest.mark.parametrize('new_instance_admin', [(2, False)],
                         indirect=True)
def test_instance_pagination_admin(login, driver, instance_name,
                                   new_instance_admin, change_page_size_admin,
                                   config):
    """This test checks instance pagination for admin user

    Steps:
    1) Login to Horizon Dashboard as admin user
    2) Create 2 instances
    3) Navigate to user settings page
    4) Change 'Items Per Page' value to 1
    5) Go to Instances page
    6) Check that only 'Next' link is available, only one instance is
       available (and it has correct name) on the first page
    7) Click 'Next' and check that on the second page only one instance is
       available (and it has correct name), there is no 'Next' link on page
    8) Click 'Prev' and check result (should be the same as for step6)
    9) Go to user settings page and restore 'Items Per Page' to default
    10) Delete created instances
    """
    items_per_page = 1
    instance_count = 2
    instance_list = [f"{instance_name}-{item}"
                     for item in range(1, instance_count + 1)]
    first_page_definition = widgets.TableDefinition(next=True, prev=False,
                                                    count=items_per_page,
                                                    names=[instance_list[1]])
    second_page_definition = widgets.TableDefinition(next=False, prev=True,
                                                     count=items_per_page,
                                                     names=[instance_list[0]])
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances'
    ))
    driver.get(url)
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert first_page_definition == current_table_status
    # Turning to next page
    driver.find_element_by_link_text("Next »").click()
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[0],
                                                    sorting=True)
    assert second_page_definition == current_table_status
    # Turning back to previous page
    driver.find_element_by_link_text("« Prev").click()
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert first_page_definition == current_table_status


@pytest.mark.parametrize('new_instance_admin', [(2, False)],
                         indirect=True)
def test_instances_pagination_and_filtration_admin(login, driver, instance_name,
                                                   new_instance_admin,
                                                   change_page_size_admin,
                                                   config):
    """This test checks instance pagination and filtration

        Steps:
        1) Login to Horizon Dashboard as admin user
        2) Create 2 instances
        3) Go to user settings page
        4) Change 'Items Per Page' value to 1
        5) Go to Instances page
        6) Check filter by Name of the first and the second instance in order
           to have one instance in the list (and it should have correct name)
           and no 'Next' link is available
        7) Check filter by common part of Name of in order to have one instance
           in the list (and it should have correct name) and 'Next' link is
           available on the first page and is not available on the second page
        9) Go to user settings page and restore 'Items Per Page'
        10) Delete created instances

        """
    items_per_page = 1
    instance_count = 2
    instance_list = [f"{instance_name}-{item}"
                     for item in range(1, instance_count + 1)]
    filter_instance1_def = widgets.TableDefinition(next=False, prev=False,
                                                   count=items_per_page,
                                                   names=[instance_list[1]])
    filter_instance2_def = widgets.TableDefinition(next=False, prev=False,
                                                   count=items_per_page,
                                                   names=[instance_list[0]])
    common_filter_page1_def = widgets.TableDefinition(next=True, prev=False,
                                                      count=items_per_page,
                                                      names=[instance_list[1]])
    common_filter_page2_def = widgets.TableDefinition(next=False, prev=True,
                                                      count=items_per_page,
                                                      names=[instance_list[0]])

    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances'
    ))
    driver.get(url)
    driver.find_element_by_css_selector(
        "button[class='btn btn-default dropdown-toggle']").click()
    # set filter by instance_name
    driver.find_element_by_css_selector(
        "a[data-select-value='name']").click()
    apply_instance_name_filter(driver, config, instance_list[1])
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert filter_instance1_def == current_table_status
    apply_instance_name_filter(driver, config, instance_list[0])
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[0],
                                                    sorting=True)
    assert filter_instance2_def == current_table_status
    apply_instance_name_filter(driver, config, instance_name)
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert common_filter_page1_def == current_table_status
    # Turning to next page
    driver.find_element_by_link_text("Next »").click()
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[0],
                                                    sorting=True)
    assert common_filter_page2_def == current_table_status


@pytest.mark.parametrize('new_instance_admin', [(2, False)],
                         indirect=True)
def test_filter_instances_admin(login, driver, instance_name,
                                new_instance_admin, config):
    """This test checks filtering of instances by Instance Name

        Steps:
        1) Login to Horizon dashboard as admin user
        2) Create 2 instances
        3) Go to Instances Page
        5) Use filter by Instance Name
        6) Check that filtered table has one instance only (which name is equal
           to filter value) and no other instances in the table
        7) Set nonexistent instance name. Check that 0 rows are displayed
        8) Delete both instances
        """
    instance_count = 2
    instance_list = [f"{instance_name}-{item}"
                     for item in range(1, instance_count + 1)]
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances'
    ))
    driver.get(url)
    driver.find_element_by_css_selector(
        "button[class='btn btn-default dropdown-toggle']").click()
    # set filter by instance_name
    driver.find_element_by_css_selector(
        "a[data-select-value='name']").click()
    apply_instance_name_filter(driver, config, instance_list[1])
    current_table_status = widgets.get_table_status(driver, "instances",
                                                    instance_list[1],
                                                    sorting=True)
    assert (vars(current_table_status)['names'][0] == instance_list[1] and
            vars(current_table_status)['count'] == 1)
    # Generate random non existent image name
    random_instance_name = 'horizon_instance_%s' % \
                           uuidutils.generate_uuid(dashed=False)
    apply_instance_name_filter(driver, config, random_instance_name)
    no_items_present = driver.find_element_by_xpath(
        "//td[text()='No items to display.']")
    assert no_items_present
