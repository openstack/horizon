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

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.utils.six.moves.urllib.parse import urlsplit  # noqa

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:settings:password:index')


class ChangePasswordTests(test.TestCase):

    @test.create_stubs({api.keystone: ('user_update_own_password', )})
    def test_change_password(self):
        api.keystone.user_update_own_password(IsA(http.HttpRequest),
                                              'oldpwd',
                                              'normalpwd',).AndReturn(None)
        self.mox.ReplayAll()

        formData = {'method': 'PasswordForm',
                    'current_password': 'oldpwd',
                    'new_password': 'normalpwd',
                    'confirm_password': 'normalpwd'}
        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)

    def test_change_validation_passwords_not_matching(self):
        formData = {'method': 'PasswordForm',
                    'current_password': 'currpasswd',
                    'new_password': 'testpassword',
                    'confirm_password': 'doesnotmatch'}
        res = self.client.post(INDEX_URL, formData)

        self.assertFormError(res, "form", None, ['Passwords do not match.'])

    @test.create_stubs({api.keystone: ('user_update_own_password', )})
    def test_change_password_sets_logout_reason(self):
        api.keystone.user_update_own_password(IsA(http.HttpRequest),
                                              'oldpwd',
                                              'normalpwd').AndReturn(None)
        self.mox.ReplayAll()

        formData = {'method': 'PasswordForm',
                    'current_password': 'oldpwd',
                    'new_password': 'normalpwd',
                    'confirm_password': 'normalpwd'}
        res = self.client.post(INDEX_URL, formData, follow=False)

        self.assertRedirectsNoFollow(res, settings.LOGOUT_URL)
        self.assertIn('logout_reason', res.cookies)
        self.assertEqual(res.cookies['logout_reason'].value,
                         "Password changed. Please log in again to continue.")
        scheme, netloc, path, query, fragment = urlsplit(res.url)
        redirect_response = res.client.get(path, http.QueryDict(query))
        self.assertRedirectsNoFollow(redirect_response, settings.LOGIN_URL)
