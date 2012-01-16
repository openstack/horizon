# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django import http
from django import test as django_test
from django.conf import settings
from django.contrib.messages.storage import default_storage
from django.test.client import RequestFactory
import httplib2
import mox

from horizon import context_processors
from horizon import middleware
from horizon import users


def time():
    '''Overrideable version of datetime.datetime.today'''
    if time.override_time:
        return time.override_time
    return datetime.time()

time.override_time = None


def today():
    '''Overridable version of datetime.datetime.today'''
    if today.override_time:
        return today.override_time
    return datetime.datetime.today()

today.override_time = None


def utcnow():
    '''Overridable version of datetime.datetime.utcnow'''
    if utcnow.override_time:
        return utcnow.override_time
    return datetime.datetime.utcnow()

utcnow.override_time = None


class RequestFactoryWithMessages(RequestFactory):
    def post(self, *args, **kwargs):
        req = super(RequestFactoryWithMessages, self).post(*args, **kwargs)
        req.session = []
        req._messages = default_storage(req)
        return req


class TestCase(django_test.TestCase):
    TEST_STAFF_USER = 'staffUser'
    TEST_TENANT = '1'
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'
    TEST_USER_ID = '1'
    TEST_ROLES = [{'name': 'admin', 'id': '1'}]
    TEST_CONTEXT = {'authorized_tenants': [{'enabled': True,
                                            'name': 'aTenant',
                                            'id': '1',
                                            'description': "None"}],
                    'object_store_configured': False,
                    'network_configured': False}

    TEST_SERVICE_CATALOG = [
        {"endpoints": [{
            "adminURL": "http://cdn.admin-nets.local:8774/v1.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:8774/v1.0",
            "publicURL": "http://cdn.admin-nets.local:8774/v1.0/"}],
        "type": "nova_compat",
        "name": "nova_compat"},
        {"endpoints": [{
            "adminURL": "http://nova/novapi/admin",
            "region": "RegionOne",
            "internalURL": "http://nova/novapi/internal",
            "publicURL": "http://nova/novapi/public"}],
        "type": "compute",
        "name": "nova"},
        {"endpoints": [{
            "adminURL": "http://glance/glanceapi/admin",
            "region": "RegionOne",
            "internalURL": "http://glance/glanceapi/internal",
            "publicURL": "http://glance/glanceapi/public"}],
        "type": "image",
        "name": "glance"},
        {"endpoints": [{
            "adminURL": "http://cdn.admin-nets.local:35357/v2.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:5000/v2.0",
            "publicURL": "http://cdn.admin-nets.local:5000/v2.0"}],
        "type": "identity",
        "name": "identity"},
        {"endpoints": [{
            "adminURL": "http://swift/swiftapi/admin",
            "region": "RegionOne",
            "internalURL": "http://swift/swiftapi/internal",
            "publicURL": "http://swift/swiftapi/public"}],
        "type": "object-store",
        "name": "swift"}]

    def setUp(self):
        self.mox = mox.Mox()
        self.factory = RequestFactoryWithMessages()

        def fake_conn_request(*args, **kwargs):
            raise Exception("An external URI request tried to escape through "
                            "an httplib2 client. Args: %s, kwargs: %s"
                            % (args, kwargs))
        self._real_conn_request = httplib2.Http._conn_request
        httplib2.Http._conn_request = fake_conn_request

        self._real_horizon_context_processor = context_processors.horizon
        context_processors.horizon = lambda request: self.TEST_CONTEXT

        self._real_get_user_from_request = users.get_user_from_request
        tenants = self.TEST_CONTEXT['authorized_tenants']
        self.setActiveUser(token=self.TEST_TOKEN,
                           username=self.TEST_USER,
                           tenant_id=self.TEST_TENANT,
                           service_catalog=self.TEST_SERVICE_CATALOG,
                           authorized_tenants=tenants)
        self.request = http.HttpRequest()
        self.request.session = self.client._session()
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
        now = datetime.datetime.utcnow()
        time.override_time = \
                datetime.time(now.hour, now.minute, now.second)
        today.override_time = datetime.date(now.year, now.month, now.day)
        utcnow.override_time = now

        return now

    def reset_times(self):
        time.override_time = None
        today.override_time = None
        utcnow.override_time = None


class BaseViewTests(TestCase):
    """
    Base class for view based unit tests.
    """
    def assertRedirectsNoFollow(self, response, expected_url):
        self.assertEqual(response._headers['location'],
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)


class BaseAdminViewTests(BaseViewTests):
    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                      service_catalog=None, tenant_name=None, roles=None,
                      authorized_tenants=None):
        users.get_user_from_request = lambda x: \
                users.User(id=self.TEST_USER_ID,
                           token=self.TEST_TOKEN,
                           user=self.TEST_USER,
                           tenant_id=self.TEST_TENANT,
                           service_catalog=self.TEST_SERVICE_CATALOG,
                           roles=self.TEST_ROLES,
                           authorized_tenants=None)
