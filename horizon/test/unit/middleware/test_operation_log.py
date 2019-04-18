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

import mock
from mock import patch

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponseRedirect
from django import test as django_test
from django.test.utils import override_settings

from horizon import defaults
from horizon import middleware
from horizon.test import helpers as test


class OperationLogMiddlewareTest(django_test.TestCase):

    http_host = u'test_host'
    http_referer = u'/dashboard/test_http_referer'

    def setUp(self):
        super(OperationLogMiddlewareTest, self).setUp()
        self.factory = test.RequestFactoryWithMessages()

    def test_middleware_not_used(self):
        get_response = mock.Mock()
        with self.assertRaises(MiddlewareNotUsed):
            middleware.OperationLogMiddleware(get_response)
        self.assertFalse(get_response.called)

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

    def _test_ready_for_get(self, url=None):
        if url is None:
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
        request, response = self._test_ready_for_post()
        get_response = mock.Mock(return_value=response)
        olm = middleware.OperationLogMiddleware(get_response)

        resp = olm(request)

        get_response.assert_called_once_with(request)
        self.assertTrue(mock_logger.info.called)
        self.assertEqual(302, resp.status_code)
        log_args = mock_logger.info.call_args[0]
        logging_str = log_args[0] % log_args[1]
        self.assertIn(request.user.username, logging_str)
        self.assertIn(self.http_referer, logging_str)
        self.assertIn(settings.LOGIN_URL, logging_str)
        self.assertIn('POST', logging_str)
        self.assertIn('302', logging_str)
        post_data = ['"username": "admin"', '"password": "********"']
        for data in post_data:
            self.assertIn(data, logging_str)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @test.update_settings(OPERATION_LOG_OPTIONS={'target_methods': ['GET']})
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_response_for_get(self, mock_logger):
        request, response = self._test_ready_for_get()
        get_response = mock.Mock(return_value=response)
        olm = middleware.OperationLogMiddleware(get_response)

        resp = olm(request)

        get_response.assert_called_once_with(request)
        self.assertTrue(mock_logger.info.called)
        self.assertEqual(302, resp.status_code)
        log_args = mock_logger.info.call_args[0]
        logging_str = log_args[0] % log_args[1]
        self.assertIn(request.user.username, logging_str)
        self.assertIn(self.http_referer, logging_str)
        self.assertIn(request.path, logging_str)
        self.assertIn('GET', logging_str)
        self.assertIn('302', logging_str)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_response_for_get_no_target(self, mock_logger):
        """In default setting, Get method is not logged"""
        request, response = self._test_ready_for_get()
        get_response = mock.Mock(return_value=response)
        olm = middleware.OperationLogMiddleware(get_response)

        resp = olm(request)

        get_response.assert_called_once_with(request)
        self.assertEqual(0, mock_logger.info.call_count)
        self.assertEqual(302, resp.status_code)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_process_exception(self, mock_logger):
        request, response = self._test_ready_for_post()
        get_response = mock.Mock(return_value=response)
        olm = middleware.OperationLogMiddleware(get_response)
        exception = Exception("Unexpected error occurred.")

        olm.process_exception(request, exception)

        self.assertFalse(get_response.called)
        log_args = mock_logger.info.call_args[0]
        logging_str = log_args[0] % log_args[1]
        self.assertTrue(mock_logger.info.called)
        self.assertIn(request.user.username, logging_str)
        self.assertIn(self.http_referer, logging_str)
        self.assertIn(settings.LOGIN_URL, logging_str)
        self.assertIn('Unexpected error occurred.', logging_str)
        post_data = ['"username": "admin"', '"password": "********"']
        for data in post_data:
            self.assertIn(data, logging_str)

    @override_settings(OPERATION_LOG_ENABLED=True)
    @test.update_settings(OPERATION_LOG_OPTIONS={'target_methods': ['GET']})
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_get_log_format(self, mock_logger):
        get_response = mock.Mock()
        olm = middleware.OperationLogMiddleware(get_response)
        request, _ = self._test_ready_for_get()

        self.assertEqual(
            defaults.OPERATION_LOG_OPTIONS['format'],
            olm._get_log_format(request))

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_get_log_format_no_user(self, mock_logger):
        get_response = mock.Mock()
        olm = middleware.OperationLogMiddleware(get_response)
        request, _ = self._test_ready_for_get()
        delattr(request, "user")

        self.assertIsNone(olm._get_log_format(request))

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_get_log_format_unknown_method(self, mock_logger):
        get_response = mock.Mock()
        olm = middleware.OperationLogMiddleware(get_response)
        request, _ = self._test_ready_for_get()
        request.method = "FAKE"

        self.assertIsNone(olm._get_log_format(request))

    @override_settings(OPERATION_LOG_ENABLED=True)
    @patch(('horizon.middleware.operation_log.OperationLogMiddleware.'
            'OPERATION_LOG'))
    def test_get_log_format_ignored_url(self, mock_logger):
        get_response = mock.Mock()
        olm = middleware.OperationLogMiddleware(get_response)
        request, _ = self._test_ready_for_get("/api/policy")

        self.assertIsNone(olm._get_log_format(request))
