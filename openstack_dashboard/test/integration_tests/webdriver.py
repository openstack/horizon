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
import time

from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.common import desired_capabilities as dc
from selenium.webdriver.remote import webelement


class ElementNotReloadableException(Exception):
    """Raised when reload is not possible."""
    pass


class WrapperFindOverride(object):
    """Mixin for overriding find_element methods."""

    def find_element(self, by=by.By.ID, value=None):
        web_el = super(WrapperFindOverride, self).find_element(by, value)
        return WebElementWrapper(web_el.parent, web_el.id, (by, value), self)

    def find_elements(self, by=by.By.ID, value=None):
        web_els = super(WrapperFindOverride, self).find_elements(by, value)
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
    element needs to be reloaded as well, it asks its parent till web driver
    is reached. In case driver was reached and did not manage to find the
    element it is probable that programmer made a mistake and actual
    StaleElementReferenceException is raised.
    """

    STALE_ELEMENT_REFERENCE_WAIT = 0.5
    STALE_ELEMENT_REFERENCE_MAX_TRY = 10

    def __init__(self, parent, id_, locator, src_element, index=None):
        super(WebElementWrapper, self).__init__(parent, id_)
        self.locator = locator
        self.src_element = src_element

        # StaleElementReferenceException occurrence counter
        self.stale_reference_occurrence = 0

        # storing if web element reload succeed or not
        # in case of fail StaleElementReferenceException is raised
        self.reload_failed = False

        # in case element was looked up previously via find_elements
        # we need his position in the returned list
        self.index = index

        # if reloading of some other web element is in progress
        # StaleElementReferenceException is not raised within current context
        self.web_element_reload = False

    def reload_request(self, locator, index=None):
        self.web_element_reload = True
        try:
            # element was found out via find_elements
            if index is not None:
                web_els = self.src_element.find_elements(*locator)
                web_el = web_els[index]
            else:
                web_el = self.src_element.find_element(*locator)
        except (exceptions.NoSuchElementException, IndexError):
            return False

        self.web_element_reload = False
        return web_el

    def _reload_element(self):
        """Method for starting reload process on current instance."""
        web_el = self.src_element.reload_request(self.locator, self.index)
        if not web_el:
            return
        self._parent = web_el.parent
        self._id = web_el.id

    def _execute(self, command, params=None):
        """Overriding in order to catch StaleElementReferenceException."""
        result = None
        while True:
            try:
                result = super(WebElementWrapper, self)._execute(command,
                                                                 params)
                break
            except exceptions.StaleElementReferenceException:

                # in case we reach the limit STALE_ELEMENT_REFERENCE_MAX_TRY
                # it is very probable that it is programmer fault
                if self.reload_failed or self.stale_reference_occurrence \
                        > self.STALE_ELEMENT_REFERENCE_MAX_TRY:
                    raise

                # this is either programmer fault
                # (bad logic in accessing elements)
                # or web page content is been loaded via ajax, let's go with
                # the second one and wait STALE_ELEMENT_REFERENCE_WAIT till
                # the assumed page content is loaded and try
                # to execute the whole process
                # STALE_ELEMENT_REFERENCE_MAX_TRY times in case of failures
                time.sleep(self.STALE_ELEMENT_REFERENCE_WAIT)

                # try to reload the web element
                # if result is false it means that request has gone to the
                # driver and he did not find the element -> must be programmer
                # fault, because it seems we are on entirely different page
                try:
                    self._reload_element()
                except ElementNotReloadableException:

                    # In case this element was responsible only for loading
                    #  some other element raise the exception further
                    if self.web_element_reload:
                        raise
                    else:
                        self.reload_failed = True

                # increment occurrences
                self.stale_reference_occurrence += 1

        # reset counter
        self.stale_reference_occurrence = 0
        return result


class WebDriverWrapper(WrapperFindOverride, webdriver.Firefox):
    """Wrapper for webdriver to return WebElementWrapper on find_element."""
    def __init__(self, logging_prefs=None, capabilities=None, **kwargs):
        if capabilities is None:
            capabilities = dc.DesiredCapabilities.FIREFOX
        if logging_prefs is None:
            logging_prefs = {'browser': 'ALL'}
        capabilities['loggingPrefs'] = logging_prefs
        super(WebDriverWrapper, self).__init__(capabilities=capabilities,
                                               **kwargs)

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
            raise ElementNotReloadableException()
