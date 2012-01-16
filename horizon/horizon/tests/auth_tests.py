# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from keystoneclient import exceptions as keystone_exceptions
from mox import IsA

from horizon import api
from horizon import test


SYSPANEL_INDEX_URL = reverse('horizon:syspanel:overview:index')
DASH_INDEX_URL = reverse('horizon:nova:overview:index')


class AuthViewTests(test.BaseViewTests):
    def setUp(self):
        super(AuthViewTests, self).setUp()
        self.setActiveUser()
        self.PASSWORD = 'secret'

    def test_login_index(self):
        res = self.client.get(reverse('horizon:auth_login'))
        self.assertTemplateUsed(res, 'splash.html')

    def test_login_user_logged_in(self):
        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           False, self.TEST_SERVICE_CATALOG)

        res = self.client.get(reverse('horizon:auth_login'))
        self.assertRedirectsNoFollow(res, DASH_INDEX_URL)

    def test_login_no_tenants(self):
        NEW_TENANT_ID = '6'
        NEW_TENANT_NAME = 'FAKENAME'
        TOKEN_ID = 1

        form_data = {'method': 'Login',
                    'region': 'http://localhost:5000/v2.0,local',
                    'password': self.PASSWORD,
                    'username': self.TEST_USER}

        self.mox.StubOutWithMock(api, 'token_create')

        class FakeToken(object):
            id = TOKEN_ID,
            user = {'roles': [{'name': 'fake'}]},
            serviceCatalog = {}
        aToken = api.Token(FakeToken())

        api.token_create(IsA(http.HttpRequest), "", self.TEST_USER,
                         self.PASSWORD).AndReturn(aToken)

        aTenant = self.mox.CreateMock(api.Token)
        aTenant.id = NEW_TENANT_ID
        aTenant.name = NEW_TENANT_NAME

        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        api.tenant_list_for_token(IsA(http.HttpRequest), aToken.id).\
                                  AndReturn([])

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest),
                       IsA(unicode),
                       extra_tags=IsA(str))

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:auth_login'), form_data)

        self.assertTemplateUsed(res, 'splash.html')

    def test_login(self):
        NEW_TENANT_ID = '6'
        NEW_TENANT_NAME = 'FAKENAME'
        TOKEN_ID = 1

        form_data = {'method': 'Login',
                    'region': 'http://localhost:5000/v2.0,local',
                    'password': self.PASSWORD,
                    'username': self.TEST_USER}

        self.mox.StubOutWithMock(api, 'token_create')

        class FakeToken(object):
            id = TOKEN_ID,
            user = {"id": "1",
                    "roles": [{"id": "1", "name": "fake"}], "name": "user"}
            serviceCatalog = {}
            tenant = None
        aToken = api.Token(FakeToken())
        bToken = aToken

        api.token_create(IsA(http.HttpRequest), "", self.TEST_USER,
                         self.PASSWORD).AndReturn(aToken)

        aTenant = self.mox.CreateMock(api.Token)
        aTenant.id = NEW_TENANT_ID
        aTenant.name = NEW_TENANT_NAME
        bToken.tenant = {'id': aTenant.id, 'name': aTenant.name}

        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        api.tenant_list_for_token(IsA(http.HttpRequest), aToken.id).\
                                  AndReturn([aTenant])

        self.mox.StubOutWithMock(api, 'token_create_scoped')
        api.token_create_scoped(IsA(http.HttpRequest), aTenant.id,
                                    aToken.id).AndReturn(bToken)

        self.mox.ReplayAll()
        res = self.client.post(reverse('horizon:auth_login'), form_data)
        self.assertRedirectsNoFollow(res, DASH_INDEX_URL)

    def test_login_invalid_credentials(self):
        self.mox.StubOutWithMock(api, 'token_create')
        unauthorized = keystone_exceptions.Unauthorized("Invalid")
        api.token_create(IsA(http.HttpRequest), "", self.TEST_USER,
                         self.PASSWORD).AndRaise(unauthorized)

        self.mox.ReplayAll()

        form_data = {'method': 'Login',
                     'region': 'http://localhost:5000/v2.0,local',
                     'password': self.PASSWORD,
                     'username': self.TEST_USER}
        res = self.client.post(reverse('horizon:auth_login'),
                               form_data,
                               follow=True)

        self.assertTemplateUsed(res, 'splash.html')

    def test_login_exception(self):
        self.mox.StubOutWithMock(api, 'token_create')
        ex = keystone_exceptions.BadRequest('Cannot talk to keystone')
        api.token_create(IsA(http.HttpRequest),
                         "",
                         self.TEST_USER,
                         self.PASSWORD).AndRaise(ex)

        self.mox.ReplayAll()

        form_data = {'method': 'Login',
                    'region': 'http://localhost:5000/v2.0,local',
                    'password': self.PASSWORD,
                    'username': self.TEST_USER}
        res = self.client.post(reverse('horizon:auth_login'), form_data)

        self.assertTemplateUsed(res, 'splash.html')

    def test_switch_tenants_index(self):
        res = self.client.get(reverse('horizon:auth_switch',
                                      args=[self.TEST_TENANT]))

        self.assertRedirects(res, reverse("horizon:auth_login"))

    def test_switch_tenants(self):
        NEW_TENANT_ID = '6'
        NEW_TENANT_NAME = 'FAKENAME'
        TOKEN_ID = 1
        tenants = self.TEST_CONTEXT['authorized_tenants']

        aTenant = self.mox.CreateMock(api.Token)
        aTenant.id = NEW_TENANT_ID
        aTenant.name = NEW_TENANT_NAME

        aToken = self.mox.CreateMock(api.Token)
        aToken.id = TOKEN_ID
        aToken.user = {'id': self.TEST_USER_ID,
                       'name': self.TEST_USER, 'roles': [{'name': 'fake'}]}
        aToken.serviceCatalog = {}
        aToken.tenant = {'id': aTenant.id, 'name': aTenant.name}

        self.setActiveUser(id=self.TEST_USER_ID,
                           token=self.TEST_TOKEN,
                           username=self.TEST_USER,
                           tenant_id=self.TEST_TENANT,
                           service_catalog=self.TEST_SERVICE_CATALOG,
                           authorized_tenants=tenants)

        self.mox.StubOutWithMock(api, 'token_create')
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')

        api.token_create(IsA(http.HttpRequest), NEW_TENANT_ID, self.TEST_USER,
                         self.PASSWORD).AndReturn(aToken)
        api.tenant_list_for_token(IsA(http.HttpRequest), aToken.id) \
                                  .AndReturn([aTenant])

        self.mox.ReplayAll()

        form_data = {'method': 'LoginWithTenant',
                     'region': 'http://localhost:5000/v2.0,local',
                     'password': self.PASSWORD,
                     'tenant': NEW_TENANT_ID,
                     'username': self.TEST_USER}
        res = self.client.post(reverse('horizon:auth_switch',
                                       args=[NEW_TENANT_ID]), form_data)

        self.assertRedirectsNoFollow(res, DASH_INDEX_URL)
        self.assertEqual(self.client.session['tenant'], NEW_TENANT_NAME)

    def test_logout(self):
        KEY = 'arbitraryKeyString'
        VALUE = 'arbitraryKeyValue'
        self.assertNotIn(KEY, self.client.session)
        self.client.session[KEY] = VALUE

        res = self.client.get(reverse('horizon:auth_logout'))

        self.assertRedirectsNoFollow(res, reverse('splash'))
        self.assertNotIn(KEY, self.client.session)
