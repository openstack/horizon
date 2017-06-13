# Copyright 2012 Nebula, Inc.
#
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


def load_test_data(load_onto=None):
    from openstack_dashboard.test.test_data import cinder_data
    from openstack_dashboard.test.test_data import exceptions
    from openstack_dashboard.test.test_data import glance_data
    from openstack_dashboard.test.test_data import heat_data
    from openstack_dashboard.test.test_data import keystone_data
    from openstack_dashboard.test.test_data import neutron_data
    from openstack_dashboard.test.test_data import nova_data
    from openstack_dashboard.test.test_data import swift_data

    # The order of these loaders matters, some depend on others.
    loaders = (
        exceptions.data,
        keystone_data.data,
        glance_data.data,
        nova_data.data,
        cinder_data.data,
        neutron_data.data,
        swift_data.data,
        heat_data.data,
    )
    if load_onto:
        for data_func in loaders:
            data_func(load_onto)
        return load_onto
    else:
        return TestData(*loaders)


class TestData(object):
    """Holder object for test data.

    Any functions passed to the init method will be called with the
    ``TestData`` object as their only argument.
    They can then load data onto the object as desired.

    The idea is to use the instantiated object like this::

        >>> import glance_data
        >>> TEST = TestData(glance_data.data)
        >>> TEST.images.list()
        [<Image: visible_image>, <Image: invisible_image>]
        >>> TEST.images.first()
        <Image: visible_image>

    You can load as little or as much data as you like as long as the loaders
    don't conflict with each other.

    See the
    :class:`~openstack_dashboard.test.test_data.utils.TestDataContainer`
    class for a list of available methods.
    """
    def __init__(self, *args):
        for data_func in args:
            data_func(self)


class TestDataContainer(object):
    """A container for test data objects.

    The behavior of this class is meant to mimic a "manager" class, which
    has convenient shortcuts for common actions like "list", "filter", "get",
    and "add".
    """
    def __init__(self):
        self._objects = []

    def add(self, *args):
        """Add a new object to this container.

        Generally this method should only be used during data loading, since
        adding data during a test can affect the results of other tests.
        """
        for obj in args:
            if obj not in self._objects:
                self._objects.append(obj)

    def list(self):
        """Returns a list of all objects in this container."""
        return self._objects

    def filter(self, filtered=None, **kwargs):
        """Returns objects whose attributes match the given kwargs."""
        if filtered is None:
            filtered = self._objects
        try:
            key, value = kwargs.popitem()
        except KeyError:
            # We're out of filters, return
            return filtered

        def get_match(obj):
            return hasattr(obj, key) and getattr(obj, key) == value

        filtered = [obj for obj in filtered if get_match(obj)]
        return self.filter(filtered=filtered, **kwargs)

    def get(self, **kwargs):
        """Returns a single object whose attributes match the given kwargs.

        An error will be raised if the arguments
        provided don't return exactly one match.
        """
        matches = self.filter(**kwargs)
        if not matches:
            raise Exception("No matches found.")
        elif len(matches) > 1:
            raise Exception("Multiple matches found.")
        else:
            return matches.pop()

    def first(self):
        """Returns the first object from this container."""
        return self._objects[0]

    def count(self):
        return len(self._objects)
