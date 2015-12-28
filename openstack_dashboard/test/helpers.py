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

import collections
import copy
from functools import wraps  # noqa
import os


from ceilometerclient.v2 import client as ceilometer_client
from cinderclient import client as cinder_client
from django.conf import settings
from django.contrib.messages.storage import default_storage  # noqa
from django.core.handlers import wsgi
from django.core import urlresolvers
from django.test.client import RequestFactory  # noqa
from django.test import utils as django_test_utils
from django.utils.importlib import import_module  # noqa
from django.utils import unittest
import glanceclient
from heatclient import client as heat_client
import httplib2
from keystoneclient.v2_0 import client as keystone_client
import mock
from mox3 import mox
from neutronclient.v2_0 import client as neutron_client
from novaclient.v2 import client as nova_client
from openstack_auth import user
from openstack_auth import utils
import six
from six import moves
from swiftclient import client as swift_client

from horizon import base
from horizon import conf
from horizon.test import helpers as horizon_helpers
from openstack_dashboard import api
from openstack_dashboard import context_processors
from openstack_dashboard.test.test_data import utils as test_utils


# Makes output of failing mox tests much easier to read.
wsgi.WSGIRequest.__repr__ = lambda self: "<class 'django.http.HttpRequest'>"


def create_stubs(stubs_to_create=None):
    """decorator to simplify setting up multiple stubs at once via mox

    :param stubs_to_create: methods to stub in one or more modules
    :type stubs_to_create: dict

    The keys are python paths to the module containing the methods to mock.

    To mock a method in openstack_dashboard/api/nova.py, the key is::

        api.nova

    The values are either a tuple of list of methods to mock in the module
    indicated by the key.

    For example::

        ('server_list',)
            -or-
        ('flavor_list', 'server_list',)
            -or-
        ['flavor_list', 'server_list']

    Additionally, multiple modules can be mocked at once::

        {
            api.nova: ('flavor_list', 'server_list'),
            api.glance: ('image_list_detailed',),
        }

    """
    if stubs_to_create is None:
        stubs_to_create = {}
    if not isinstance(stubs_to_create, dict):
        raise TypeError("create_stub must be passed a dict, but a %s was "
                        "given." % type(stubs_to_create).__name__)

    def inner_stub_out(fn):
        @wraps(fn)
        def instance_stub_out(self, *args, **kwargs):
            for key in stubs_to_create:
                if not (isinstance(stubs_to_create[key], tuple) or
                        isinstance(stubs_to_create[key], list)):
                    raise TypeError("The values of the create_stub "
                                    "dict must be lists or tuples, but "
                                    "is a %s."
                                    % type(stubs_to_create[key]).__name__)

                for value in stubs_to_create[key]:
                    self.mox.StubOutWithMock(key, value)
            return fn(self, *args, **kwargs)
        return instance_stub_out
    return inner_stub_out


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


@unittest.skipIf(os.environ.get('SKIP_UNITTESTS', False),
                 "The SKIP_UNITTESTS env variable is set.")
