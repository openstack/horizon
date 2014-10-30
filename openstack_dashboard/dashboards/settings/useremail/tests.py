# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mox import IgnoreArg
from mox import IsA  # noqa

from django import http
from django.contrib import auth as django_auth
from django.core.urlresolvers import reverse

from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:settings:useremail:index')

class UseremailTests(test.TestCase):

    @test.create_stubs({
        api.keystone: ('user_update',
                        'user_get',
                        'keystone_can_edit_user', ),
        django_auth: ('authenticate',)

    })
    def test_change_email(self):
        user = self.user
        api.keystone.keystone_can_edit_user().AndReturn(True)

        django_auth.authenticate(request=IsA(http.HttpRequest),
                                username=user.name,
                                password=user.password,
                                user_domain_name='test_domain',
                                auth_url='http://localhost:5000/v2.0').AndReturn(None)

        api.keystone.user_get(IsA(http.HttpRequest),
                                 user.id,
                                 admin=False).AndReturn(user)

        api.keystone.user_update(IsA(http.HttpRequest),
                                            user.id,
                                            email='user@test.com',
                                            password=None,).AndReturn(None)
        self.mox.ReplayAll()

        formData = {
            'method': 'EmailForm',
            'email': 'user@test.com',
            'password': user.password
        }

        response = self.client.post(INDEX_URL, formData)
        self.assertNoFormErrors(response)
        # don't pass response to assertMessageCount because it's a redirect,
        # leave it default (None) to check the internal request object
        self.assertMessageCount(success=1)

    @test.create_stubs({
        api.keystone: ('user_get',)
    })
    def test_invalid_email(self):
        user = self.user
        api.keystone.user_get(IsA(http.HttpRequest),
                                 user.id,
                                 admin=False).AndReturn(user)
        self.mox.ReplayAll()

        formData = {
            'method': 'EmailForm',
            'email': 'BADEMAIL',
            'password': user.password
        }

        response = self.client.post(INDEX_URL, formData)
        self.assertFormError(response, "form", 'email', ['Enter a valid email address.'])
        self.assertNoMessages()

    @test.create_stubs({
        api.keystone: ('user_update',
                        'user_get',
                        'keystone_can_edit_user', ),
        django_auth: ('authenticate',)

    })
    def test_wrong_password(self):
        user = self.user
        api.keystone.keystone_can_edit_user().AndReturn(True)

        django_auth.authenticate(request=IsA(http.HttpRequest),
                                username=user.name,
                                password='wrongpassword',
                                user_domain_name='test_domain',
                                auth_url='http://localhost:5000/v2.0'
                            ).AndRaise(auth_exceptions.KeystoneAuthException)

        api.keystone.user_get(IsA(http.HttpRequest),
                                 user.id,
                                 admin=False).AndReturn(user)

        self.mox.ReplayAll()

        formData = {
            'method': 'EmailForm',
            'email': 'user@test.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(INDEX_URL, formData)
        # The password error is not a form error because is an error that
        # appears processing the form
        self.assertNoFormErrors(response)
        self.assertMessageCount(response, error=1)

    @test.create_stubs({
        api.keystone: ('user_get',)
    })
    def test_required_fields(self):
        user = self.user
        api.keystone.user_get(IsA(http.HttpRequest),
                                 user.id,
                                 admin=False).AndReturn(user)
        self.mox.ReplayAll()

        formData = {
            'method': 'EmailForm',
            'email': '',
            'password': ''
        }

        response = self.client.post(INDEX_URL, formData)
        self.assertFormError(response, 'form', 'email', ['This field is required.'])
        self.assertFormError(response, 'form', 'password', ['This field is required.'])
        self.assertNoMessages() 