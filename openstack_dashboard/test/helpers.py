# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from functools import wraps
from importlib import import_module
import logging
import os
import traceback

from django.conf import settings
from django.contrib.messages.storage import default_storage
from django.core.handlers import wsgi
from django.test.client import RequestFactory
from django.test import tag
from django import urls
from django.utils import http

import mock
from openstack_auth import user
from openstack_auth import utils
from requests.packages.urllib3.connection import HTTPConnection
import six
from six import moves

from horizon import base
from horizon import conf
from horizon.test import helpers as horizon_helpers
from openstack_dashboard import api
from openstack_dashboard import context_processors
from openstack_dashboard.test.test_data import utils as test_utils


LOG = logging.getLogger(__name__)

# Makes output of failing tests much easier to read.
wsgi.WSGIRequest.__repr__ = lambda self: "<class 'django.http.HttpRequest'>"

# Shortcuts to avoid importing horizon_helpers and for backward compatibility.
update_settings = horizon_helpers.update_settings
IsA = horizon_helpers.IsA
IsHttpRequest = horizon_helpers.IsHttpRequest


def create_mocks(target_methods):
    """decorator to simplify setting up multiple mocks at once

    :param target_methods: a dict to define methods to be patched using mock.

    A key of "target_methods" is a target object whose attribute(s) are
    patched.

    A value of "target_methods" is a list of methods to be patched
    using mock. Each element of the list can be a string or a tuple
    consisting of two strings.

    A string specifies a method name of "target" object to be mocked.
    The decorator create a mock object for the method and the started mock
    can be accessed via 'mock_<method-name>' of the test class.
    For example, in case of::

        @create_mocks({api.nova: ['server_list',
                                  'flavor_list']})
        def test_example(self):
            ...
            self.mock_server_list.return_value = ...
            self.mock_flavar_list.side_effect = ...

    you can access the mocked method via "self.mock_server_list"
    inside a test class.

    The tuple version is useful when there are multiple methods with
    a same name are mocked in a single test.
    The format of the tuple is::

        ("<method-name-to-be-mocked>", "<attr-name>")

    The decorator create a mock object for "<method-name-to-be-mocked>"
    and the started mock can be accessed via 'mock_<attr-name>' of
    the test class.

    Example::

        @create_mocks({
            api.nova: [
                'usage_get',
                ('tenant_absolute_limits', 'nova_tenant_absolute_limits'),
                'extension_supported',
            ],
            api.cinder: [
                ('tenant_absolute_limits', 'cinder_tenant_absolute_limits'),
            ],
        })
        def test_example(self):
            ...
            self.mock_usage_get.return_value = ...
            self.mock_nova_tenant_absolute_limits.return_value = ...
            self.mock_cinder_tenant_absolute_limits.return_value = ...
            ...
            self.mock_extension_supported.assert_has_calls(....)

    """
    def wrapper(function):
        @wraps(function)
        def wrapped(inst, *args, **kwargs):
            for target, methods in target_methods.items():
                for method in methods:
                    if isinstance(method, str):
                        method_mocked = method
                        attr_name = method
                    else:
                        method_mocked = method[0]
                        attr_name = method[1]
                    m = mock.patch.object(target, method_mocked)
                    setattr(inst, 'mock_%s' % attr_name, m.start())
            return function(inst, *args, **kwargs)
        return wrapped
    return wrapper


def _apply_panel_mocks(patchers=None):
    """Global mocks on panels that get called on all views."""
    if patchers is None:
        patchers = {}
    mocked_methods = settings.TEST_GLOBAL_MOCKS_ON_PANELS
    for name, mock_config in mocked_methods.items():
        method = mock_config['method']
        mock_params = {}
        for param in ['return_value', 'side_effect']:
            if param in mock_config:
                mock_params[param] = mock_config[param]
        patcher = mock.patch(method, **mock_params)
        patcher.start()
        patchers[name] = patcher
    return patchers


class RequestFactoryWithMessages(RequestFactory):
    def get(self, *args, **kwargs):
        req = super(RequestFactoryWithMessages, self).get(*args, **kwargs)
        req.user = utils.get_user(req)
        req.session = []
        req._messages = default_storage(req)
        return req

    def post(self, *args, **kwargs):
        req = super(RequestFactoryWithMessages, self).post(*args, **kwargs)
        req.user = utils.get_user(req)
        req.session = []
        req._messages = default_storage(req)
        return req


