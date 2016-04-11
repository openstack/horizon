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


class BaseRegion(basewebobject.BaseWebObject):
    """Base class for region module

    * there is necessity to override some basic methods for obtaining elements
      as in content of regions it is required to do relative searches

    * self.driver cannot be easily replaced with self.src_elem because that
      would result in functionality loss, self.driver is WebDriver and
      src_elem is WebElement its usage is different.

    * this does not mean that self.src_elem cannot be self.driver
    """

    _default_src_locator = None

    # private methods
    def __init__(self, driver, conf, src_elem=None):
        super(BaseRegion, self).__init__(driver, conf)
        if self._default_src_locator:
            root = src_elem or driver
            src_elem = root.find_element(*self._default_src_locator)

        self.src_elem = src_elem or driver

        # variable for storing names of dynamic properties and
        # associated 'getters' - meaning method that are supplying
        # regions or web elements
        self._dynamic_properties = {}

    def __getattr__(self, name):
        """It is not possible to create property bounded just to object
        and not class at runtime, therefore it is necessary to
        override __getattr__ and make fake 'properties' by storing them in
        the protected attribute _dynamic_attributes and returning result
        of the method associated with the specified attribute.

        This way the feeling of having regions accessed as 'properties'
        is created, which is one of the requirement of page object pattern.
        """
        try:
            return self._dynamic_properties[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    def _get_element(self, *locator):
        return self.src_elem.find_element(*locator)

    def _get_elements(self, *locator):
        return self.src_elem.find_elements(*locator)
