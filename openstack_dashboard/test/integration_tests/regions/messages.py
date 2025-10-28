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

ERROR = 'alert-danger'
INFO = 'alert-info'
SUCCESS = 'alert-success'
WARNING = 'alert-warning'


class MessageRegion(baseregion.BaseRegion):
    _close_locator = (by.By.CSS_SELECTOR, 'a.close')

    def __init__(self, driver, conf, src_elem):
        self.src_elem = src_elem
        self.message_class = self.get_message_class()

    def exists(self):
        return self._is_element_displayed(self.src_elem)

    def close(self):
        self._get_element(*self._close_locator).click()

    def get_message_class(self):
        message_class = self.src_elem.get_attribute("class")
        if SUCCESS in message_class:
            return SUCCESS
        elif ERROR in message_class:
            return ERROR
        elif INFO in message_class:
            return INFO
        elif WARNING in message_class:
            return WARNING
        else:
            return "Unknown"
