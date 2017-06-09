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

import collections
import functools
import inspect

import testtools

from openstack_dashboard.test.integration_tests import config


def _is_test_method_name(method):
    return method.startswith('test_')


def _is_test_fixture(method):
    return method in ['setUp', 'tearDown']


def _is_test_cls(cls):
    return cls.__name__.startswith('Test')


def _mark_method_skipped(meth, reason):
    """Decorate to mark method as skipped.

    This marks method as skipped by replacing the actual method with wrapper
    that raises the testtools.testcase.TestSkipped exception.
    """

    @functools.wraps(meth)
    def wrapper(*args, **kwargs):
        raise testtools.testcase.TestSkipped(reason)

    return wrapper


def _mark_class_skipped(cls, reason):
    """Mark every test method of the class as skipped."""
    tests = [attr for attr in dir(cls) if _is_test_method_name(attr) or
             _is_test_fixture(attr)]
    for test in tests:
        method = getattr(cls, test)
        if callable(method):
            setattr(cls, test, _mark_method_skipped(method, reason))
    return cls


NOT_TEST_OBJECT_ERROR_MSG = "Decorator can be applied only on test" \
                            " classes and test methods."


def _get_skip_method(obj):
    """Make sure that we can decorate both methods and classes."""
    if inspect.isclass(obj):
        if not _is_test_cls(obj):
            raise ValueError(NOT_TEST_OBJECT_ERROR_MSG)
        return _mark_class_skipped
    else:
        if not _is_test_method_name(obj.__name__):
            raise ValueError(NOT_TEST_OBJECT_ERROR_MSG)
        return _mark_method_skipped


def services_required(*req_services):
    """Decorator for marking test's service requirements.

    If requirements are not met in the configuration file
    test is marked as skipped.

    Usage:
    from openstack_dashboard.test.integration_tests.tests import decorators

    @decorators.services_required("sahara")
    class TestLogin(helpers.BaseTestCase):
    .
    .
    .


    from openstack_dashboard.test.integration_tests.tests import decorators

    class TestLogin(helpers.BaseTestCase):

        @decorators.services_required("sahara")
        def test_login(self):
            login_pg = loginpage.LoginPage(self.driver, self.conf)
            .
            .
            .
    """
    def actual_decoration(obj):
        skip_method = _get_skip_method(obj)
        # get available services from configuration
        avail_services = config.get_config().service_available
        for req_service in req_services:
            if not getattr(avail_services, req_service, False):
                obj = skip_method(obj, "%s service is required for this test"
                                       " to work properly." % req_service)
                break
        return obj
    return actual_decoration


def _parse_compound_config_option_value(option_name):
    """Parses the value of a given config option.

    The section name of the option is separated from option name by '.'.
    """
    name_parts = option_name.split('.')
    name_parts.reverse()
    option = config.get_config()
    while name_parts:
        option = getattr(option, name_parts.pop())
    return option


def config_option_required(option_key, required_value, message=None):
    if message is None:
        message = "%s option equal to '%s' is required for this test to work" \
                  " properly." % (option_key, required_value)

    def actual_decoration(obj):
        skip_method = _get_skip_method(obj)
        option_value = _parse_compound_config_option_value(option_key)
        if option_value != required_value:
            obj = skip_method(obj, message)
        return obj
    return actual_decoration


def skip_because(**kwargs):
    """Decorator for skipping tests hitting known bugs

    Usage:
    from openstack_dashboard.test.integration_tests.tests import decorators

    class TestDashboardHelp(helpers.TestCase):

        @decorators.skip_because(bugs=["1234567"])
        def test_dashboard_help_redirection(self):
        .
        .
        .
    """
    def actual_decoration(obj):
        skip_method = _get_skip_method(obj)
        bugs = kwargs.get("bugs")
        if bugs and isinstance(bugs, collections.Iterable):
            for bug in bugs:
                if not bug.isdigit():
                    raise ValueError("bug must be a valid bug number")
            obj = skip_method(obj, "Skipped until Bugs: %s are resolved." %
                              ", ".join([bug for bug in bugs]))
        return obj
    return actual_decoration


def attach_video(func):
    """Notify test runner to attach test video in any case"""

    @functools.wraps(func)
    def wrapper(self, *args, **kwgs):
        self._need_attach_video = True
        return func(self, *args, **kwgs)

    return wrapper
