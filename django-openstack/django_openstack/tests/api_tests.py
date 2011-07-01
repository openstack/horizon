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

import cloudfiles
import mox

from django import http
from django import test
from django.conf import settings
from django.utils import unittest
from django_openstack import api
from glance import client as glance_client
from mox import IsA
from openstack import compute as OSCompute
from openstackx import admin as OSAdmin
from openstackx import auth as OSAuth
from openstackx import extras as OSExtras


TEST_CONSOLE_KIND = 'vnc'
TEST_HOSTNAME = 'hostname'
TEST_INSTANCE_ID = '2'
TEST_PASSWORD = '12345'
TEST_PORT = 8000
TEST_RETURN = 'retValue'
TEST_TENANT_DESCRIPTION = 'tenantDescription'
TEST_TENANT_ID = '1234'
TEST_TOKEN = 'aToken'
TEST_TOKEN_ID = 'userId'
TEST_URL = 'http://%s:%s/something/v1.0' % (TEST_HOSTNAME, TEST_PORT)
TEST_USERNAME = 'testUser'


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
        self.inner_attrs = {'host': self.HOST}

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


class AccountApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.request = http.HttpRequest()
        self.request.session = dict()
        self.request.session['token'] = TEST_TOKEN

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_account_api(self):
        self.mox.StubOutWithMock(api, 'account_api')
        account_api = self.mox.CreateMock(OSExtras.Account)
        api.account_api(IsA(http.HttpRequest)).AndReturn(account_api)
        return account_api

    def test_get_account_api(self):
        self.mox.StubOutClassWithMocks(OSExtras, 'Account')
        OSExtras.Account(auth_token=TEST_TOKEN, management_url=TEST_URL)

        self.mox.StubOutWithMock(api, 'url_for')
        api.url_for(
                IsA(http.HttpRequest), 'keystone', True).AndReturn(TEST_URL)
        api.url_for(
                IsA(http.HttpRequest), 'keystone', True).AndReturn(TEST_URL)

        self.mox.ReplayAll()

        self.assertIsNotNone(api.account_api(self.request))

        self.mox.VerifyAll()


class AdminApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.request = http.HttpRequest()
        self.request.session = dict()
        self.request.session['token'] = TEST_TOKEN

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_admin_api(self, count=1):
        self.mox.StubOutWithMock(api, 'admin_api')
        admin_api = self.mox.CreateMock(OSAdmin.Admin)
        for i in range(count):
            api.admin_api(IsA(http.HttpRequest)).AndReturn(admin_api)
        return admin_api

    def test_get_admin_api(self):
        self.mox.StubOutClassWithMocks(OSAdmin, 'Admin')
        OSAdmin.Admin(auth_token=TEST_TOKEN, management_url=TEST_URL)

        self.mox.StubOutWithMock(api, 'url_for')
        api.url_for(IsA(http.HttpRequest), 'nova', True).AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'nova', True).AndReturn(TEST_URL)

        self.mox.ReplayAll()

        self.assertIsNotNone(api.admin_api(self.request))

        self.mox.VerifyAll()

    def test_flavor_create(self):
        FLAVOR_DISK = 1000
        FLAVOR_ID = 6
        FLAVOR_MEMORY = 1024
        FLAVOR_NAME = 'newFlavor'
        FLAVOR_VCPU = 2

        admin_api = self.stub_admin_api()

        admin_api.flavors = self.mox.CreateMockAnything()
        admin_api.flavors.create(FLAVOR_NAME, FLAVOR_MEMORY, FLAVOR_VCPU,
                                 FLAVOR_DISK, FLAVOR_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.flavor_create(self.request, FLAVOR_NAME,
                                    str(FLAVOR_MEMORY), str(FLAVOR_VCPU),
                                    str(FLAVOR_DISK), FLAVOR_ID)

        self.assertIsInstance(ret_val, api.Flavor)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_flavor_delete(self):
        FLAVOR_ID = 6

        admin_api = self.stub_admin_api(count=2)

        admin_api.flavors = self.mox.CreateMockAnything()
        admin_api.flavors.delete(FLAVOR_ID, False).AndReturn(TEST_RETURN)
        admin_api.flavors.delete(FLAVOR_ID, True).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.flavor_delete(self.request, FLAVOR_ID)
        self.assertIsNone(ret_val)

        ret_val = api.flavor_delete(self.request, FLAVOR_ID, purge=True)
        self.assertIsNone(ret_val)


class AuthApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_get_auth_api(self):
        settings.OPENSTACK_KEYSTONE_URL = TEST_URL
        self.mox.StubOutClassWithMocks(OSAuth, 'Auth')
        OSAuth.Auth(management_url=settings.OPENSTACK_KEYSTONE_URL)

        self.mox.ReplayAll()

        self.assertIsNotNone(api.auth_api())

        self.mox.VerifyAll()

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


class ComputeApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.request = http.HttpRequest()
        self.request.session = {}
        self.request.session['token'] = TEST_TOKEN

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_compute_api(self, count=1):
        self.mox.StubOutWithMock(api, 'compute_api')
        compute_api = self.mox.CreateMock(OSCompute.Compute)
        for i in range(count):
            api.compute_api(IsA(http.HttpRequest)).AndReturn(compute_api)
        return compute_api

    def test_get_compute_api(self):
        class ComputeClient(object):
            __slots__ = ['auth_token', 'management_url']

        self.mox.StubOutClassWithMocks(OSCompute, 'Compute')
        compute_api = OSCompute.Compute(auth_token=TEST_TOKEN,
                                        management_url=TEST_URL)

        compute_api.client = ComputeClient()

        self.mox.StubOutWithMock(api, 'url_for')
        # called three times?  Looks like a good place for optimization
        api.url_for(IsA(http.HttpRequest), 'nova').AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'nova').AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'nova').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        compute_api = api.compute_api(self.request)

        self.assertIsNotNone(compute_api)
        self.assertEqual(compute_api.client.auth_token, TEST_TOKEN)
        self.assertEqual(compute_api.client.management_url, TEST_URL)

        self.mox.VerifyAll()

    def test_flavor_get(self):
        FLAVOR_ID = 6

        compute_api = self.stub_compute_api()

        compute_api.flavors = self.mox.CreateMockAnything()
        compute_api.flavors.get(FLAVOR_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.flavor_get(self.request, FLAVOR_ID)
        self.assertIsInstance(ret_val, api.Flavor)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_server_delete(self):
        INSTANCE = 'anInstance'

        compute_api = self.stub_compute_api()

        compute_api.servers = self.mox.CreateMockAnything()
        compute_api.servers.delete(INSTANCE).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.server_delete(self.request, INSTANCE)

        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_server_get(self):
        INSTANCE_ID = '2'

        compute_api = self.stub_compute_api()
        compute_api.servers = self.mox.CreateMockAnything()
        compute_api.servers.get(INSTANCE_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.server_get(self.request, INSTANCE_ID)

        self.assertIsInstance(ret_val, api.Server)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()


class ExtrasApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.request = http.HttpRequest()
        self.request.session = dict()
        self.request.session['token'] = TEST_TOKEN

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_extras_api(self, count=1):
        self.mox.StubOutWithMock(api, 'extras_api')
        extras_api = self.mox.CreateMock(OSExtras.Extras)
        for i in range(count):
            api.extras_api(IsA(http.HttpRequest)).AndReturn(extras_api)
        return extras_api

    def test_get_extras_api(self):
        self.mox.StubOutClassWithMocks(OSExtras, 'Extras')
        OSExtras.Extras(auth_token=TEST_TOKEN, management_url=TEST_URL)

        self.mox.StubOutWithMock(api, 'url_for')
        api.url_for(IsA(http.HttpRequest), 'nova').AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'nova').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        self.assertIsNotNone(api.extras_api(self.request))

        self.mox.VerifyAll()

    def test_console_create(self):
        extras_api = self.stub_extras_api(count=2)
        extras_api.consoles = self.mox.CreateMockAnything()
        extras_api.consoles.create(
                TEST_INSTANCE_ID, TEST_CONSOLE_KIND).AndReturn(TEST_RETURN)
        extras_api.consoles.create(
                TEST_INSTANCE_ID, None).AndReturn(TEST_RETURN + '2')

        self.mox.ReplayAll()

        ret_val = api.console_create(self.request,
                                     TEST_INSTANCE_ID,
                                     TEST_CONSOLE_KIND)
        self.assertIsInstance(ret_val, api.Console)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        ret_val = api.console_create(self.request, TEST_INSTANCE_ID)
        self.assertIsInstance(ret_val, api.Console)
        self.assertEqual(ret_val._apiresource, TEST_RETURN + '2')

        self.mox.VerifyAll()

    def test_flavor_list(self):
        flavors = (TEST_RETURN, TEST_RETURN + '2')
        extras_api = self.stub_extras_api()
        extras_api.flavors = self.mox.CreateMockAnything()
        extras_api.flavors.list().AndReturn(flavors)

        self.mox.ReplayAll()

        ret_val = api.flavor_list(self.request)

        self.assertEqual(len(ret_val), len(flavors))
        for flavor in ret_val:
            self.assertIsInstance(flavor, api.Flavor)
            self.assertIn(flavor._apiresource, flavors)

        self.mox.VerifyAll()

    def test_keypair_create(self):
        NAME = '1'

        extras_api = self.stub_extras_api()
        extras_api.keypairs = self.mox.CreateMockAnything()
        extras_api.keypairs.create(NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.keypair_create(self.request, NAME)
        self.assertIsInstance(ret_val, api.KeyPair)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_keypair_delete(self):
        KEYPAIR_ID = '1'

        extras_api = self.stub_extras_api()
        extras_api.keypairs = self.mox.CreateMockAnything()
        extras_api.keypairs.delete(KEYPAIR_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.keypair_delete(self.request, KEYPAIR_ID)
        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_keypair_list(self):
        NAME = 'keypair'
        keypairs = (NAME + '1', NAME + '2')

        extras_api = self.stub_extras_api()
        extras_api.keypairs = self.mox.CreateMockAnything()
        extras_api.keypairs.list().AndReturn(keypairs)

        self.mox.ReplayAll()

        ret_val = api.keypair_list(self.request)

        self.assertEqual(len(ret_val), len(keypairs))
        for keypair in ret_val:
            self.assertIsInstance(keypair, api.KeyPair)
            self.assertIn(keypair._apiresource, keypairs)

        self.mox.VerifyAll()

    def test_server_create(self):
        NAME = 'server'
        IMAGE = 'anImage'
        FLAVOR = 'cherry'
        USER_DATA = {'nuts': 'berries'}
        KEY = 'user'

        extras_api = self.stub_extras_api()
        extras_api.servers = self.mox.CreateMockAnything()
        extras_api.servers.create(NAME, IMAGE, FLAVOR, user_data=USER_DATA,
                                  key_name=KEY).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.server_create(self.request, NAME, IMAGE, FLAVOR,
                                    USER_DATA, KEY)

        self.assertIsInstance(ret_val, api.Server)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

class GlanceApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

        self.request = http.HttpRequest()
        self.request.session = dict()
        self.request.session['token'] = TEST_TOKEN

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_glance_api(self, count=1):
        self.mox.StubOutWithMock(api, 'glance_api')
        glance_api = self.mox.CreateMock(glance_client.Client)
        for i in range(count):
            api.glance_api(IsA(http.HttpRequest)).AndReturn(glance_api)
        return glance_api

    def test_get_glance_api(self):
        self.mox.StubOutClassWithMocks(glance_client, 'Client')
        glance_client.Client(TEST_HOSTNAME, TEST_PORT)

        self.mox.StubOutWithMock(api, 'url_for')
        api.url_for(IsA(http.HttpRequest), 'glance').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        self.assertIsNotNone(api.glance_api(self.request))

        self.mox.VerifyAll()

    def test_image_create(self):
        IMAGE_FILE = 'someData'
        IMAGE_META = {'metadata': 'foo'}

        glance_api = self.stub_glance_api()
        glance_api.add_image(IMAGE_META, IMAGE_FILE).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.image_create(self.request, IMAGE_META, IMAGE_FILE)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)

        self.mox.VerifyAll()

    def test_image_delete(self):
        IMAGE_ID = '1'

        glance_api = self.stub_glance_api()
        glance_api.delete_image(IMAGE_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.image_delete(self.request, IMAGE_ID)

        self.assertEqual(ret_val, TEST_RETURN)

        self.mox.VerifyAll()

    def test_image_get(self):
        IMAGE_ID = '1'

        glance_api = self.stub_glance_api()
        glance_api.get_image(IMAGE_ID).AndReturn([TEST_RETURN])

        self.mox.ReplayAll()

        ret_val = api.image_get(self.request, IMAGE_ID)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)

    def test_image_list_detailed(self):
        images = (TEST_RETURN, TEST_RETURN + '2')
        glance_api = self.stub_glance_api()
        glance_api.get_images_detailed().AndReturn(images)

        self.mox.ReplayAll()

        ret_val = api.image_list_detailed(self.request)

        self.assertEqual(len(ret_val), len(images))
        for image in ret_val:
            self.assertIsInstance(image, api.Image)
            self.assertIn(image._apidict, images)

        self.mox.VerifyAll()

    def test_image_update(self):
        IMAGE_ID = '1'
        IMAGE_META = {'metadata': 'foobar'}

        glance_api = self.stub_glance_api(count=2)
        glance_api.update_image(IMAGE_ID, image_meta={}).AndReturn(TEST_RETURN)
        glance_api.update_image(IMAGE_ID,
                                image_meta=IMAGE_META).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.image_update(self.request, IMAGE_ID)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)

        ret_val = api.image_update(self.request,
                                   IMAGE_ID,
                                   image_meta=IMAGE_META)

        self.assertIsInstance(ret_val, api.Image)
        self.assertEqual(ret_val._apidict, TEST_RETURN)

        self.mox.VerifyAll()


class SwiftApiTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_get_swift_api(self):
        self.mox.StubOutWithMock(cloudfiles, 'get_connection')

        swiftuser = ':'.join((settings.SWIFT_ACCOUNT, settings.SWIFT_USER))
        cloudfiles.get_connection(swiftuser,
                                  settings.SWIFT_PASS,
                                  authurl=settings.SWIFT_AUTHURL
                                 ).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        self.assertEqual(api.swift_api(), TEST_RETURN)

        self.mox.VerifyAll()
