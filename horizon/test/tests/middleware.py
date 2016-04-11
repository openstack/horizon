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

import django
from django.conf import settings
from django.http import HttpResponseRedirect  # noqa
from django.utils import timezone

from horizon import exceptions
from horizon import middleware
from horizon.test import helpers as test


class MiddlewareTests(test.TestCase):

    def setUp(self):
        self._timezone_backup = timezone.get_current_timezone_name()
        return super(MiddlewareTests, self).setUp()

    def tearDown(self):
        timezone.activate(self._timezone_backup)
        return super(MiddlewareTests, self).tearDown()

    def test_redirect_login_fail_to_login(self):
        url = settings.LOGIN_URL
        request = self.factory.post(url)

        mw = middleware.HorizonMiddleware()
        resp = mw.process_exception(request, exceptions.NotAuthorized())
        resp.client = self.client

        if django.VERSION >= (1, 9):
            self.assertRedirects(resp, settings.TESTSERVER + url)
        else:
            self.assertRedirects(resp, url)

    def test_process_response_redirect_on_ajax_request(self):
        url = settings.LOGIN_URL
        mw = middleware.HorizonMiddleware()

        request = self.factory.post(url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.horizon = {'async_messages':
                           [('error', 'error_msg', 'extra_tag')]}

        response = HttpResponseRedirect(url)
        response.client = self.client

        resp = mw.process_response(request, response)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(url, resp['X-Horizon-Location'])

    def test_timezone_awareness(self):
        url = settings.LOGIN_REDIRECT_URL
        mw = middleware.HorizonMiddleware()

        request = self.factory.get(url)
        request.session['django_timezone'] = 'America/Chicago'
        mw.process_request(request)
        self.assertEqual(
            timezone.get_current_timezone_name(), 'America/Chicago')
        request.session['django_timezone'] = 'Europe/Paris'
        mw.process_request(request)
        self.assertEqual(timezone.get_current_timezone_name(), 'Europe/Paris')
        request.session['django_timezone'] = 'UTC'
        mw.process_request(request)
        self.assertEqual(timezone.get_current_timezone_name(), 'UTC')
