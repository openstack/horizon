# Copyright 2013 Centrin Data Systems Ltd.
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

from unittest import mock
from urllib.parse import urlsplit

from django.conf import settings
from django import http
from django.urls import reverse


from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:settings:password:index')


class ChangePasswordTests(test.TestCase):

    @test.create_mocks({
        api.keystone: ['user_update_own_password', 'user_get']})
    def test_change_password(self):
        self.mock_user_update_own_password.return_value = None
        self.mock_user_get.return_value = mock.Mock(options={})

        formData = {'method': 'PasswordForm',
                    'current_password': 'oldpwd',
                    'new_password': 'normalpwd',
                    'confirm_password': 'normalpwd'}
        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_user_update_own_password.assert_called_once_with(
            test.IsHttpRequest(), 'oldpwd', 'normalpwd')

    @test.create_mocks({
        api.keystone: ['user_update_own_password', 'user_get']})
    def test_change_password_sets_logout_reason(self):

        self.mock_user_update_own_password.return_value = None
        self.mock_user_get.return_value = mock.Mock(options={})

        formData = {'method': 'PasswordForm',
                    'current_password': 'oldpwd',
                    'new_password': 'normalpwd',
                    'confirm_password': 'normalpwd'}
        res = self.client.post(INDEX_URL, formData, follow=False)

        self.assertRedirectsNoFollow(res, settings.LOGOUT_URL)
        self.assertIn('logout_reason', res.cookies)
        self.assertIn('logout_status', res.cookies)
        self.assertEqual(res.cookies['logout_reason'].value,
                         "Password changed. Please log in again to continue.")
        self.assertEqual('success', res.cookies['logout_status'].value)
        scheme, netloc, path, query, fragment = urlsplit(res.url)
        redirect_response = res.client.get(path, http.QueryDict(query))
        self.assertRedirectsNoFollow(redirect_response, settings.LOGIN_URL)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_user_update_own_password.assert_called_once_with(
            test.IsHttpRequest(), 'oldpwd', 'normalpwd')

    def test_change_validation_passwords_not_matching(self):
        formData = {'method': 'PasswordForm',
                    'current_password': 'currpasswd',
                    'new_password': 'testpassword',
                    'confirm_password': 'doesnotmatch'}
        res = self.client.post(INDEX_URL, formData)

        self.assertFormError(res, "form", None, ['Passwords do not match.'])

    @test.create_mocks({
        api.keystone: ['user_get']})
    def test_lock_password(self):
        self.mock_user_get.return_value = mock.Mock(
            options={'lock_password': True})
        formData = {'method': 'PasswordForm',
                    'current_password': 'oldpwd',
                    'new_password': 'normalpwd',
                    'confirm_password': 'normalpwd'}
        res = self.client.post(INDEX_URL, formData)
        self.assertNoFormErrors(res)
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
