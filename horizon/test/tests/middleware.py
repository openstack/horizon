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
from mock import patch

import django
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponseRedirect  # noqa
from django.test.utils import override_settings
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


class OperationLogMiddlewareTest(test.TestCase):

    http_host = u'test_host'
    http_referer = u'/dashboard/test_http_referer'

    def test_middleware_not_used(self):
        with self.assertRaises(MiddlewareNotUsed):
            middleware.OperationLogMiddleware()

    def _test_ready_for_post(self):
        url = settings.LOGIN_URL
        request = self.factory.post(url)
        request.META['HTTP_HOST'] = self.http_host
        request.META['HTTP_REFERER'] = self.http_referer
        request.POST = {
            "username": u"admin",
            "password": u"pass"
        }
        request.user.username = u'test_user_name'
        response = HttpResponseRedirect(url)
        response.client = self.client

        return request, response

    def _test_ready_for_get(self):
        url = '/dashboard/project/?start=2016-03-01&end=2016-03-11'
        request = self.factory.get(url)
        request.META['HTTP_HOST'] = self.http_host
        request.META['HTTP_REFERER'] = self.http_referer
        request.user.username = u'test_user_name'
        response = HttpResponseRedirect(url)
        response.client = self.client

        return request, response

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_response_for_post(self, mock_logger):
        olm = middleware.OperationLogMiddleware()
        request, response = self._test_ready_for_post()

        resp = olm.process_response(request, response)

        self.assertTrue(mock_logger.info.called)
        self.assertEqual(302, resp.status_code)
        log_args = mock_logger.info.call_args[0]
        logging_str = log_args[0] % log_args[1]
        self.assertTrue(request.user.username in logging_str)
        self.assertTrue(self.http_referer in logging_str)
        self.assertTrue(settings.LOGIN_URL in logging_str)
        self.assertTrue('POST' in logging_str)
        self.assertTrue('302' in logging_str)
        post_data = ['"username": "admin"', '"password": "********"']
        for data in post_data:
            self.assertTrue(data in logging_str)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @override_settings(OPERATION_LOG_OPTIONS={'target_methods': ['GET']})
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_response_for_get(self, mock_logger):
        olm = middleware.OperationLogMiddleware()
        request, response = self._test_ready_for_get()

        resp = olm.process_response(request, response)

        self.assertTrue(mock_logger.info.called)
        self.assertEqual(302, resp.status_code)
        log_args = mock_logger.info.call_args[0]
        logging_str = log_args[0] % log_args[1]
        self.assertTrue(request.user.username in logging_str)
        self.assertTrue(self.http_referer in logging_str)
        self.assertTrue(request.path in logging_str)
        self.assertTrue('GET' in logging_str)
        self.assertTrue('302' in logging_str)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_response_for_get_no_target(self, mock_logger):
        """In default setting, Get method is not logged"""
        olm = middleware.OperationLogMiddleware()
        request, response = self._test_ready_for_get()

        resp = olm.process_response(request, response)

        self.assertEqual(0, mock_logger.info.call_count)
        self.assertEqual(302, resp.status_code)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_exception(self, mock_logger):
        olm = middleware.OperationLogMiddleware()
        request, response = self._test_ready_for_post()
        exception = Exception("Unexpected error occured.")

        olm.process_exception(request, exception)

        log_args = mock_logger.info.call_args[0]
        logging_str = log_args[0] % log_args[1]
        self.assertTrue(mock_logger.info.called)
        self.assertTrue(request.user.username in logging_str)
        self.assertTrue(self.http_referer in logging_str)
        self.assertTrue(settings.LOGIN_URL in logging_str)
        self.assertTrue('Unexpected error occured.' in logging_str)
        post_data = ['"username": "admin"', '"password": "********"']
        for data in post_data:
            self.assertTrue(data in logging_str)
