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

import datetime

import cloudfiles as swift_client
from django import http
from django import test as django_test
from django.conf import settings
from django.contrib.messages.storage import default_storage
from django.core.handlers import wsgi
from django.test.client import RequestFactory
from glance import client as glance_client
from keystoneclient.v2_0 import client as keystone_client
from novaclient.v1_1 import client as nova_client
import httplib2
import mox

from horizon import api
from horizon import context_processors
from horizon import middleware
from horizon import users
from horizon.tests.test_data.utils import load_test_data

from .time import time
from .time import today
from .time import utcnow


# Makes output of failing mox tests much easier to read.
wsgi.WSGIRequest.__repr__ = lambda self: "<class 'django.http.HttpRequest'>"


class RequestFactoryWithMessages(RequestFactory):
    def post(self, *args, **kwargs):
        req = super(RequestFactoryWithMessages, self).post(*args, **kwargs)
        req.session = []
        req._messages = default_storage(req)
        return req


class TestCase(django_test.TestCase):
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

        self._real_horizon_context_processor = context_processors.horizon
        context_processors.horizon = lambda request: self.context

        self._real_get_user_from_request = users.get_user_from_request
        tenants = self.context['authorized_tenants']
        self.setActiveUser(token=self.token.id,
                           username=self.user.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=tenants)
        self.request = http.HttpRequest()
        self.request.session = self.client._session()
        self.request.session['token'] = self.token.id
        middleware.HorizonMiddleware().process_request(self.request)

    def tearDown(self):
        self.mox.UnsetStubs()
        httplib2.Http._conn_request = self._real_conn_request
        context_processors.horizon = self._real_horizon_context_processor
        users.get_user_from_request = self._real_get_user_from_request
        self.mox.VerifyAll()

    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                        service_catalog=None, tenant_name=None, roles=None,
                        authorized_tenants=None):
        users.get_user_from_request = lambda x: \
                users.User(id=id,
                           token=token,
                           user=username,
                           tenant_id=tenant_id,
                           service_catalog=service_catalog,
                           authorized_tenants=authorized_tenants)

    def override_times(self):
        """ Overrides the "current" time with immutable values. """
        now = datetime.datetime.utcnow()
        time.override_time = \
                datetime.time(now.hour, now.minute, now.second)
        today.override_time = datetime.date(now.year, now.month, now.day)
        utcnow.override_time = now
        return now

    def reset_times(self):
        """ Undoes the changes made by ``override_times``. """
        time.override_time = None
        today.override_time = None
        utcnow.override_time = None

    def assertRedirectsNoFollow(self, response, expected_url):
        """
        Asserts that the given response issued a 302 redirect without
        processing the view which is redirected to.
        """
        if response.status_code / 100 != 3:
            assert("The response did not return a redirect.")
        self.assertEqual(response._headers.get('location', None),
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)

    def assertNoMessages(self):
        """
        Asserts that no messages have been attached by the ``contrib.messages``
        framework.
        """
        self.assertMessageCount(success=0, warn=0, info=0, error=0)

    def assertMessageCount(self, **kwargs):
        """
        Asserts that the specified number of messages have been attached
        for various message types. Usage would look like
        ``self.assertMessageCount(success=1)``.
        """
        temp_req = self.client.request(**{'wsgi.input': None})
        temp_req.COOKIES = self.client.cookies
        storage = default_storage(temp_req)
        # To gain early access to the messages we have to decode the
        # cookie on the test client.
        if 'messages' in self.client.cookies:
            messages = storage._decode(self.client.cookies['messages'].value)
        elif any(kwargs.values()):
            error_msg = "Messages were expected, but none were set."
            assert 0 == sum(kwargs.values()), error_msg

        for msg_type, count in kwargs.items():
            msgs = [m.message for m in messages if msg_type in m.tags]
            assert len(msgs) == count, \
                   "%s messages not as expected: %s" % (msg_type.title(),
                                                        ", ".join(msgs))

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


class BaseAdminViewTests(TestCase):
    """
    A ``TestCase`` subclass which sets an active user with the "admin" role
    for testing admin-only views and functionality.
    """
    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                      service_catalog=None, tenant_name=None, roles=None,
                      authorized_tenants=None):
        users.get_user_from_request = lambda x: \
                users.User(id=self.user.id,
                           token=self.token.id,
                           user=self.user.name,
                           tenant_id=self.tenant.id,
                           service_catalog=self.service_catalog,
                           roles=[self.roles.admin._info],
                           authorized_tenants=None)


class APITestCase(TestCase):
    """
    The ``APITestCase`` class is for use with tests which deal with the
    underlying clients rather than stubbing out the horizon.api.* methods.
    """
    def setUp(self):
        super(APITestCase, self).setUp()

        def fake_keystoneclient(request, username=None, password=None,
                                tenant_id=None, token_id=None, endpoint=None):
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

        # Replace the clients with our stubs.
        api.glance.glanceclient = lambda request: self.stub_glanceclient()
        api.keystone.keystoneclient = fake_keystoneclient
        api.nova.novaclient = lambda request: self.stub_novaclient()

    def tearDown(self):
        super(APITestCase, self).tearDown()
        api.glance.glanceclient = self._original_glanceclient
        api.nova.novaclient = self._original_novaclient
        api.keystone.keystoneclient = self._original_keystoneclient

    def stub_novaclient(self):
        if not hasattr(self, "novaclient"):
            self.mox.StubOutWithMock(nova_client, 'Client')
            self.novaclient = self.mox.CreateMock(nova_client.Client)
        return self.novaclient

    def stub_keystoneclient(self):
        if not hasattr(self, "keystoneclient"):
            self.mox.StubOutWithMock(keystone_client, 'Client')
            self.keystoneclient = self.mox.CreateMock(keystone_client.Client)
        return self.keystoneclient

    def stub_glanceclient(self):
        if not hasattr(self, "glanceclient"):
            self.mox.StubOutWithMock(glance_client, 'Client')
            self.glanceclient = self.mox.CreateMock(glance_client.Client)
            self.glanceclient.token = self.tokens.first().id
        return self.glanceclient

    def stub_swiftclient(self, expected_calls=1):
        if not hasattr(self, "swiftclient"):
            self.mox.StubOutWithMock(swift_client, 'Connection')
            self.swiftclient = self.mox.CreateMock(swift_client.Connection)
            while expected_calls:
                swift_client.Connection(auth=mox.IgnoreArg())\
                            .AndReturn(self.swiftclient)
                expected_calls -= 1
        return self.swiftclient
