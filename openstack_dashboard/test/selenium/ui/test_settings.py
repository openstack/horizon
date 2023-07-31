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
from openstack_dashboard.test.selenium import widgets


def test_login(live_server, driver, mock_openstack_auth, mock_keystoneclient):
    # We go to a page that doesn't do more api calls.
    driver.get(live_server.url + '/settings')
    assert driver.title == "Login - OpenStack Dashboard"
    user_field = driver.find_element_by_id('id_username')
    user_field.clear()
    user_field.send_keys("user")
    pass_field = driver.find_element_by_id('id_password')
    pass_field.clear()
    pass_field.send_keys("password")
    button = driver.find_element_by_css_selector('div.panel-footer button.btn')
    button.click()
    errors = [m.text for m in
              driver.find_elements_by_css_selector('div.alert-danger p')]
    assert errors == []
    assert driver.title != "Login - OpenStack Dashboard"


def test_languages(live_server, driver, mock_openstack_auth,
                   mock_keystoneclient):
    user_settings = driver.find_element_by_id('user_settings_modal')
    language_options = user_settings.find_element_by_id('id_language')
    language_options.click()
    language_options.find_element_by_xpath("//option[@value='de']").click()
    user_settings.find_element_by_xpath('//*[@class="btn btn-primary"]').click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert "Success: Settings saved." in messages
    assert "Error" not in messages
# ToDo - mock API switch page language.
