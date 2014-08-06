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
import functools
import inspect

import nose

from openstack_dashboard.test.integration_tests import config


def _is_test_method_name(method):
    return method.startswith('test_')


def _is_test_cls(cls):
    return cls.__name__.startswith('Test')


def _mark_method_skipped(meth, reason):
    """Mark method as skipped by replacing the actual method with wrapper
    that raises the nose.SkipTest exception.
    """

    @functools.wraps(meth)
    def wrapper(*args, **kwargs):
        raise nose.SkipTest(reason)

    return wrapper


def _mark_class_skipped(cls, reason):
    """Mark every test method of the class as skipped."""
    tests = [attr for attr in dir(cls) if _is_test_method_name(attr)]
    for test in tests:
        method = getattr(cls, test)
        if callable(method):
            setattr(cls, test, _mark_method_skipped(method, reason))
    return cls


NOT_TEST_OBJECT_ERROR_MSG = "Decorator can be applied only on test" \
                            " classes and test methods."


def services_required(*req_services):
    """Decorator for marking test's service requirements,
    if requirements are not met in the configuration file
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
        # make sure that we can decorate method and classes as well
        if inspect.isclass(obj):
            if not _is_test_cls(obj):
                raise ValueError(NOT_TEST_OBJECT_ERROR_MSG)
            skip_method = _mark_class_skipped
        else:
            if not _is_test_method_name(obj.func_name):
                raise ValueError(NOT_TEST_OBJECT_ERROR_MSG)
            skip_method = _mark_method_skipped
        # get available services from configuration
        avail_services = config.get_config().service_available
        for req_service in req_services:
            if not getattr(avail_services, req_service, False):
                obj = skip_method(obj, "%s service is required for this test"
                                       " to work properly." % req_service)
                break
        return obj
    return actual_decoration
