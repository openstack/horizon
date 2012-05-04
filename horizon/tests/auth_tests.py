# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django import http
from django.core.urlresolvers import reverse
from keystoneclient import exceptions as keystone_exceptions
from mox import IsA

from horizon import api
from horizon import test


SYSPANEL_INDEX_URL = reverse('horizon:syspanel:overview:index')
DASH_INDEX_URL = reverse('horizon:nova:overview:index')


class AuthViewTests(test.TestCase):
    def setUp(self):
        super(AuthViewTests, self).setUp()
        self.setActiveUser()

    def test_login_index(self):
        res = self.client.get(reverse('horizon:auth_login'))
        self.assertTemplateUsed(res, 'horizon/auth/login.html')

    def test_login_user_logged_in(self):
        self.setActiveUser(self.tokens.first().id,
                           self.user.name,
                           self.tenant.id,
                           False,
                           self.service_catalog)
        # Hitting the login URL directly should always give you a login page.
        res = self.client.get(reverse('horizon:auth_login'))
        self.assertTemplateUsed(res, 'horizon/auth/login.html')

    def test_login_no_tenants(self):
        aToken = self.tokens.first()

        self.mox.StubOutWithMock(api, 'token_create')
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        api.token_create(IsA(http.HttpRequest), "", self.user.name,
                         self.user.password).AndReturn(aToken)
        api.tenant_list_for_token(IsA(http.HttpRequest), aToken.id).\
                                  AndReturn([])

        self.mox.ReplayAll()

        form_data = {'method': 'Login',
                    'region': 'http://localhost:5000/v2.0',
                    'password': self.user.password,
                    'username': self.user.name}
        res = self.client.post(reverse('horizon:auth_login'), form_data)

        self.assertTemplateUsed(res, 'horizon/auth/login.html')

    def test_login(self):
        form_data = {'method': 'Login',
                     'region': 'http://localhost:5000/v2.0',
                     'password': self.user.password,
                     'username': self.user.name}

        self.mox.StubOutWithMock(api, 'token_create')
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        self.mox.StubOutWithMock(api, 'token_create_scoped')

        aToken = self.tokens.unscoped_token
        bToken = self.tokens.scoped_token

        api.token_create(IsA(http.HttpRequest), "", self.user.name,
                         self.user.password).AndReturn(aToken)
        api.tenant_list_for_token(IsA(http.HttpRequest),
                                  aToken.id).AndReturn([self.tenants.first()])
        api.token_create_scoped(IsA(http.HttpRequest),
                                self.tenant.id,
                                aToken.id).AndReturn(bToken)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:auth_login'), form_data)
        self.assertRedirectsNoFollow(res, DASH_INDEX_URL)

    def test_login_first_tenant_invalid(self):
        form_data = {'method': 'Login',
                     'region': 'http://localhost:5000/v2.0',
                     'password': self.user.password,
                     'username': self.user.name}

        self.mox.StubOutWithMock(api, 'token_create')
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        self.mox.StubOutWithMock(api, 'token_create_scoped')

        aToken = self.tokens.unscoped_token
        bToken = self.tokens.scoped_token
        disabled_tenant = self.tenants.get(name="disabled_tenant")
        tenant = self.tenants.get(name="test_tenant")
        tenants = [tenant, disabled_tenant]
        api.token_create(IsA(http.HttpRequest), "", self.user.name,
                         self.user.password).AndReturn(aToken)
        api.tenant_list_for_token(IsA(http.HttpRequest),
                                  aToken.id).AndReturn(tenants)
        exc = keystone_exceptions.Unauthorized("Not authorized.")
        api.token_create_scoped(IsA(http.HttpRequest),
                                disabled_tenant.id,
                                aToken.id).AndRaise(exc)
        api.token_create_scoped(IsA(http.HttpRequest),
                                tenant.id,
                                aToken.id).AndReturn(bToken)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:auth_login'), form_data)
        self.assertNoFormErrors(res)
        self.assertNoMessages()
        self.assertRedirectsNoFollow(res, DASH_INDEX_URL)

    def test_login_invalid_credentials(self):
        self.mox.StubOutWithMock(api, 'token_create')
        unauthorized = keystone_exceptions.Unauthorized("Invalid")
        api.token_create(IsA(http.HttpRequest), "", self.user.name,
                         self.user.password).AndRaise(unauthorized)

        self.mox.ReplayAll()

        form_data = {'method': 'Login',
                     'region': 'http://localhost:5000/v2.0',
                     'password': self.user.password,
                     'username': self.user.name}
        res = self.client.post(reverse('horizon:auth_login'),
                               form_data,
                               follow=True)

        self.assertTemplateUsed(res, 'horizon/auth/login.html')

    def test_login_exception(self):
        self.mox.StubOutWithMock(api, 'token_create')
        ex = keystone_exceptions.BadRequest('Cannot talk to keystone')
        api.token_create(IsA(http.HttpRequest),
                         "",
                         self.user.name,
                         self.user.password).AndRaise(ex)

        self.mox.ReplayAll()

        form_data = {'method': 'Login',
                    'region': 'http://localhost:5000/v2.0',
                    'password': self.user.password,
                    'username': self.user.name}
        res = self.client.post(reverse('horizon:auth_login'), form_data)

        self.assertTemplateUsed(res, 'horizon/auth/login.html')

    def test_switch_tenants_index(self):
        res = self.client.get(reverse('horizon:auth_switch',
                                      args=[self.tenant.id]))

        self.assertRedirects(res, reverse("horizon:auth_login"))

    def test_switch_tenants(self):
        tenants = self.tenants.list()

        tenant = self.tenants.first()
        token = self.tokens.unscoped_token
        scoped_token = self.tokens.scoped_token
        switch_to = scoped_token.tenant['id']
        user = self.users.first()

        self.setActiveUser(id=user.id,
                           token=token.id,
                           username=user.name,
                           tenant_id=tenant.id,
                           service_catalog=self.service_catalog,
                           authorized_tenants=tenants)

        self.mox.StubOutWithMock(api, 'token_create')
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')

        api.token_create(IsA(http.HttpRequest),
                         switch_to,
                         user.name,
                         user.password).AndReturn(scoped_token)
        api.tenant_list_for_token(IsA(http.HttpRequest),
                                  token.id).AndReturn(tenants)
        self.mox.ReplayAll()

        form_data = {'method': 'LoginWithTenant',
                     'region': 'http://localhost:5000/v2.0',
                     'username': user.name,
                     'password': user.password,
                     'tenant': switch_to}
        switch_url = reverse('horizon:auth_switch', args=[switch_to])
        res = self.client.post(switch_url, form_data)
        self.assertRedirectsNoFollow(res, DASH_INDEX_URL)
        self.assertEqual(self.client.session['tenant'],
                         scoped_token.tenant['name'])

    def test_logout(self):
        KEY = 'arbitraryKeyString'
        VALUE = 'arbitraryKeyValue'
        self.assertNotIn(KEY, self.client.session)
        self.client.session[KEY] = VALUE

        res = self.client.get(reverse('horizon:auth_logout'))

        self.assertRedirectsNoFollow(res, reverse('splash'))
        self.assertNotIn(KEY, self.client.session)

    def test_session_fixation(self):
        session_ids = []
        form_data = {'method': 'Login',
                     'region': 'http://localhost:5000/v2.0',
                     'password': self.user.password,
                     'username': self.user.name}

        self.mox.StubOutWithMock(api, 'token_create')
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        self.mox.StubOutWithMock(api, 'token_create_scoped')

        aToken = self.tokens.unscoped_token
        bToken = self.tokens.scoped_token

        api.token_create(IsA(http.HttpRequest), "", self.user.name,
                         self.user.password).AndReturn(aToken)
        api.tenant_list_for_token(IsA(http.HttpRequest),
                                  aToken.id).AndReturn([self.tenants.first()])
        api.token_create_scoped(IsA(http.HttpRequest),
                                self.tenant.id,
                                aToken.id).AndReturn(bToken)

        api.token_create(IsA(http.HttpRequest), "", self.user.name,
                         self.user.password).AndReturn(aToken)
        api.tenant_list_for_token(IsA(http.HttpRequest),
                                  aToken.id).AndReturn([self.tenants.first()])
        api.token_create_scoped(IsA(http.HttpRequest),
                                self.tenant.id,
                                aToken.id).AndReturn(bToken)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:auth_login'))
        self.assertEqual(res.cookies.get('sessionid'), None)
        res = self.client.post(reverse('horizon:auth_login'), form_data)
        session_ids.append(res.cookies['sessionid'].value)

        self.assertEquals(self.client.session['user_name'],
                          self.user.name)
        self.client.session['foobar'] = 'MY TEST VALUE'
        res = self.client.get(reverse('horizon:auth_logout'))
        session_ids.append(res.cookies['sessionid'].value)
        self.assertEqual(len(self.client.session.items()), 0)
        # Sleep for 1 second so the session values are different if
        # using the signed_cookies backend.
        time.sleep(1)
        res = self.client.post(reverse('horizon:auth_login'), form_data)
        session_ids.append(res.cookies['sessionid'].value)
        # Make sure all 3 session id values are different
        self.assertEqual(len(session_ids), len(set(session_ids)))