class TestCase(horizon_helpers.TestCase):
    """Specialized base test case class for Horizon.

    It gives access to numerous additional features:

      * A full suite of test data through various attached objects and
        managers (e.g. ``self.servers``, ``self.user``, etc.). See the
        docs for
        :class:`~openstack_dashboard.test.test_data.utils.TestData`
        for more information.
      * The ``mox`` mocking framework via ``self.mox``.
      * A set of request context data via ``self.context``.
      * A ``RequestFactory`` class which supports Django's ``contrib.messages``
        framework via ``self.factory``.
      * A ready-to-go request object via ``self.request``.
      * The ability to override specific time data controls for easier testing.
      * Several handy additional assertion methods.
    """
    def setUp(self):
        def fake_conn_request(*args, **kwargs):
            raise Exception("An external URI request tried to escape through "
                            "an httplib2 client. Args: %s, kwargs: %s"
                            % (args, kwargs))

        self._real_conn_request = httplib2.Http._conn_request
        httplib2.Http._conn_request = fake_conn_request

        self._real_context_processor = context_processors.openstack
        context_processors.openstack = lambda request: self.context

        self.patchers = {}
        self.add_panel_mocks()

        super(TestCase, self).setUp()

    def _setup_test_data(self):
        super(TestCase, self)._setup_test_data()
        test_utils.load_test_data(self)
        self.context = {'authorized_tenants': self.tenants.list()}

    def _setup_factory(self):
        # For some magical reason we need a copy of this here.
        self.factory = RequestFactoryWithMessages()

    def _setup_user(self):
        self._real_get_user = utils.get_user
        tenants = self.context['authorized_tenants']
        self.setActiveUser(id=self.user.id,
                           token=self.token,
                           username=self.user.name,
                           domain_id=self.domain.id,
                           user_domain_name=self.domain.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=tenants)

    def _setup_request(self):
        super(TestCase, self)._setup_request()
        self.request.session['token'] = self.token.id

    def add_panel_mocks(self):
        """Global mocks on panels that get called on all views."""
        self.patchers['aggregates'] = mock.patch(
            'openstack_dashboard.dashboards.admin'
            '.aggregates.panel.Aggregates.can_access',
            mock.Mock(return_value=True))
        self.patchers['aggregates'].start()

    def tearDown(self):
        httplib2.Http._conn_request = self._real_conn_request
        context_processors.openstack = self._real_context_processor
        utils.get_user = self._real_get_user
        mock.patch.stopall()
        super(TestCase, self).tearDown()

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
        self.assertEqual(response._headers.get('location', None),
                         ('Location', settings.TESTSERVER + expected_url))
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
        self.assertTrue(
            len(actions) > 0,
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
        self.assertTrue(
            len(actions) > 0,
            "No action named '%s' found in '%s' table" % msg_args)

        self.assertEqual(
            1, len(actions),
            "More than one action named '%s' found in '%s' table" % msg_args)

        return actions[0]

    @staticmethod
    def mock_rest_request(**args):
        mock_args = {
            'user.is_authenticated.return_value': True,
            'is_ajax.return_value': True,
            'policy.check.return_value': True,
            'body': ''
        }
        mock_args.update(args)
        return mock.Mock(**mock_args)


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
    """Testing APIs.

    For use with tests which deal with the underlying clients rather than
    stubbing out the openstack_dashboard.api.* methods.
    """
    def setUp(self):
        super(APITestCase, self).setUp()
        utils.patch_middleware_get_user()

        def fake_keystoneclient(request, admin=False):
            """Returns the stub keystoneclient.

            Only necessary because the function takes too many arguments to
            conveniently be a lambda.
            """
            return self.stub_keystoneclient()

        def fake_glanceclient(request, version='1'):
            """Returns the stub glanceclient.

            Only necessary because the function takes too many arguments to
            conveniently be a lambda.
            """
            return self.stub_glanceclient()

        # Store the original clients
        self._original_glanceclient = api.glance.glanceclient
        self._original_keystoneclient = api.keystone.keystoneclient
        self._original_novaclient = api.nova.novaclient
        self._original_neutronclient = api.neutron.neutronclient
        self._original_cinderclient = api.cinder.cinderclient
        self._original_heatclient = api.heat.heatclient
        self._original_ceilometerclient = api.ceilometer.ceilometerclient

        # Replace the clients with our stubs.
        api.glance.glanceclient = fake_glanceclient
        api.keystone.keystoneclient = fake_keystoneclient
        api.nova.novaclient = lambda request: self.stub_novaclient()
        api.neutron.neutronclient = lambda request: self.stub_neutronclient()
        api.cinder.cinderclient = lambda request: self.stub_cinderclient()
        api.heat.heatclient = (lambda request, password=None:
                               self.stub_heatclient())
        api.ceilometer.ceilometerclient = (lambda request:
                                           self.stub_ceilometerclient())

    def tearDown(self):
        super(APITestCase, self).tearDown()
        api.glance.glanceclient = self._original_glanceclient
        api.nova.novaclient = self._original_novaclient
        api.keystone.keystoneclient = self._original_keystoneclient
        api.neutron.neutronclient = self._original_neutronclient
        api.cinder.cinderclient = self._original_cinderclient
        api.heat.heatclient = self._original_heatclient
        api.ceilometer.ceilometerclient = self._original_ceilometerclient

    def stub_novaclient(self):
        if not hasattr(self, "novaclient"):
            self.mox.StubOutWithMock(nova_client, 'Client')
            self.novaclient = self.mox.CreateMock(nova_client.Client)
        return self.novaclient

    def stub_cinderclient(self):
        if not hasattr(self, "cinderclient"):
            self.mox.StubOutWithMock(cinder_client, 'Client')
            self.cinderclient = self.mox.CreateMock(cinder_client.Client)
        return self.cinderclient

    def stub_keystoneclient(self):
        if not hasattr(self, "keystoneclient"):
            self.mox.StubOutWithMock(keystone_client, 'Client')
            # NOTE(saschpe): Mock properties, MockObject.__init__ ignores them:
            keystone_client.Client.auth_token = 'foo'
            keystone_client.Client.service_catalog = None
            keystone_client.Client.tenant_id = '1'
            keystone_client.Client.tenant_name = 'tenant_1'
            keystone_client.Client.management_url = ""
            keystone_client.Client.__dir__ = lambda: []
            self.keystoneclient = self.mox.CreateMock(keystone_client.Client)
        return self.keystoneclient

    def stub_glanceclient(self):
        if not hasattr(self, "glanceclient"):
            self.mox.StubOutWithMock(glanceclient, 'Client')
            self.glanceclient = self.mox.CreateMock(glanceclient.Client)
        return self.glanceclient

    def stub_neutronclient(self):
        if not hasattr(self, "neutronclient"):
            self.mox.StubOutWithMock(neutron_client, 'Client')
            self.neutronclient = self.mox.CreateMock(neutron_client.Client)
        return self.neutronclient

    def stub_swiftclient(self, expected_calls=1):
        if not hasattr(self, "swiftclient"):
            self.mox.StubOutWithMock(swift_client, 'Connection')
            self.swiftclient = self.mox.CreateMock(swift_client.Connection)
            while expected_calls:
                swift_client.Connection(None,
                                        mox.IgnoreArg(),
                                        None,
                                        preauthtoken=mox.IgnoreArg(),
                                        preauthurl=mox.IgnoreArg(),
                                        cacert=None,
                                        insecure=False,
                                        auth_version="2.0") \
                            .AndReturn(self.swiftclient)
                expected_calls -= 1
        return self.swiftclient

    def stub_heatclient(self):
        if not hasattr(self, "heatclient"):
            self.mox.StubOutWithMock(heat_client, 'Client')
            self.heatclient = self.mox.CreateMock(heat_client.Client)
        return self.heatclient

    def stub_ceilometerclient(self):
        if not hasattr(self, "ceilometerclient"):
            self.mox.StubOutWithMock(ceilometer_client, 'Client')
            self.ceilometerclient = self.mox.\
                CreateMock(ceilometer_client.Client)
        return self.ceilometerclient


@unittest.skipUnless(os.environ.get('WITH_SELENIUM', False),
                     "The WITH_SELENIUM env variable is not set.")
class SeleniumTestCase(horizon_helpers.SeleniumTestCase):

    def setUp(self):
        super(SeleniumTestCase, self).setUp()

        test_utils.load_test_data(self)
        self.mox = mox.Mox()

        self._real_get_user = utils.get_user
        self.setActiveUser(id=self.user.id,
                           token=self.token,
                           username=self.user.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=self.tenants.list())
        self.patchers = {}
        self.patchers['aggregates'] = mock.patch(
            'openstack_dashboard.dashboards.admin'
            '.aggregates.panel.Aggregates.can_access',
            mock.Mock(return_value=True))
        self.patchers['aggregates'].start()
        os.environ["HORIZON_TEST_RUN"] = "True"

    def tearDown(self):
        self.mox.UnsetStubs()
        utils.get_user = self._real_get_user
        mock.patch.stopall()
        self.mox.VerifyAll()
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
        urlresolvers.clear_url_caches()
        moves.reload_module(import_module(settings.ROOT_URLCONF))
        base.Horizon._urls()


class update_settings(django_test_utils.override_settings):
    """override_settings which allows override an item in dict.

    django original override_settings replaces a dict completely,
    however OpenStack dashboard setting has many dictionary configuration
    and there are test case where we want to override only one item in
    a dictionary and keep other items in the dictionary.
    This version of override_settings allows this if keep_dict is True.

    If keep_dict False is specified, the original behavior of
    Django override_settings is used.
    """

    def __init__(self, keep_dict=True, **kwargs):
        if keep_dict:
            for key, new_value in kwargs.items():
                value = getattr(settings, key, None)
                if (isinstance(new_value, collections.Mapping) and
                        isinstance(value, collections.Mapping)):
                    copied = copy.copy(value)
                    copied.update(new_value)
                    kwargs[key] = copied
        super(update_settings, self).__init__(**kwargs)
