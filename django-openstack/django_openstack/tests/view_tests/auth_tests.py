from django import http
from django.core.urlresolvers import reverse
from django.utils import unittest
from django_openstack import api
from django_openstack.tests.view_tests import base
from openstackx.api import exceptions as api_exceptions
from mox import IsA


class AuthViewTests(base.BaseViewTests):
    def setUp(self):
        super(AuthViewTests, self).setUp()
        self.setActiveUser(None, None, None, None, None)
        self.PASSWORD = 'secret'

    def test_login_index(self):
        res = self.client.get(reverse('auth_login'))
        self.assertTemplateUsed(res, 'splash.html')

    def test_login_user_logged_in(self):
        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           False, self.TEST_SERVICE_CATALOG)

        res = self.client.get(reverse('auth_login'))
        self.assertRedirectsNoFollow(res, reverse('dash_overview'))

    def test_login_admin_logged_in(self):
        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           True, self.TEST_SERVICE_CATALOG)

        res = self.client.get(reverse('auth_login'))
        self.assertRedirectsNoFollow(res, reverse('syspanel_overview'))

    def test_login(self):
        TOKEN_ID = 1

        form_data = {'method': 'Login',
                    'password': self.PASSWORD,
                    'username': self.TEST_USER}

        self.mox.StubOutWithMock(api, 'token_create')
        aToken = self.mox.CreateMock(api.Token)
        aToken.id = TOKEN_ID
        aToken.serviceCatalog = {}
        api.token_create(IsA(http.HttpRequest), "", self.TEST_USER,
                         self.PASSWORD).AndReturn(aToken)

        self.mox.StubOutWithMock(api, 'token_info')
        tokenInfo = {'user': self.TEST_USER,
                     'tenant': self.TEST_TENANT,
                     'admin': False}
        api.token_info(IsA(http.HttpRequest), aToken).AndReturn(tokenInfo)

        self.mox.ReplayAll()

        res = self.client.post(reverse('auth_login'), form_data)

        self.assertRedirectsNoFollow(res, reverse('dash_overview'))

        self.mox.VerifyAll()

    def test_login_invalid_credentials(self):
        form_data = {'method': 'Login',
                    'password': self.PASSWORD,
                    'username': self.TEST_USER}

        self.mox.StubOutWithMock(api, 'token_create')
        unauthorized = api_exceptions.Unauthorized('unauth', message='unauth')
        api.token_create(IsA(http.HttpRequest), "", self.TEST_USER,
                         self.PASSWORD).AndRaise(unauthorized)

        self.mox.ReplayAll()

        res = self.client.post(reverse('auth_login'), form_data)

        self.assertTemplateUsed(res, 'splash.html')

        self.mox.VerifyAll()

    def test_login_exception(self):
        form_data = {'method': 'Login',
                    'password': self.PASSWORD,
                    'username': self.TEST_USER}

        self.mox.StubOutWithMock(api, 'token_create')
        api_exception = api_exceptions.ApiException('apiException',
                                                    message='apiException')
        api.token_create(IsA(http.HttpRequest), "", self.TEST_USER,
                         self.PASSWORD).AndRaise(api_exception)

        self.mox.ReplayAll()

        res = self.client.post(reverse('auth_login'), form_data)

        self.assertTemplateUsed(res, 'splash.html')

        self.mox.VerifyAll()

    def test_switch_tenants_index(self):
        res = self.client.get(reverse('auth_switch', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'switch_tenants.html')

    def test_switch_tenants(self):
        NEW_TENANT = 'newTenant'
        TOKEN_ID = 1

        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           False, self.TEST_SERVICE_CATALOG)

        form_data = {'method': 'LoginWithTenant',
                     'password': self.PASSWORD,
                     'tenant': NEW_TENANT,
                     'username': self.TEST_USER}

        self.mox.StubOutWithMock(api, 'token_create')
        aToken = self.mox.CreateMock(api.Token)
        aToken.id = TOKEN_ID
        aToken.serviceCatalog = {}
        api.token_create(IsA(http.HttpRequest), NEW_TENANT, self.TEST_USER,
                         self.PASSWORD).AndReturn(aToken)

        self.mox.StubOutWithMock(api, 'token_info')
        tokenInfo = {'user': self.TEST_USER,
                     'tenant': NEW_TENANT,
                     'admin': False}
        api.token_info(IsA(http.HttpRequest), aToken).AndReturn(tokenInfo)

        self.mox.ReplayAll()

        res = self.client.post(reverse('auth_switch', args=[NEW_TENANT]),
                               form_data)

        self.assertRedirectsNoFollow(res, reverse('dash_overview'))
        self.assertEqual(self.client.session['tenant'], NEW_TENANT)

        self.mox.VerifyAll()

    def test_logout(self):
        KEY = 'arbitraryKeyString'
        VALUE = 'arbitraryKeyValue'
        self.assertNotIn(KEY, self.client.session)
        self.client.session[KEY] = VALUE

        res = self.client.get(reverse('auth_logout'))

        self.assertRedirectsNoFollow(res, reverse('splash'))
        self.assertNotIn(KEY, self.client.session)
