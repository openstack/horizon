import mox

from django import http
from django import test

from django_openstack import api

TEST_PASSWORD = '12345'
TEST_RETURN = 'retValue'
TEST_TENANT_DESCRIPTION = 'tenantDescription'
TEST_TENANT_ID = '1234'
TEST_USERNAME = 'testUser'
TEST_TOKEN_ID = 'userId'

class Tenant(object):
    ''' More or less fakes what the api is looking for '''
    def __init__(self, id, description, enabled):
        self.id = id
        self.description = description
        self.enabled = enabled

    def __eq__(self, other):
        return self.id == other.id and \
               self.description == other.description and \
               self.enabled == other.enabled

    def __ne__(self, other):
        return not self == other

class Token(object):
    ''' More or less fakes what the api is looking for '''
    def __init__(self, id, username, tenant_id):
        self.id = id
        self.username = username
        self.tenant_id = tenant_id

    def __eq__(self, other):
        return self.id == other.id and \
               self.username == other.username and \
               self.tenant_id == other.tenant_id

    def __ne__(self, other):
        return not self == other

class AuthApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_token_get_tenant(self):
        self.mox.StubOutWithMock(api, 'auth_api')
        auth_api_mock = self.mox.CreateMockAnything()
        api.auth_api().AndReturn(auth_api_mock)

        tenants_mock = self.mox.CreateMockAnything()
        auth_api_mock.tenants = tenants_mock

        tenant_list = [Tenant('notTheDroid',
                              'notTheDroid_desc',
                              False),
                       Tenant(TEST_TENANT_ID,
                              TEST_TENANT_DESCRIPTION,
                              True),
                      ]
        tenants_mock.for_token('aToken').AndReturn(tenant_list)

        request_mock = self.mox.CreateMock(http.HttpResponse)
        request_mock.session = {'token': 'aToken'}

        self.mox.ReplayAll()

        ret_val = api.token_get_tenant(request_mock, TEST_TENANT_ID)
        self.assertEqual(tenant_list[1], ret_val)

        self.mox.VerifyAll()

    def test_token_get_tenant_no_tenant(self):
        self.mox.StubOutWithMock(api, 'auth_api')
        auth_api_mock = self.mox.CreateMockAnything()
        api.auth_api().AndReturn(auth_api_mock)

        tenants_mock = self.mox.CreateMockAnything()
        auth_api_mock.tenants = tenants_mock

        tenant_list = [Tenant('notTheDroid',
                              'notTheDroid_desc',
                              False),
                      ]
        tenants_mock.for_token('aToken').AndReturn(tenant_list)

        request_mock = self.mox.CreateMock(http.HttpResponse)
        request_mock.session = {'token': 'aToken'}

        self.mox.ReplayAll()

        ret_val = api.token_get_tenant(request_mock, TEST_TENANT_ID)
        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_token_list_tenants(self):
        self.mox.StubOutWithMock(api, 'auth_api')
        auth_api_mock = self.mox.CreateMockAnything()
        api.auth_api().AndReturn(auth_api_mock)

        tenants_mock = self.mox.CreateMockAnything()
        auth_api_mock.tenants = tenants_mock

        tenant_list = [Tenant('notTheDroid',
                              'notTheDroid_desc',
                              False),
                       Tenant(TEST_TENANT_ID,
                              TEST_TENANT_DESCRIPTION,
                              True),
                      ]
        tenants_mock.for_token('aToken').AndReturn(tenant_list)

        request_mock = self.mox.CreateMock(http.HttpResponse)

        self.mox.ReplayAll()

        ret_val = api.token_list_tenants(request_mock, 'aToken')
        for tenant in ret_val:
            self.assertIn(tenant, tenant_list)

        self.mox.VerifyAll()

    def test_token_create(self):
        self.mox.StubOutWithMock(api, 'auth_api')
        auth_api_mock = self.mox.CreateMockAnything()
        api.auth_api().AndReturn(auth_api_mock)

        tokens_mock = self.mox.CreateMockAnything()
        auth_api_mock.tokens = tokens_mock

        test_token = Token(TEST_TOKEN_ID, TEST_USERNAME, TEST_TENANT_ID)

        tokens_mock.create(TEST_TENANT_ID, TEST_USERNAME,
                           TEST_PASSWORD).AndReturn(test_token)

        request_mock = self.mox.CreateMock(http.HttpResponse)

        self.mox.ReplayAll()

        ret_val = api.token_create(request_mock, TEST_TENANT_ID,
                                   TEST_USERNAME, TEST_PASSWORD)

        self.assertEqual(test_token, ret_val)

        self.mox.VerifyAll()

class GlanceApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_image_all_metadata(self):
        self.failIf(True)

    
