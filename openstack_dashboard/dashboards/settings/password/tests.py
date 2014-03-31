# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.core.urlresolvers import NoReverseMatch  # noqa
from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

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
    def test_change_password_shows_message_on_login_page(self):
        api.keystone.user_update_own_password(IsA(http.HttpRequest),
                                              'oldpwd',
                                              'normalpwd').AndReturn(None)
        self.mox.ReplayAll()

        formData = {'method': 'PasswordForm',
                    'current_password': 'oldpwd',
                    'new_password': 'normalpwd',
                    'confirm_password': 'normalpwd'}
        res = self.client.post(INDEX_URL, formData, follow=True)

        info_msg = "Password changed. Please log in again to continue."
        self.assertContains(res, info_msg)
