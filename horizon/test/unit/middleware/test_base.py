# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

import mock
import pytz

from django.conf import settings
from django.http import HttpResponseRedirect
from django import test as django_test
from django.test.utils import override_settings
from django.utils import timezone

from horizon import exceptions
from horizon import middleware
from horizon.test import helpers as test


class MiddlewareTests(django_test.TestCase):

    def setUp(self):
        self._timezone_backup = timezone.get_current_timezone_name()
        self.factory = test.RequestFactoryWithMessages()
        self.get_response = mock.Mock()
        super(MiddlewareTests, self).setUp()

    def tearDown(self):
        timezone.activate(self._timezone_backup)
        super(MiddlewareTests, self).tearDown()

    def test_redirect_login_fail_to_login(self):
        url = settings.LOGIN_URL
        request = self.factory.post(url)
        self.get_response.return_value = request

        mw = middleware.HorizonMiddleware(self.get_response)
        resp = mw.process_exception(request, exceptions.NotAuthenticated())
        resp.client = self.client

        self.assertRedirects(resp, settings.TESTSERVER + url)

    def test_process_response_redirect_on_ajax_request(self):
        url = settings.LOGIN_URL
        mw = middleware.HorizonMiddleware(self.get_response)

        request = self.factory.post(url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.horizon = {'async_messages':
                           [('error', 'error_msg', 'extra_tag')]}

        response = HttpResponseRedirect(url)
        response.client = self.client

        resp = mw._process_response(request, response)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(url, resp['X-Horizon-Location'])

    @override_settings(SESSION_REFRESH=False)
    def test_timezone_awareness(self):
        url = settings.LOGIN_REDIRECT_URL
        mw = middleware.HorizonMiddleware(self.get_response)

        request = self.factory.get(url)

        request.session['django_timezone'] = 'America/Chicago'
        mw._process_request(request)
        self.assertEqual(
            timezone.get_current_timezone_name(), 'America/Chicago')
        request.session['django_timezone'] = 'Europe/Paris'
        mw._process_request(request)
        self.assertEqual(timezone.get_current_timezone_name(), 'Europe/Paris')
        request.session['django_timezone'] = 'UTC'
        mw._process_request(request)
        self.assertEqual(timezone.get_current_timezone_name(), 'UTC')

    @override_settings(SESSION_TIMEOUT=600,
                       SESSION_REFRESH=True)
    def test_refresh_session_expiry_enough_token_life(self):
        url = settings.LOGIN_REDIRECT_URL
        mw = middleware.HorizonMiddleware(self.get_response)

        request = self.factory.get(url)

        now = datetime.datetime.now(pytz.utc)
        token_expiry = now + datetime.timedelta(seconds=1800)
        request.user.token = mock.Mock(expires=token_expiry)
        session_expiry_before = now + datetime.timedelta(seconds=300)
        request.session.set_expiry(session_expiry_before)

        mw._process_request(request)

        session_expiry_after = request.session.get_expiry_date()
        # Check if session_expiry has been updated.
        self.assertGreater(session_expiry_after, session_expiry_before)
        # Check session_expiry is before token expiry
        self.assertLess(session_expiry_after, token_expiry)

    @override_settings(SESSION_TIMEOUT=600,
                       SESSION_REFRESH=True)
    def test_refresh_session_expiry_near_token_expiry(self):
        url = settings.LOGIN_REDIRECT_URL
        mw = middleware.HorizonMiddleware(self.get_response)

        request = self.factory.get(url)

        now = datetime.datetime.now(pytz.utc)
        token_expiry = now + datetime.timedelta(seconds=10)
        request.user.token = mock.Mock(expires=token_expiry)

        mw._process_request(request)

        session_expiry_after = request.session.get_expiry_date()
        # Check if session_expiry_after is around token_expiry.
        # We set some margin to avoid accidental test failure.
        self.assertGreater(session_expiry_after,
                           token_expiry - datetime.timedelta(seconds=3))
        self.assertLess(session_expiry_after,
                        token_expiry + datetime.timedelta(seconds=3))

    @override_settings(SESSION_TIMEOUT=600,
                       SESSION_REFRESH=False)
    def test_no_refresh_session_expiry(self):
        url = settings.LOGIN_REDIRECT_URL
        mw = middleware.HorizonMiddleware(self.get_response)

        request = self.factory.get(url)

        now = datetime.datetime.now(pytz.utc)
        token_expiry = now + datetime.timedelta(seconds=1800)
        request.user.token = mock.Mock(expires=token_expiry)
        session_expiry_before = now + datetime.timedelta(seconds=300)
        request.session.set_expiry(session_expiry_before)

        mw._process_request(request)

        session_expiry_after = request.session.get_expiry_date()
        # Check if session_expiry has been updated.
        self.assertEqual(session_expiry_after, session_expiry_before)
