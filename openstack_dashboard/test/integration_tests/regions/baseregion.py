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
import types

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
        if src_elem is None and self._default_src_locator:
            # fake self.src_elem must be set up in
            # order self._get_element work
            self.src_elem = driver
            src_elem = self._get_element(*self._default_src_locator)

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
            return self._dynamic_properties[name]()
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    # protected methods and classes
    class _DynamicProperty(object):
        """Serves as new property holder."""

        def __init__(self, method, name=None, id_pattern=None):
            """Invocation of `method` should return either single property, or
            a dictionary of properties, or a list of them.

            In case it's single, neither name, nor id_pattern is required.

            In case it's a dictionary, it's expected that it has a value for
            the key equal to `name` argument. That's a standard way of
            fetching a form field).

            In case it's a list, the element with an id equal to the result of
            `id_pattern % name` is supposed to be there. That's a standard way
            of fetching a table action (either table-wise or row-wise).
            """
            self.method = method
            self.name = name
            self.id_pattern = id_pattern

        def __call__(self, *args, **kwargs):
            result = self.method()
            if self.name is None:
                return result
            else:
                if isinstance(result, list) and self.id_pattern is not None:
                    # NOTE(tsufiev): map table actions to action names using
                    # action tag's ids
                    actual_id = self.id_pattern % self.name
                    result = {self.name: entry for entry in result
                              if entry.get_attribute('id') == actual_id}
                if isinstance(result, dict):
                    return result[self.name]
                return result

    def _init_dynamic_properties(self, new_attr_names, method,
                                 id_pattern=None):
        """Create new object's 'properties' at runtime."""
        for new_attr_name in new_attr_names:
            self._init_dynamic_property(new_attr_name, method, id_pattern)

    def _init_dynamic_property(self, new_attr_name, method, id_pattern=None):
        """Create new object's property at runtime. See _DynamicProperty's
        __init__ docstring for a description of arguments.
        """
        if (new_attr_name in dir(self) or
                new_attr_name in self._dynamic_properties):
            raise AttributeError("%s class has already attribute %s."
                                 "The new property could not be "
                                 "created." % (self.__class__.__name__,
                                               new_attr_name))
        new_method = self.__class__._DynamicProperty(
            method, new_attr_name, id_pattern)
        inst_method = types.MethodType(new_method, self)
        self._dynamic_properties[new_attr_name] = inst_method

    def _get_element(self, *locator):
        return self.src_elem.find_element(*locator)

    def _get_elements(self, *locator):
        return self.src_elem.find_elements(*locator)
