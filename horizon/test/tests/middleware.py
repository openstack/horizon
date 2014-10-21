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

import time

from django.conf import settings

from django.http import HttpResponseRedirect  # noqa

from horizon import exceptions
from horizon import middleware
from horizon.test import helpers as test


class MiddlewareTests(test.TestCase):
    def test_redirect_login_fail_to_login(self):
        url = settings.LOGIN_URL
        request = self.factory.post(url)

        mw = middleware.HorizonMiddleware()
        resp = mw.process_exception(request, exceptions.NotAuthorized())
        resp.client = self.client

        self.assertRedirects(resp, url)

    def test_session_timeout(self):
        requested_url = '/project/instances/'
        request = self.factory.get(requested_url)
        try:
            timeout = settings.SESSION_TIMEOUT
        except AttributeError:
            timeout = 1800
        request.session['last_activity'] = int(time.time()) - (timeout + 10)
        mw = middleware.HorizonMiddleware()
        resp = mw.process_request(request)
        self.assertEqual(302, resp.status_code)
        self.assertEqual(requested_url, resp.get('Location'))

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
