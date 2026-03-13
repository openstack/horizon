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

from openstack_dashboard import api
from openstack_dashboard.test.selenium import widgets


@pytest.fixture()
def metadata_modal(live_server, driver, user, dashboard_data):
    obj = mock.patch.object
    with (
        obj(api.glance, 'image_list_detailed') as image_list,
        obj(api.glance, 'image_get') as image_get,
        obj(api.glance, 'metadefs_namespace_full_list') as namespace_list,
    ):
        image_list.return_value = (
            dashboard_data.images.list()[0:2],
            False,
            False,
        )
        image_get.return_value = dashboard_data.images.list()[0]
        namespace_list.return_value = (
            dashboard_data.metadata_defs.list(),
            False,
            False,
        )
        driver.get(live_server.url + '/project/images/')
        actions_column = driver.find_element(By.CSS_SELECTOR, 'table')
        widgets.select_from_dropdown(actions_column, "Update Metadata")
        modal = driver.find_element(By.CSS_SELECTOR, 'div.modal-content')
        yield modal
        modal.find_element(By.CSS_SELECTOR, 'button.cancel').click()


def test_image_metadata_custom_property(driver, config, metadata_modal):
    """Create and remove a custom property field."""

    uls = metadata_modal.find_elements(By.CSS_SELECTOR,
                                       'ul.metadata-list-group')
    available_props_ul = uls[0]
    active_props_ul = uls[1]
    custom_li = available_props_ul.find_element(By.CSS_SELECTOR,
                                                'li.list-group-item')
    custom_li.find_element(
        By.CSS_SELECTOR, 'input[name="customItem"]'
    ).send_keys("custom_property")
    custom_li.find_element(By.CSS_SELECTOR, 'button.btn-primary').click()
    label = active_props_ul.find_element(
        By.XPATH, './/span[normalize-space()="custom_property"]')
    input_field = label.parent.find_element(By.CSS_SELECTOR, 'input')
    input_field.send_keys("custom value")
    label.parent.find_element(By.CSS_SELECTOR, 'a.btn').click()
    with widgets.no_wait(driver, config):
        labels = active_props_ul.find_elements(
            By.XPATH, './/span[normalize-space()="custom_property"]')
    assert len(labels) == 0


def test_image_metadata_tree_property(driver, config, metadata_modal):
    """Navigate the tree of properties and add and remove one of them."""

    uls = metadata_modal.find_elements(By.CSS_SELECTOR,
                                       'ul.metadata-list-group')
    available_props_ul = uls[0]
    active_props_ul = uls[1]
    namespace = available_props_ul.find_element(
        By.XPATH, './/span[normalize-space()="Namespace 1"]')
    namespace.click()
    prop = available_props_ul.find_element(By.XPATH,
                                           './/*[normalize-space()="mocks"]')
    prop.parent.find_element(By.CSS_SELECTOR, 'a.btn').click()
    label = active_props_ul.find_element(
        By.XPATH, './/span[normalize-space()="cpu_mock:mock"]')
    input_field = label.parent.find_element(By.CSS_SELECTOR, 'input')
    input_field.send_keys("123")
    label.parent.find_element(By.CSS_SELECTOR, 'a.btn').click()
    with widgets.no_wait(driver, config):
        labels = active_props_ul.find_elements(
            By.XPATH, './/span[normalize-space()="cpu_mock:mock"]')
    assert len(labels) == 0


def test_image_metadata_available_filter(driver, config, metadata_modal):
    """Filter the list of available properties."""

    filter_input = metadata_modal.find_element(
        By.CSS_SELECTOR, 'input[ng-model="ctrl.filterText.available"]')
    filter_input.click()
    filter_input.send_keys("cpu")
    uls = metadata_modal.find_elements(By.CSS_SELECTOR,
                                       'ul.metadata-list-group')
    available_props_ul = uls[0]
    namespace = available_props_ul.find_element(
        By.XPATH, './/span[normalize-space()="Namespace 1"]')
    namespace.click()
    props = available_props_ul.find_elements(By.CSS_SELECTOR, 'li span.leaf')
    assert len(props) == 1


def test_image_metadata_active_filter(driver, config, metadata_modal):
    """Filter the list of active properties."""

    filter_input = metadata_modal.find_element(
        By.CSS_SELECTOR, 'input[ng-model="ctrl.filterText.existing"]')
    filter_input.click()
    filter_input.send_keys("test")
    uls = metadata_modal.find_elements(By.CSS_SELECTOR,
                                       'ul.metadata-list-group')
    active_props_ul = uls[1]
    props = active_props_ul.find_elements(
        By.CSS_SELECTOR, 'li:not(.ng-hide) span.input-group-addon')
    assert len(props) == 1
