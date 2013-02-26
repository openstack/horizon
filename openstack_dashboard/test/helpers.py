# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import os

from django import http
from django.conf import settings
from django.contrib.messages.storage import default_storage
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.handlers import wsgi
from django.test.client import RequestFactory
from django.utils import unittest

import glanceclient
from keystoneclient.v2_0 import client as keystone_client
from novaclient.v1_1 import client as nova_client
from quantumclient.v2_0 import client as quantum_client
from swiftclient import client as swift_client
from cinderclient import client as cinder_client

import httplib2
import mox

from openstack_auth import utils, user

from horizon.test import helpers as horizon_helpers
from horizon import middleware

from openstack_dashboard import api
from openstack_dashboard import context_processors
from openstack_dashboard.test.test_data.utils import load_test_data


# Makes output of failing mox tests much easier to read.
wsgi.WSGIRequest.__repr__ = lambda self: "<class 'django.http.HttpRequest'>"


def create_stubs(stubs_to_create={}):
    if not isinstance(stubs_to_create, dict):
        raise TypeError("create_stub must be passed a dict, but a %s was "
                        "given." % type(stubs_to_create).__name__)

    def inner_stub_out(fn):
        @wraps(fn)
        def instance_stub_out(self):
            for key in stubs_to_create:
                if not (isinstance(stubs_to_create[key], tuple) or
                        isinstance(stubs_to_create[key], list)):
                    raise TypeError("The values of the create_stub "
                                    "dict must be lists or tuples, but "
                                    "is a %s."
                                    % type(stubs_to_create[key]).__name__)

                for value in stubs_to_create[key]:
                    self.mox.StubOutWithMock(key, value)
            return fn(self)
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
    """
    Specialized base test case class for Horizon which gives access to
    numerous additional features:

      * A full suite of test data through various attached objects and
        managers (e.g. ``self.servers``, ``self.user``, etc.). See the
        docs for :class:`~horizon.tests.test_data.utils.TestData` for more
        information.
      * The ``mox`` mocking framework via ``self.mox``.
      * A set of request context data via ``self.context``.
      * A ``RequestFactory`` class which supports Django's ``contrib.messages``
        framework via ``self.factory``.
      * A ready-to-go request object via ``self.request``.
      * The ability to override specific time data controls for easier testing.
      * Several handy additional assertion methods.
    """
    def setUp(self):
        load_test_data(self)
        self.mox = mox.Mox()
        self.factory = RequestFactoryWithMessages()
        self.context = {'authorized_tenants': self.tenants.list()}

        def fake_conn_request(*args, **kwargs):
            raise Exception("An external URI request tried to escape through "
                            "an httplib2 client. Args: %s, kwargs: %s"
                            % (args, kwargs))

        self._real_conn_request = httplib2.Http._conn_request
        httplib2.Http._conn_request = fake_conn_request

        self._real_context_processor = context_processors.openstack
        context_processors.openstack = lambda request: self.context

        self._real_get_user = utils.get_user
        tenants = self.context['authorized_tenants']
        self.setActiveUser(id=self.user.id,
                           token=self.token,
                           username=self.user.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=tenants)
        self.request = http.HttpRequest()
        self.request.session = self.client._session()
        self.request.session['token'] = self.token.id
        middleware.HorizonMiddleware().process_request(self.request)
        AuthenticationMiddleware().process_request(self.request)
        os.environ["HORIZON_TEST_RUN"] = "True"

    def tearDown(self):
        self.mox.UnsetStubs()
        httplib2.Http._conn_request = self._real_conn_request
        context_processors.openstack = self._real_context_processor
        utils.get_user = self._real_get_user
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

    def assertRedirectsNoFollow(self, response, expected_url):
        """
        Asserts that the given response issued a 302 redirect without
        processing the view which is redirected to.
        """
        assert (response.status_code / 100 == 3), \
            "The response did not return a redirect."
        self.assertEqual(response._headers.get('location', None),
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)

    def assertNoFormErrors(self, response, context_name="form"):
        """
        Asserts that the response either does not contain a form in it's
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
        """
        Asserts that the response does contain a form in it's
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
            if message and message not in unicode(errors):
                self.fail("Expected message not found, instead found: %s"
                          % ["%s: %s" % (key, [e for e in field_errors]) for
                             (key, field_errors) in errors.items()])
        else:
            assert len(errors) > 0, "No errors were found on the form"


