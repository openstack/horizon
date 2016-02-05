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

from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.regions import baseregion
from openstack_dashboard.test.integration_tests.regions import menus


class TopBarRegion(baseregion.BaseRegion):
    _user_dropdown_menu_locator = (by.By.CSS_SELECTOR,
                                   '.nav.navbar-nav.navbar-right li.dropdown')
    _openstack_brand_locator = (by.By.CSS_SELECTOR, 'a[href*="/home/"]')

    _user_dropdown_project_locator = (
        by.By.CSS_SELECTOR,
        '.navbar-collapse > ul.navbar-nav:first-child li.dropdown')

    @property
    def user(self):
        return self._get_element(*self._user_dropdown_menu_locator)

    @property
    def brand(self):
        return self._get_element(*self._openstack_brand_locator)

    @property
    def user_dropdown_menu(self):
        src_elem = self._get_element(*self._user_dropdown_menu_locator)
        return menus.UserDropDownMenuRegion(self.driver,
                                            self.conf, src_elem)

    @property
    def is_logged_in(self):
        return self._is_element_visible(*self._user_dropdown_menu_locator)

    @property
    def user_dropdown_project(self):
        src_elem = self._get_element(*self._user_dropdown_project_locator)
        return menus.ProjectDropDownRegion(self.driver,
                                           self.conf, src_elem)
