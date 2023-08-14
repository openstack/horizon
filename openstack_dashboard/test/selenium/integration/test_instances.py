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
from selenium.common import exceptions

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def instance_name():
    return 'xhorizon_instance_%s' % uuidutils.generate_uuid(dashed=False)


@pytest.fixture
def new_instance_demo(instance_name, openstack_demo, config):

    instance = openstack_demo.create_server(
        instance_name,
        image=config.image.images_list[0],
        flavor=config.launch_instances.flavor,
        availability_zone=config.launch_instances.available_zone,
        network=config.network.external_network,
        wait=True,
    )
    yield instance
    openstack_demo.delete_server(instance_name)


@pytest.fixture
def new_instance_admin(instance_name, openstack_admin, config):

    instance = openstack_admin.create_server(
        instance_name,
        image=config.image.images_list,
        flavor=config.launch_instances.flavor,
        availability_zone=config.launch_instances.available_zone,
        network=config.network.external_network,
        wait=True,
    )
    yield instance
    openstack_admin.delete_server(instance_name)


@pytest.fixture
def clear_instance_demo(instance_name, openstack_demo):
    yield None
    openstack_demo.delete_server(
        instance_name,
        wait=True,
    )


@pytest.fixture
def clear_instance_admin(instance_name, openstack_admin):
    yield None
    openstack_admin.delete_server(
        instance_name,
        wait=True,
    )


def select_from_transfer_table(element, label):
    """Choose row from available Images, Flavors, Networks, etc.

    in launch tab for example: m1.tiny for Flavor, cirros for image, etc.
    """

    try:
        element.find_element_by_xpath(
            f"//*[text()='{label}']//ancestor::tr/td//*"
            f"[@class='btn btn-default fa fa-arrow-up']").click()
    except exceptions.NoSuchElementException:
        try:
            element.find_element_by_xpath(
                f"//*[text()='{label}']//ancestor::tr/td//*"
                f"[@class='btn btn-default fa fa-arrow-down']")
        except exceptions.NoSuchElementException:
            raise


def create_new_volume_during_create_instance(driver, required_state):
    create_new_volume_btn = widgets.find_already_visible_element_by_xpath(
        f"//*[@id='vol-create'][text()='{required_state}']", driver
    )
    create_new_volume_btn.click()


def delete_volume_on_instance_delete(driver, required_state):
    delete_volume_btn = widgets.find_already_visible_element_by_xpath(
        f"//label[contains(@ng-model, 'vol_delete_on_instance_delete')]"
        f"[text()='{required_state}']", driver)
    delete_volume_btn.click()


def test_create_instance_demo(login, driver, instance_name,
                              clear_instance_demo, config):
    image = config.launch_instances.image_name
    network = config.network.external_network
    flavor = config.launch_instances.flavor

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Launch Instance").click()
    wizard = driver.find_element_by_css_selector("wizard")
    navigation = wizard.find_element_by_css_selector("div.wizard-nav")
    widgets.find_already_visible_element_by_xpath(
        "//*[@id='name']", wizard).send_keys(instance_name)
    navigation.find_element_by_link_text("Networks").click()
    network_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceNetworkForm]"
    )
    select_from_transfer_table(network_table, network)
    navigation.find_element_by_link_text("Flavor").click()
    flavor_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceFlavorForm]"
    )
    select_from_transfer_table(flavor_table, flavor)
    navigation.find_element_by_link_text("Source").click()
    source_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceSourceForm]"
    )
#   create_new_volume_during_create_instance(source_table, "No")
    delete_volume_on_instance_delete(source_table, "Yes")
    select_from_transfer_table(source_table, image)
    wizard.find_element_by_css_selector(
        "button.btn-primary.finish").click()
    widgets.find_already_visible_element_by_xpath(
        f"//*[contains(text(),'{instance_name}')]//ancestor::tr/td"
        f"[contains(text(),'Active')]", driver)
    assert True


def test_create_instance_from_volume_demo(login, driver, instance_name,
                                          volume_name, new_volume_demo,
                                          clear_instance_demo, config):
    network = config.network.external_network
    flavor = config.launch_instances.flavor

    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Launch Instance").click()
    wizard = driver.find_element_by_css_selector("wizard")
    navigation = wizard.find_element_by_css_selector("div.wizard-nav")
    widgets.find_already_visible_element_by_xpath(
        "//*[@id='name']", wizard).send_keys(instance_name)
    navigation.find_element_by_link_text("Networks").click()
    network_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceNetworkForm]"
    )
    select_from_transfer_table(network_table, network)
    navigation.find_element_by_link_text("Flavor").click()
    flavor_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceFlavorForm]"
    )
    select_from_transfer_table(flavor_table, flavor)
    navigation.find_element_by_link_text("Source").click()
    source_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceSourceForm]"
    )
    select_boot_sources_type_tab = source_table.find_element_by_xpath(
        "//*[@id='boot-source-type']")
    select_boot_sources_type_tab.click()
    select_boot_sources_type_tab.find_element_by_xpath(
        "//option[@value='volume']").click()
    delete_volume_on_instance_delete(source_table, "No")
    select_from_transfer_table(source_table, volume_name)
    wizard.find_element_by_css_selector("button.btn-primary.finish").click()
    widgets.find_already_visible_element_by_xpath(
        f"//*[contains(text(),'{instance_name}')]//ancestor::tr/td\
        [contains(text(),'Active')]", driver)
    assert True


def test_delete_instance_demo(login, driver, instance_name,
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
    widgets.select_from_dropdown(actions_column, " Delete Instance")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Info: Scheduled deletion of Instance: {instance_name}" in messages


# Admin tests


def test_create_instance_admin(login, driver, instance_name,
                               clear_instance_admin, config):
    image = config.launch_instances.image_name
    network = config.network.external_network
    flavor = config.launch_instances.flavor

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'project',
        'instances',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Launch Instance").click()
    wizard = driver.find_element_by_css_selector("wizard")
    navigation = wizard.find_element_by_css_selector("div.wizard-nav")
    widgets.find_already_visible_element_by_xpath(
        "//*[@id='name']", wizard).send_keys(instance_name)
    navigation.find_element_by_link_text("Networks").click()
    network_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceNetworkForm]"
    )
    select_from_transfer_table(network_table, network)
    navigation.find_element_by_link_text("Flavor").click()
    flavor_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceFlavorForm]"
    )
    select_from_transfer_table(flavor_table, flavor)
    navigation.find_element_by_link_text("Source").click()
    source_table = wizard.find_element_by_css_selector(
        "ng-include[ng-form=launchInstanceSourceForm]"
    )
#   create_new_volume_during_create_instance(source_table, "No")
    delete_volume_on_instance_delete(source_table, "Yes")
    select_from_transfer_table(source_table, image)
    wizard.find_element_by_css_selector(
        "button.btn-primary.finish").click()
    widgets.find_already_visible_element_by_xpath(
        f"//*[contains(text(),'{instance_name}')]//ancestor::tr/td\
        [contains(text(),'Active')]", driver)
    assert True


def test_delete_instance_admin(login, driver, instance_name,
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
    widgets.select_from_dropdown(actions_column, " Delete Instance")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert f"Info: Scheduled deletion of Instance: {instance_name}" in messages
