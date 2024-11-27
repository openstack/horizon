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

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def test_dashboard_help_redirection(login, driver, config):
    login('user')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'settings',
    ))
    driver.get(url)
    for step in config.theme.help_sequence:
        driver.find_element_by_xpath(step).click()
    available_windows = driver.window_handles
    assert len(available_windows) == 2
    driver.switch_to.window(available_windows[-1])
    WebDriverWait(driver, config.selenium.page_timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1')))
    assert config.dashboard.help_url in driver.current_url
    driver.close()
    driver.switch_to.window(available_windows[0])
