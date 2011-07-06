# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development Inc.
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

"""
Base classes for view based unit tests.
"""

import mox

from django import http
from django import shortcuts
from django import template as django_template
from django import test
from django.conf import settings
from django.contrib.auth import models as auth_models


class Object(object):
    '''Inner Object for api objects'''
    pass


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
    test.signals.template_rendered.send(template, template=template,
                                        context=context_instance)

    return resp


class BaseViewTests(test.TestCase):
    TEST_PROJECT = 'test'
    TEST_STAFF_USER = 'staffUser'
    TEST_USER = 'test'
    TEST_REGION = 'test'

    @classmethod
    def setUpClass(cls):
        cls._real_render_to_response = shortcuts.render_to_response
        shortcuts.render_to_response = fake_render_to_response

    @classmethod
    def tearDownClass(cls):
        shortcuts.render_to_response = cls._real_render_to_response

    def setUp(self):
        self.mox = mox.Mox()
        self.user = self.authenticateTestUser()

    def tearDown(self):
        self.mox.UnsetStubs()

    def assertRedirectsNoFollow(self, response, expected_url):
        self.assertEqual(response._headers['location'],
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)

    def authenticateTestUser(self):
        user = auth_models.User.objects.create_user(self.TEST_USER,
                                                         'test@test.com',
                                                         password='test')
        login = self.client.login(username=self.TEST_USER, password='test')
        self.failUnless(login, 'Unable to login')
        return user

    def authenticateTestStaffUser(self):
        user = auth_models.User.objects.create_user(self.TEST_STAFF_USER,
                                                         'teststaff@test.com',
                                                         password='test')
        user.is_staff = True
        user.save()
        login = self.client.login(username=self.TEST_STAFF_USER,
                                  password='test')
        self.failUnless(login, 'Unable to login')
        return user