class TestCase(horizon_helpers.TestCase):
    """Specialized base test case class for Horizon.

    It gives access to numerous additional features:

    * A full suite of test data through various attached objects and
      managers (e.g. ``self.servers``, ``self.user``, etc.). See the
      docs for
      :class:`~openstack_dashboard.test.test_data.utils.TestData`
      for more information.
    * A set of request context data via ``self.context``.
    * A ``RequestFactory`` class which supports Django's ``contrib.messages``
      framework via ``self.factory``.
    * A ready-to-go request object via ``self.request``.
    * The ability to override specific time data controls for easier testing.
    * Several handy additional assertion methods.
    """

    # To force test failures when unmocked API calls are attempted, provide
    # boolean variable to store failures
    missing_mocks = False

    def fake_conn_request(self):
        # print a stacktrace to illustrate where the unmocked API call
        # is being made from
        traceback.print_stack()
        # forcing a test failure for missing mock
        self.missing_mocks = True

    def setUp(self):
        self._real_conn_request = HTTPConnection.connect
        HTTPConnection.connect = self.fake_conn_request

        self._real_context_processor = context_processors.openstack
        context_processors.openstack = lambda request: self.context

        self.patchers = _apply_panel_mocks()

        super(TestCase, self).setUp()

    def _setup_test_data(self):
        super(TestCase, self)._setup_test_data()
        test_utils.load_test_data(self)
        self.context = {
            'authorized_tenants': self.tenants.list(),
            'JS_CATALOG': context_processors.get_js_catalog(settings),
        }

    def _setup_factory(self):
        # For some magical reason we need a copy of this here.
        self.factory = RequestFactoryWithMessages()

    def _setup_user(self, **kwargs):
        self._real_get_user = utils.get_user
        tenants = self.context['authorized_tenants']
        base_kwargs = {
            'id': self.user.id,
            'token': self.token,
            'username': self.user.name,
            'domain_id': self.domain.id,
            'user_domain_name': self.domain.name,
            'tenant_id': self.tenant.id,
            'service_catalog': self.service_catalog,
            'authorized_tenants': tenants
        }
        base_kwargs.update(kwargs)
        self.setActiveUser(**base_kwargs)

    def _setup_request(self):
        super(TestCase, self)._setup_request()
        self.request.session['token'] = self.token.id

    def tearDown(self):
        HTTPConnection.connect = self._real_conn_request
        context_processors.openstack = self._real_context_processor
        utils.get_user = self._real_get_user
        mock.patch.stopall()
        super(TestCase, self).tearDown()

        # cause a test failure if an unmocked API call was attempted
        if self.missing_mocks:
            raise AssertionError("An unmocked API call was made.")

    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                      service_catalog=None, tenant_name=None, roles=None,
                      authorized_tenants=None, enabled=True, domain_id=None,
                      user_domain_name=None):
        def get_user(request):
            return user.User(id=id,
                             token=token,
                             user=username,
                             domain_id=domain_id,
                             user_domain_name=user_domain_name,
                             tenant_id=tenant_id,
                             tenant_name=tenant_name,
                             service_catalog=service_catalog,
                             roles=roles,
                             enabled=enabled,
                             authorized_tenants=authorized_tenants,
                             endpoint=settings.OPENSTACK_KEYSTONE_URL)
        utils.get_user = get_user

    def assertRedirectsNoFollow(self, response, expected_url):
        """Check for redirect.

        Asserts that the given response issued a 302 redirect without
        processing the view which is redirected to.
        """
        loc = six.text_type(response._headers.get('location', None)[1])
        loc = http.urlunquote(loc)
        expected_url = http.urlunquote(expected_url)
        self.assertEqual(loc, expected_url)
        self.assertEqual(response.status_code, 302)

    def assertNoFormErrors(self, response, context_name="form"):
        """Checks for no form errors.

        Asserts that the response either does not contain a form in its
        context, or that if it does, that form has no errors.
        """
        context = getattr(response, "context", {})
        if not context or context_name not in context:
            return True
        errors = response.context[context_name]._errors
        assert len(errors) == 0, \
            "Unexpected errors were found on the form: %s" % errors

    def assertFormErrors(self, response, count=0, message=None,
                         context_name="form"):
        """Check for form errors.

        Asserts that the response does contain a form in its
        context, and that form has errors, if count were given,
        it must match the exact numbers of errors
        """
        context = getattr(response, "context", {})
        assert (context and context_name in context), \
            "The response did not contain a form."
        errors = response.context[context_name]._errors
        if count:
            assert len(errors) == count, \
                "%d errors were found on the form, %d expected" % \
                (len(errors), count)
            if message and message not in six.text_type(errors):
                self.fail("Expected message not found, instead found: %s"
                          % ["%s: %s" % (key, [e for e in field_errors]) for
                             (key, field_errors) in errors.items()])
        else:
            assert len(errors) > 0, "No errors were found on the form"

    def assertStatusCode(self, response, expected_code):
        """Validates an expected status code.

        Matches camel case of other assert functions
        """
        if response.status_code == expected_code:
            return
        self.fail('status code %r != %r: %s' % (response.status_code,
                                                expected_code,
                                                response.content))

    def assertItemsCollectionEqual(self, response, items_list):
        self.assertEqual(response.json, {"items": items_list})

    def getAndAssertTableRowAction(self, response, table_name,
                                   action_name, row_id):
        table = response.context[table_name + '_table']
        rows = list(moves.filter(lambda x: x.id == row_id,
                                 table.data))
        self.assertEqual(1, len(rows),
                         "Did not find a row matching id '%s'" % row_id)
        row_actions = table.get_row_actions(rows[0])
        actions = list(moves.filter(lambda x: x.name == action_name,
                                    row_actions))

        msg_args = (action_name, table_name, row_id)
        self.assertGreater(
            len(actions), 0,
            "No action named '%s' found in '%s' table for id '%s'" % msg_args)

        self.assertEqual(
            1, len(actions),
            "Multiple actions named '%s' found in '%s' table for id '%s'"
            % msg_args)

        return actions[0]

    def getAndAssertTableAction(self, response, table_name, action_name):

        table = response.context[table_name + '_table']
        table_actions = table.get_table_actions()
        actions = list(moves.filter(lambda x: x.name == action_name,
                                    table_actions))
        msg_args = (action_name, table_name)
        self.assertGreater(
            len(actions), 0,
            "No action named '%s' found in '%s' table" % msg_args)

        self.assertEqual(
            1, len(actions),
            "More than one action named '%s' found in '%s' table" % msg_args)

        return actions[0]

    @staticmethod
    def mock_rest_request(**args):
        mock_args = {
            'user.is_authenticated': True,
            'is_ajax.return_value': True,
            'policy.check.return_value': True,
            'body': ''
        }
        mock_args.update(args)
        return mock.Mock(**mock_args)

    def assert_mock_multiple_calls_with_same_arguments(
            self, mocked_method, count, expected_call):
        self.assertEqual(count, mocked_method.call_count)
        mocked_method.assert_has_calls([expected_call] * count)

    def assertNoWorkflowErrors(self, response, context_name="workflow"):
        """Checks for no workflow errors.

        Asserts that the response either does not contain a workflow in its
        context, or that if it does, that workflow has no errors.
        """
        context = getattr(response, "context", {})
        if not context or context_name not in context:
            return True
        errors = [step.action._errors for step in
                  response.context[context_name].steps]
        self.assertEqual(
            0, len(errors),
            "Unexpected errors were found on the workflow: %s" % errors)

    def assertWorkflowErrors(self, response, count=0, message=None,
                             context_name="workflow"):
        """Check for workflow errors.

        Asserts that the response does contain a workflow in its
        context, and that workflow has errors, if count were given,
        it must match the exact numbers of errors
        """
        context = getattr(response, "context", {})
        self.assertIn(context_name, context,
                      msg="The response did not contain a workflow.")
        errors = {}
        for step in response.context[context_name].steps:
            errors.update(step.action._errors)
        if count:
            self.assertEqual(
                count, len(errors),
                "%d errors were found on the workflow, %d expected" %
                (len(errors), count))
            if message and message not in six.text_type(errors):
                self.fail("Expected message not found, instead found: %s"
                          % ["%s: %s" % (key, [e for e in field_errors]) for
                             (key, field_errors) in errors.items()])
        else:
            self.assertGreater(
                len(errors), 0,
                "No errors were found on the workflow")


