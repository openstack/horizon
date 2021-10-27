# Copyright (c) 2021 Wind River Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from unittest import mock

from django.conf import settings
from django.contrib.sessions.backends import signed_cookies
from django import test as django_test
from django.test.utils import override_settings

from horizon import middleware
from horizon.test import helpers as test


class SimultaneousSessionsMiddlewareTest(django_test.TestCase):

    def setUp(self):
        self.url = settings.LOGIN_URL
        self.factory = test.RequestFactoryWithMessages()
        self.get_response = mock.Mock()
        self.request = self.factory.get(self.url)
        self.request.user.pk = '123'
        super().setUp()

    @mock.patch.object(signed_cookies.SessionStore, 'delete', return_value=None)
    def test_simultaneous_sessions(self, mock_delete):
        mw = middleware.SimultaneousSessionsMiddleware(
            self.get_response)

        self.request.session._set_session_key('123456789')
        mw._process_request(self.request)
        mock_delete.assert_not_called()

        self.request.session._set_session_key('987654321')
        mw._process_request(self.request)
        mock_delete.assert_not_called()

    @override_settings(SIMULTANEOUS_SESSIONS='disconnect')
    @mock.patch.object(signed_cookies.SessionStore, 'delete', return_value=None)
    def test_disconnect_simultaneous_sessions(self, mock_delete):
        mw = middleware.SimultaneousSessionsMiddleware(
            self.get_response)

        self.request.session._set_session_key('123456789')
        mw._process_request(self.request)
        mock_delete.assert_not_called()

        self.request.session._set_session_key('987654321')
        mw._process_request(self.request)
        mock_delete.assert_called_once_with()
