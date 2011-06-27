import mox

from django import http
from django import test

from django_openstack import api

TEST_TENANT_ID = '1234'

class Tenant(object):
    def __init__(self, id, description, enabled):
        self.id = id
        self.description = description
        self.enabled = enabled

    def __eq__(self, other):
        return self.id == other.id and \
               self.description == other.description and \
               self.enabled == other.enabled

    def __ne__(self, other):
        return not self.__eq__(other)

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

        tenant_list = [Tenant(TEST_TENANT_ID,
                              TEST_TENANT_ID + '_desc',
                              True),
                       Tenant('notTheDroid',
                              'notTheDroid_desc',
                              False)
                      ]
        tenants_mock.for_token('aToken').AndReturn(tenant_list)

        request_mock = self.mox.CreateMock(http.HttpResponse)
        request_mock.session = {'token': 'aToken'}

        self.mox.ReplayAll()

        ret_val = api.token_get_tenant(request, TEST_TENANT_ID)
        self.assertEqual(ret_val, tenant_list[0])

        self.mox.VerifyAll()

    def test_token_get_tenant_no_tenant(self):
        self.failIf(True)

    def test_token_list_tenants(self):
        self.failIf(True)

    def test_tenant_create(self):
        self.failIf(True)

    def test_token_create(self):
        self.failIf(True)

