# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development, Inc.
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


class APIResource(api.APIResourceWrapper):
    ''' Simple APIResource for testing '''
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerObject=None):
        if innerObject is None:
            class InnerAPIResource(object):
                pass
            innerObject = InnerAPIResource()
            innerObject.foo = 'foo'
            innerObject.bar = 'bar'
        return APIResource(innerObject)


class APIDict(api.APIDictWrapper):
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerDict=None):
        if innerDict is None:
            innerDict = {'foo': 'foo',
                         'bar': 'bar'}
        return APIDict(innerDict)


class APIResourceWrapperTests(test.TestCase):
    def test_get_attribute(self):
        resource = APIResource.get_instance()
        self.assertEqual(resource.foo, 'foo')

    def test_get_invalid_attribute(self):
        resource = APIResource.get_instance()
        with self.assertRaises(AttributeError):
            resource.missing

    def test_get_inner_missing_attribute(self):
        resource = APIResource.get_instance()
        with self.assertRaises(AttributeError):
            resource.baz


class APIDictWrapperTests(test.TestCase):
    # APIDict allows for both attribute access and dictionary style [element]
    # style access.  Test both
    def test_get_item(self):
        resource = APIDict.get_instance()
        self.assertEqual(resource.foo, 'foo')
        self.assertEqual(resource['foo'], 'foo')

    def test_get_invalid_item(self):
        resource = APIDict.get_instance()
        with self.assertRaises(AttributeError):
            resource.missing
        with self.assertRaises(KeyError):
            resource['missing']

    def test_get_inner_missing_attribute(self):
        resource = APIDict.get_instance()
        with self.assertRaises(AttributeError):
            resource.baz
        with self.assertRaises(KeyError):
            resource['baz']


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