class BaseAdminViewTests(TestCase):
    """Sets an active user with the "admin" role.

    For testing admin-only views and functionality.
    """
    def setActiveUser(self, *args, **kwargs):
        if "roles" not in kwargs:
            kwargs['roles'] = [self.roles.admin._info]
        super(BaseAdminViewTests, self).setActiveUser(*args, **kwargs)

    def setSessionValues(self, **kwargs):
        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        for key in kwargs:
            store[key] = kwargs[key]
            self.request.session[key] = kwargs[key]
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key


class APITestCase(TestCase):
    def setUp(self):
        super(APITestCase, self).setUp()
        utils.patch_middleware_get_user()


# APIMockTestCase was introduced to support mox to mock migration smoothly
# but it turns we have still users of APITestCase.
# We keep both for a while.
# Looking at the usage of these classes, it seems better to drop this one.
# TODO(amotoki): Clean up APIMockTestCase usage in horizon plugins.
APIMockTestCase = APITestCase


# Need this to test both Glance API V1 and V2 versions
class ResetImageAPIVersionMixin(object):
    def setUp(self):
        super(ResetImageAPIVersionMixin, self).setUp()
        api.glance.VERSIONS.clear_active_cache()

    def tearDown(self):
        api.glance.VERSIONS.clear_active_cache()
        super(ResetImageAPIVersionMixin, self).tearDown()


