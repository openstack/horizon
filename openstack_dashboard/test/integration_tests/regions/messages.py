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

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.regions import baseregion

ERROR = 'alert-danger'
INFO = 'alert-info'
SUCCESS = 'alert-success'


class MessageRegion(baseregion.BaseRegion):
    _close_locator = (by.By.CSS_SELECTOR, 'a.close')

    def _msg_locator(self, level):
        return (by.By.CSS_SELECTOR, 'div.alert.%s' % level)

    def __init__(self, driver, conf, level=SUCCESS):
        self._default_src_locator = self._msg_locator(level)
        # NOTE(tsufiev): we cannot use self._turn_off_implicit_wait() at this
        # point, because the instance is not initialized by ancestor's __init__
        driver.implicitly_wait(0)
        try:
            super(MessageRegion, self).__init__(driver, conf)
        except NoSuchElementException:
            self.src_elem = None
        finally:
            self._turn_on_implicit_wait()

    def exists(self):
        return self._is_element_displayed(self.src_elem)

    def close(self):
        self._get_element(*self._close_locator).click()
