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
from mox import IsA


TEST_PASSWORD = '12345'
TEST_RETURN = 'retValue'
TEST_TENANT_DESCRIPTION = 'tenantDescription'
TEST_TENANT_ID = '1234'
TEST_USERNAME = 'testUser'
TEST_TOKEN_ID = 'userId'

class Server(object):
    ''' More or less fakes what the api is looking for '''
    def __init__(self, id, imageRef, attrs=None):
        self.id = id
        self.imageRef = imageRef
        if attrs is not None:
            self.attrs = attrs

    def __eq__(self, other):
        if self.id != other.id or \
          self.imageRef != other.imageRef:
              return False

        for k in self.attrs:
            if other.attrs.__getattr__(k) != v:
                return False

        return True

    def __ne__(self, other):
        return not self == other

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
    ''' Simple APIDict for testing '''
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
        self.assertNotIn('missing', resource._attrs,
                msg="Test assumption broken.  Find new missing attribute")
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
        self.assertNotIn('missing', resource._attrs,
                msg="Test assumption broken.  Find new missing attribute")
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

    def test_get_with_default(self):
        resource = APIDict.get_instance()

        self.assertEqual(resource.get('foo'), 'foo')

        self.assertIsNone(resource.get('baz'))

        self.assertEqual('retValue', resource.get('baz', 'retValue'))

# Wrapper classes that only define _attrs don't need extra testing.  
# Wrapper classes that have other attributes or methods need testing
class ImageWrapperTests(test.TestCase):
    dict_with_properties = {
            'properties':
                {'image_state': 'running'},
            'size': 100,
            }
    dict_without_properties = {
            'size': 100,
            }
                
    def test_get_properties(self):
        image = api.Image(self.dict_with_properties)
        image_props = image.properties
        self.assertIsInstance(image_props, api.ImageProperties)
        self.assertEqual(image_props.image_state, 'running')

    def test_get_other(self):
        image = api.Image(self.dict_with_properties)
        self.assertEqual(image.size, 100)

    def test_get_properties_missing(self):
        image = api.Image(self.dict_without_properties)
        with self.assertRaises(AttributeError):
            image.properties

    def test_get_other_missing(self):
        image = api.Image(self.dict_without_properties)
        with self.assertRaises(AttributeError):
            self.assertNotIn('missing', image._attrs,
                msg="Test assumption broken.  Find new missing attribute")
            image.missing

class ServerWrapperTests(test.TestCase):
    HOST = 'hostname'
    ID = '1'
    IMAGE_NAME = 'imageName'
    IMAGE_REF = '3'

    def setUp(self):
        self.mox = mox.Mox()

        # these are all objects "fetched" from the api
        self.inner_attrs = {'host':self.HOST}

        self.inner_server = Server(self.ID, self.IMAGE_REF, self.inner_attrs)
        self.inner_server_no_attrs = Server(self.ID, self.IMAGE_REF)

        self.request = self.mox.CreateMock(http.HttpRequest)

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_get_attrs(self):
        server = api.Server(self.inner_server, self.request)
        attrs = server.attrs
        # for every attribute in the "inner" object passed to the api wrapper,
        # see if it can be accessed through the api.ServerAttribute instance
        for k in self.inner_attrs:
            self.assertEqual(attrs.__getattr__(k), self.inner_attrs[k])

    def test_get_other(self):
        server = api.Server(self.inner_server, self.request)
        self.assertEqual(server.id, self.ID)

    def test_get_attrs_missing(self):
        server = api.Server(self.inner_server_no_attrs, self.request)
        with self.assertRaises(AttributeError):
            server.attrs

    def test_get_other_missing(self):
        server = api.Server(self.inner_server, self.request)
        with self.assertRaises(AttributeError):
            self.assertNotIn('missing', server._attrs,
                msg="Test assumption broken.  Find new missing attribute")
            server.missing

    def test_image_name(self):
        self.mox.StubOutWithMock(api, 'image_get')
        api.image_get(IsA(http.HttpRequest),
                      self.IMAGE_REF
                      ).AndReturn(api.Image({'name': self.IMAGE_NAME}))

        server = api.Server(self.inner_server, self.request)

        self.mox.ReplayAll()

        image_name = server.image_name

        self.assertEqual(image_name, self.IMAGE_NAME)

        self.mox.VerifyAll()


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

        request_mock = self.mox.CreateMock(http.HttpRequest)
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

        request_mock = self.mox.CreateMock(http.HttpRequest)
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

        request_mock = self.mox.CreateMock(http.HttpRequest)

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

        request_mock = self.mox.CreateMock(http.HttpRequest)

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