class BaseAdminViewTests(TestCase):
    """
    A ``TestCase`` subclass which sets an active user with the "admin" role
    for testing admin-only views and functionality.
    """
    def setActiveUser(self, *args, **kwargs):
        if "roles" not in kwargs:
            kwargs['roles'] = [self.roles.admin._info]
        super(BaseAdminViewTests, self).setActiveUser(*args, **kwargs)


class APITestCase(TestCase):
    """
    The ``APITestCase`` class is for use with tests which deal with the
    underlying clients rather than stubbing out the
    openstack_dashboard.api.* methods.
    """
    def setUp(self):
        super(APITestCase, self).setUp()

        def fake_keystoneclient(request, admin=False):
            """
            Wrapper function which returns the stub keystoneclient. Only
            necessary because the function takes too many arguments to
            conveniently be a lambda.
            """
            return self.stub_keystoneclient()

        # Store the original clients
        self._original_glanceclient = api.glance.glanceclient
        self._original_keystoneclient = api.keystone.keystoneclient
        self._original_novaclient = api.nova.novaclient
        self._original_quantumclient = api.quantum.quantumclient
        self._original_cinderclient = api.cinder.cinderclient

        # Replace the clients with our stubs.
        api.glance.glanceclient = lambda request: self.stub_glanceclient()
        api.keystone.keystoneclient = fake_keystoneclient
        api.nova.novaclient = lambda request: self.stub_novaclient()
        api.quantum.quantumclient = lambda request: self.stub_quantumclient()
        api.cinder.cinderclient = lambda request: self.stub_cinderclient()

    def tearDown(self):
        super(APITestCase, self).tearDown()
        api.glance.glanceclient = self._original_glanceclient
        api.nova.novaclient = self._original_novaclient
        api.keystone.keystoneclient = self._original_keystoneclient
        api.quantum.quantumclient = self._original_quantumclient
        api.cinder.cinderclient = self._original_cinderclient

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
            # NOTE(saschpe): Mock the 'auth_token' property specifically,
            # MockObject.__init__ ignores properties altogether:
            keystone_client.Client.auth_token = 'foo'
            self.keystoneclient = self.mox.CreateMock(keystone_client.Client)
        return self.keystoneclient

    def stub_glanceclient(self):
        if not hasattr(self, "glanceclient"):
            self.mox.StubOutWithMock(glanceclient, 'Client')
            self.glanceclient = self.mox.CreateMock(glanceclient.Client)
        return self.glanceclient

    def stub_quantumclient(self):
        if not hasattr(self, "quantumclient"):
            self.mox.StubOutWithMock(quantum_client, 'Client')
            self.quantumclient = self.mox.CreateMock(quantum_client.Client)
        return self.quantumclient

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
                                        auth_version="2.0") \
                            .AndReturn(self.swiftclient)
                expected_calls -= 1
        return self.swiftclient


@unittest.skipUnless(os.environ.get('WITH_SELENIUM', False),
                     "The WITH_SELENIUM env variable is not set.")
class SeleniumTestCase(horizon_helpers.SeleniumTestCase):

    def setUp(self):
        super(SeleniumTestCase, self).setUp()

        load_test_data(self)
        self.mox = mox.Mox()

        self._real_get_user = utils.get_user
        self.setActiveUser(id=self.user.id,
                           token=self.token,
                           username=self.user.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=self.tenants.list())
        os.environ["HORIZON_TEST_RUN"] = "True"

    def tearDown(self):
        self.mox.UnsetStubs()
        utils.get_user = self._real_get_user
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
    """
    A ``TestCase`` subclass which sets an active user with the "admin" role
    for testing admin-only views and functionality.
    """
    def setActiveUser(self, *args, **kwargs):
        if "roles" not in kwargs:
            kwargs['roles'] = [self.roles.admin._info]
        super(SeleniumAdminTestCase, self).setActiveUser(*args, **kwargs)
