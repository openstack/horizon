
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

from contextlib import contextmanager
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from django.conf import settings


@contextmanager
def no_wait(driver, config):
    driver.implicitly_wait(0)
    try:
        yield
    finally:
        driver.implicitly_wait(config.selenium.implicit_wait)


def wait_for_page_load(driver, config):
    """Wait for the page to finish loading."""

    with no_wait(driver, config):
        def loaded(_):
            result = driver.execute_script("return document.readyState")
            return result == "complete"
        wait = WebDriverWait(driver, config.selenium.page_timeout, 0.5)
        wait.until(loaded)


def test_region_login_selector(login, driver, config):
    """Check for the region selector on the login screen.

    Ensures that the region selection drop-down is displayed on the login
    screen with the correct options.
    """

    regions = settings.AVAILABLE_REGIONS
    if not regions:
        pytest.skip()
    login(None)
    select = driver.find_element_by_id('id_region')
    options = select.find_elements_by_tag_name('option')
    assert len(options) == len(regions)
    for (index, option), (url, name) in zip(enumerate(options), regions):
        assert option.text.strip() == name
        assert option.get_attribute('value') == str(index)


def test_region_login_user(login, driver, config):
    """Login into every region and confirm it is active."""

    regions = settings.AVAILABLE_REGIONS
    if not regions:
        pytest.skip()
    for url, name in regions:
        login('user', region=name)
        title = driver.find_element_by_xpath(config.theme.region_name_xpath)
        assert title.text == name


def test_region_switch(login, driver, config):
    regions = settings.AVAILABLE_REGIONS
    if not regions:
        pytest.skip()
    login('user', region=regions[0][1])
    for url, name in regions:
        wait_for_page_load(driver, config)
        time.sleep(0.5)  # we need slightly more time after page loads for js
        title = driver.find_element_by_xpath(config.theme.region_name_xpath)
        if title.text == name:
            continue
        title.click()
        region_list = driver.find_element_by_xpath(
            config.theme.region_list_xpath)
        region_link = region_list.find_element_by_link_text(name)
        region_link.click()

        with no_wait(driver, config):
            WebDriverWait(driver, config.selenium.page_timeout, 0.5).until(
                EC.visibility_of_element_located((By.ID, 'id_username'))
            )

        user_field = driver.find_element_by_id('id_username')
        user_field.send_keys(config.identity.username)
        pass_field = driver.find_element_by_id('id_password')
        pass_field.send_keys(config.identity.password)
        region_select = driver.find_element_by_id('id_region')
        select_opt = Select(region_select)
        select_opt.select_by_visible_text(name)
        button = driver.find_element_by_xpath('//*[@id="loginBtn"]')
        button.click()

        with no_wait(driver, config):
            WebDriverWait(driver, config.selenium.page_timeout, 0.5).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.modal-body > .loader')
                )
            )

        title = driver.find_element_by_xpath(config.theme.region_name_xpath)
        assert title.text == name
