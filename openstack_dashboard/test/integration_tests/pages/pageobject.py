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

from openstack_dashboard.test.integration_tests import basewebobject


class PageObject(basewebobject.BaseWebObject):
    """Base class for page objects."""

    def __init__(self, driver, conf):
        """Constructor."""
        super(PageObject, self).__init__(driver, conf)
        self.login_url = self.conf.dashboard.login_url
        self._page_title = None

    @property
    def page_title(self):
        return self.driver.title

    def is_the_current_page(self):
        self.assertIn(self._page_title, self.page_title,
                      "Expected to find %s in page title, instead found: %s"
                      % (self._page_title, self.page_title))
        return True

    def get_url_current_page(self):
        return self.driver.current_url

    def close_window(self):
        return self.driver.close()

    def is_nth_window_opened(self, n):
        return len(self.driver.window_handles) == n

    def switch_window(self, window_name=None, window_index=None):
        """Switches focus between the webdriver windows.
        Args:
        - window_name: The name of the window to switch to.
        - window_index: The index of the window handle to switch to.
        If the method is called without arguments it switches to the
         last window in the driver window_handles list.
        In case only one window exists nothing effectively happens.
        Usage:
        page.switch_window('_new')
        page.switch_window(2)
        page.switch_window()
        """

        if window_name is not None and window_index is not None:
            raise ValueError("switch_window receives the window's name or "
                             "the window's index, not both.")
        if window_name is not None:
            self.driver.switch_to.window(window_name)
        elif window_index is not None:
            self.driver.switch_to.window(
                self.driver.window_handles[window_index])
        else:
            self.driver.switch_to.window(self.driver.window_handles[-1])

    def go_to_previous_page(self):
        self.driver.back()

    def go_to_next_page(self):
        self.driver.forward()

    def refresh_page(self):
        self.driver.refresh()

    def go_to_login_page(self):
        self.driver.get(self.login_url)
        self.is_the_current_page()