@tag('selenium')
class SeleniumTestCase(horizon_helpers.SeleniumTestCase):

    def setUp(self):
        super(SeleniumTestCase, self).setUp()

        test_utils.load_test_data(self)

        self._real_get_user = utils.get_user
        self.setActiveUser(id=self.user.id,
                           token=self.token,
                           username=self.user.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=self.tenants.list())
        self.patchers = _apply_panel_mocks()
        os.environ["HORIZON_TEST_RUN"] = "True"

    def tearDown(self):
        utils.get_user = self._real_get_user
        mock.patch.stopall()
        del os.environ["HORIZON_TEST_RUN"]

    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                      service_catalog=None, tenant_name=None, roles=None,
                      authorized_tenants=None, enabled=True):
        def get_user(request):
            return user.User(id=id,
                             token=token,
                             user=username,
                             tenant_id=tenant_id,
                             service_catalog=service_catalog,
                             roles=roles,
                             enabled=enabled,
                             authorized_tenants=authorized_tenants,
                             endpoint=settings.OPENSTACK_KEYSTONE_URL)
        utils.get_user = get_user


class SeleniumAdminTestCase(SeleniumTestCase):
    """Version of AdminTestCase for Selenium.

    Sets an active user with the "admin" role for testing admin-only views and
    functionality.
    """
    def setActiveUser(self, *args, **kwargs):
        if "roles" not in kwargs:
            kwargs['roles'] = [self.roles.admin._info]
        super(SeleniumAdminTestCase, self).setActiveUser(*args, **kwargs)


def my_custom_sort(flavor):
    sort_order = {
        'm1.secret': 0,
        'm1.tiny': 1,
        'm1.massive': 2,
        'm1.metadata': 3,
    }
    return sort_order[flavor.name]


# TODO(amotoki): Investigate a way to run PluginTestCase with the main
# unit tests. Currently we fail to find a way to clean up urlpatterns and
# Site registry touched by setUp() cleanly. As a workaround, we run
# PluginTestCase as a separate test process. Hopefully this workaround has gone
# in future. For more detail, see bug 1809983 and
# https://review.opendev.org/#/c/627640/.
@tag('plugin-test')
class PluginTestCase(TestCase):
    """Test case for testing plugin system of Horizon.

    For use with tests which deal with the pluggable dashboard and panel
    configuration, it takes care of backing up and restoring the Horizon
    configuration.
    """
    def setUp(self):
        super(PluginTestCase, self).setUp()
        self.old_horizon_config = conf.HORIZON_CONFIG
        conf.HORIZON_CONFIG = conf.LazySettings()
        base.Horizon._urls()
        # Store our original dashboards
        self._discovered_dashboards = base.Horizon._registry.keys()
        # Gather up and store our original panels for each dashboard
        self._discovered_panels = {}
        for dash in self._discovered_dashboards:
            panels = base.Horizon._registry[dash]._registry.keys()
            self._discovered_panels[dash] = panels

    def tearDown(self):
        super(PluginTestCase, self).tearDown()
        conf.HORIZON_CONFIG = self.old_horizon_config
        # Destroy our singleton and re-create it.
        base.HorizonSite._instance = None
        del base.Horizon
        base.Horizon = base.HorizonSite()
        # Reload the convenience references to Horizon stored in __init__
        moves.reload_module(import_module("horizon"))
        # Re-register our original dashboards and panels.
        # This is necessary because autodiscovery only works on the first
        # import, and calling reload introduces innumerable additional
        # problems. Manual re-registration is the only good way for testing.
        for dash in self._discovered_dashboards:
            base.Horizon.register(dash)
            for panel in self._discovered_panels[dash]:
                dash.register(panel)
        self._reload_urls()

    def _reload_urls(self):
        """CLeans up URLs.

        Clears out the URL caches, reloads the root urls module, and
        re-triggers the autodiscovery mechanism for Horizon. Allows URLs
        to be re-calculated after registering new dashboards. Useful
        only for testing and should never be used on a live site.
        """
        urls.clear_url_caches()
        moves.reload_module(import_module(settings.ROOT_URLCONF))
        base.Horizon._urls()


def mock_obj_to_dict(r):
    return mock.Mock(**{'to_dict.return_value': r})


def mock_factory(r):
    """mocks all the attributes as well as the to_dict """
    mocked = mock_obj_to_dict(r)
    mocked.configure_mock(**r)
    return mocked
