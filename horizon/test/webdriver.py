#
#   Copyright (c) 2011-2013 Canonical Ltd.
#
#   This file is part of: SST (selenium-simple-test)
#   https://launchpad.net/selenium-simple-test
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import os

from selenium.common import exceptions
from selenium.webdriver.common import by
from selenium.webdriver.common import desired_capabilities as dc
from selenium.webdriver.remote import webelement

# Select the WebDriver to use based on the --selenium-phantomjs switch.
if os.environ.get('SELENIUM_PHANTOMJS'):
    from selenium.webdriver import PhantomJS as WebDriver
    desired_capabilities = dc.DesiredCapabilities.PHANTOMJS
else:
    from horizon.test.firefox_binary import WebDriver
    desired_capabilities = dc.DesiredCapabilities.FIREFOX


class WrapperFindOverride(object):
    """Mixin for overriding find_element methods."""

    def find_element(self, by=by.By.ID, value=None):
        repeat = range(2)
        for i in repeat:
            try:
                web_el = super(WrapperFindOverride, self).find_element(
                    by, value)
            except exceptions.NoSuchElementException:
                if i == repeat[-1]:
                    raise
        return WebElementWrapper(web_el.parent, web_el.id, (by, value),
                                 self)

    def find_elements(self, by=by.By.ID, value=None):
        repeat = range(2)
        for i in repeat:
            try:
                web_els = super(WrapperFindOverride, self).find_elements(
                    by, value)
            except exceptions.NoSuchElementException:
                if i == repeat[-1]:
                    raise
        result = []
        for index, web_el in enumerate(web_els):
            result.append(WebElementWrapper(web_el.parent, web_el.id,
                                            (by, value), self, index))
        return result


class WebElementWrapper(WrapperFindOverride, webelement.WebElement):
    """WebElement class wrapper.

    WebElement wrapper that catches the StaleElementReferenceException and
    tries to reload the element by sending request to its source element
    (element that created actual element) for reload, in case that source
    element needs to be reloaded as well, it asks its parent till web
    driver is reached. In case driver was reached and did not manage to
    find the element it is probable that programmer made a mistake and
    actualStaleElementReferenceException is raised.
    """

    def __init__(self, parent, id_, locator, src_element, index=None):
        super(WebElementWrapper, self).__init__(parent, id_)
        self.locator = locator
        self.src_element = src_element
        # in case element was looked up previously via find_elements
        # we need his position in the returned list
        self.index = index

    def _reload_element(self):
        """Method for starting reload process on current instance."""
        web_el = self.src_element.reload_request(self.locator, self.index)
        if not web_el:
            return False
        self._parent = web_el.parent
        self._id = web_el.id
        return True

    def _execute(self, command, params=None):
        """Overriding in order to catch StaleElementReferenceException."""
        # (schipiga): not need to use while True, trying to catch StaleElement
        # exception, because driver.implicitly_wait delegates this to browser.
        # Just we need to catch StaleElement exception, reload chain of element
        # parents and then to execute command again.
        repeat = range(20)
        for i in repeat:
            try:
                return super(WebElementWrapper, self)._execute(command, params)
            except (exceptions.StaleElementReferenceException,
                    exceptions.ElementClickInterceptedException):
                if i == repeat[-1]:
                    raise
                if not self._reload_element():
                    raise


class WebDriverWrapper(WrapperFindOverride, WebDriver):
    """Wrapper for webdriver to return WebElementWrapper on find_element."""
    def reload_request(self, locator, index):
        try:
            # element was found out via find_elements
            if index is not None:
                web_els = self.find_elements(*locator)
                web_el = web_els[index]
            else:
                web_el = self.find_element(*locator)
            return web_el
        except (exceptions.NoSuchElementException, IndexError):
            return False
