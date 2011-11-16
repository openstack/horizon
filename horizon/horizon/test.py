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
from django import shortcuts
from django import test as django_test
from django import template as django_template
from django.conf import settings
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

        self._real_horizon_context_processor = context_processors.horizon
        context_processors.horizon = lambda request: self.TEST_CONTEXT

        self._real_get_user_from_request = users.get_user_from_request
        self.setActiveUser(token=self.TEST_TOKEN,
                           username=self.TEST_USER,
                           tenant_id=self.TEST_TENANT,
                           service_catalog=self.TEST_SERVICE_CATALOG)
        self.request = http.HttpRequest()
        middleware.HorizonMiddleware().process_request(self.request)

    def tearDown(self):
        self.mox.UnsetStubs()
        context_processors.horizon = self._real_horizon_context_processor
        users.get_user_from_request = self._real_get_user_from_request

    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                        service_catalog=None, tenant_name=None, roles=None):
        users.get_user_from_request = lambda x: \
                users.User(id=id,
                           token=token,
                           user=username,
                           tenant_id=tenant_id,
                           service_catalog=service_catalog)

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


def fake_render_to_response(template_name, context, context_instance=None,
                            mimetype='text/html'):
    """Replacement for render_to_response so that views can be tested
       without having to stub out templates that belong in the frontend
       implementation.

       Should be able to be tested using the django unit test assertions like a
       normal render_to_response return value can be.
    """
    class Template(object):
        def __init__(self, name):
            self.name = name

    if context_instance is None:
        context_instance = django_template.Context(context)
    else:
        context_instance.update(context)

    resp = http.HttpResponse()
    template = Template(template_name)

    resp.write('<html><body><p>'
               'This is a fake httpresponse for testing purposes only'
               '</p></body></html>')

    # Allows django.test.client to populate fields on the response object
    django_test.signals.template_rendered.send(template, template=template,
                                               context=context_instance)

    return resp


class BaseViewTests(TestCase):
    """
    Base class for view based unit tests.
    """
    def setUp(self):
        super(BaseViewTests, self).setUp()
        self._real_render_to_response = shortcuts.render_to_response
        shortcuts.render_to_response = fake_render_to_response

    def tearDown(self):
        super(BaseViewTests, self).tearDown()
        shortcuts.render_to_response = self._real_render_to_response

    def assertRedirectsNoFollow(self, response, expected_url):
        self.assertEqual(response._headers['location'],
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)


class BaseAdminViewTests(BaseViewTests):
    def setActiveUser(self, id=None, token=None, username=None, tenant_id=None,
                    service_catalog=None, tenant_name=None, roles=None):
        users.get_user_from_request = lambda x: \
                users.User(id=self.TEST_USER_ID,
                           token=self.TEST_TOKEN,
                           user=self.TEST_USER,
                           tenant_id=self.TEST_TENANT,
                           service_catalog=self.TEST_SERVICE_CATALOG,
                           roles=self.TEST_ROLES)
