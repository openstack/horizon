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

import cloudfiles
import httplib
import json
import mox

from django import http
from django.conf import settings
from django_openstack import api
from glance import client as glance_client
from mox import IsA
from novaclient import service_catalog, client as base_client
from novaclient.keystone import client as keystone_client
from novaclient.v1_1 import client as nova_client
from openstack import compute as OSCompute
from openstackx import admin as OSAdmin
from openstackx import auth as OSAuth
from openstackx import extras as OSExtras


from django_openstack import test
from django_openstack.middleware import keystone


TEST_CONSOLE_KIND = 'vnc'
TEST_EMAIL = 'test@test.com'
TEST_HOSTNAME = 'hostname'
TEST_INSTANCE_ID = '2'
TEST_PASSWORD = '12345'
TEST_PORT = 8000
TEST_RETURN = 'retValue'
TEST_TENANT_DESCRIPTION = 'tenantDescription'
TEST_TENANT_ID = '1234'
TEST_TENANT_NAME = 'foo'
TEST_TOKEN = 'aToken'
TEST_TOKEN_ID = 'userId'
TEST_URL = 'http://%s:%s/something/v1.0' % (TEST_HOSTNAME, TEST_PORT)
TEST_USERNAME = 'testUser'


class Server(object):
    """ More or less fakes what the api is looking for """
    def __init__(self, id, image, attrs=None):
        self.id = id

        self.image = image
        if attrs is not None:
            self.attrs = attrs

    def __eq__(self, other):
        if self.id != other.id or \
            self.image['id'] != other.image['id']:
                return False

        for k in self.attrs:
            if other.attrs.__getattr__(k) != v:
                return False

        return True

    def __ne__(self, other):
        return not self == other


class Tenant(object):
    """ More or less fakes what the api is looking for """
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
    """ More or less fakes what the api is looking for """
    def __init__(self, id, username, tenant_id, tenant_name,
                 serviceCatalog=None):
        self.id = id
        self.user = {'name': username}
        self.tenant = {'id': tenant_id, 'name': tenant_name}
        self.serviceCatalog = serviceCatalog

    def __eq__(self, other):
        return self.id == other.id and \
               self.user['name'] == other.user['name'] and \
               self.tenant_id == other.tenant_id and \
               self.serviceCatalog == other.serviceCatalog

    def __ne__(self, other):
        return not self == other


class APIResource(api.APIResourceWrapper):
    """ Simple APIResource for testing """
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
    """ Simple APIDict for testing """
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerDict=None):
        if innerDict is None:
            innerDict = {'foo': 'foo',
                         'bar': 'bar'}
        return APIDict(innerDict)


class APITestCase(test.TestCase):
    def setUp(self):
        def fake_keystoneclient(request, username=None, password=None,
                                tenant_id=None, token_id=None, endpoint=None):
            return self.stub_keystoneclient()
        super(APITestCase, self).setUp()
        self._original_keystoneclient = api.keystoneclient
        self._original_novaclient = api.novaclient
        api.keystoneclient = fake_keystoneclient
        api.novaclient = lambda request: self.stub_novaclient()

    def stub_novaclient(self):
        if not hasattr(self, "novaclient"):
            self.mox.StubOutWithMock(nova_client, 'Client')
            self.novaclient = self.mox.CreateMock(nova_client.Client)
        return self.novaclient

    def stub_keystoneclient(self):
        if not hasattr(self, "keystoneclient"):
            self.mox.StubOutWithMock(keystone_client, 'Client')
            self.keystoneclient = self.mox.CreateMock(keystone_client.Client)
        return self.keystoneclient

    def tearDown(self):
        super(APITestCase, self).tearDown()
        api.novaclient = self._original_novaclient
        api.keystoneclient = self._original_keystoneclient


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
    IMAGE_OBJ = {'id': '3', 'links': [{'href': '3', u'rel': u'bookmark'}]}

    def setUp(self):
        super(ServerWrapperTests, self).setUp()

        # these are all objects "fetched" from the api
        self.inner_attrs = {'host': self.HOST}

        self.inner_server = Server(self.ID, self.IMAGE_OBJ, self.inner_attrs)
        self.inner_server_no_attrs = Server(self.ID, self.IMAGE_OBJ)

        #self.request = self.mox.CreateMock(http.HttpRequest)

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
                      self.IMAGE_OBJ['id']
                      ).AndReturn(api.Image({'name': self.IMAGE_NAME}))

        server = api.Server(self.inner_server, self.request)

        self.mox.ReplayAll()

        image_name = server.image_name

        self.assertEqual(image_name, self.IMAGE_NAME)

        self.mox.VerifyAll()


class ApiHelperTests(test.TestCase):
    """ Tests for functions that don't use one of the api objects """

    def test_url_for(self):
        GLANCE_URL = 'http://glance/glanceapi/'
        NOVA_URL = 'http://nova/novapi/'

        url = api.url_for(self.request, 'image')
        self.assertEqual(url, GLANCE_URL + 'internal')

        url = api.url_for(self.request, 'image', admin=False)
        self.assertEqual(url, GLANCE_URL + 'internal')

        url = api.url_for(self.request, 'image', admin=True)
        self.assertEqual(url, GLANCE_URL + 'admin')

        url = api.url_for(self.request, 'compute')
        self.assertEqual(url, NOVA_URL + 'internal')

        url = api.url_for(self.request, 'compute', admin=False)
        self.assertEqual(url, NOVA_URL + 'internal')

        url = api.url_for(self.request, 'compute', admin=True)
        self.assertEqual(url, NOVA_URL + 'admin')

        self.assertNotIn('notAnApi', self.request.user.service_catalog,
                         'Select a new nonexistent service catalog key')
        with self.assertRaises(api.ServiceCatalogException):
            url = api.url_for(self.request, 'notAnApi')


class TenantAPITests(APITestCase):
    def test_tenant_create(self):
        DESCRIPTION = 'aDescription'
        ENABLED = True

        keystoneclient = self.stub_keystoneclient()

        keystoneclient.tenants = self.mox.CreateMockAnything()
        keystoneclient.tenants.create(TEST_TENANT_ID, DESCRIPTION,
                                   ENABLED).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.tenant_create(self.request, TEST_TENANT_ID,
                                    DESCRIPTION, ENABLED)

        self.assertIsInstance(ret_val, api.Tenant)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_tenant_get(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.tenants = self.mox.CreateMockAnything()
        keystoneclient.tenants.get(TEST_TENANT_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.tenant_get(self.request, TEST_TENANT_ID)

        self.assertIsInstance(ret_val, api.Tenant)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_tenant_list(self):
        tenants = (TEST_RETURN, TEST_RETURN + '2')

        keystoneclient = self.stub_keystoneclient()

        keystoneclient.tenants = self.mox.CreateMockAnything()
        keystoneclient.tenants.list().AndReturn(tenants)

        self.mox.ReplayAll()

        ret_val = api.tenant_list(self.request)

        self.assertEqual(len(ret_val), len(tenants))
        for tenant in ret_val:
            self.assertIsInstance(tenant, api.Tenant)
            self.assertIn(tenant._apiresource, tenants)

        self.mox.VerifyAll()

    def test_tenant_update(self):
        DESCRIPTION = 'aDescription'
        ENABLED = True

        keystoneclient = self.stub_keystoneclient()

        keystoneclient.tenants = self.mox.CreateMockAnything()
        keystoneclient.tenants.update(TEST_TENANT_ID, TEST_TENANT_NAME,
                                   DESCRIPTION, ENABLED).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.tenant_update(self.request, TEST_TENANT_ID,
                                    TEST_TENANT_NAME, DESCRIPTION, ENABLED)

        self.assertIsInstance(ret_val, api.Tenant)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()


class UserAPITests(APITestCase):
    def test_user_create(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.create(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL,
                                TEST_TENANT_ID, True).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_create(self.request, TEST_USERNAME, TEST_EMAIL,
                                  TEST_PASSWORD, TEST_TENANT_ID, True)

        self.assertIsInstance(ret_val, api.User)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_user_delete(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.delete(TEST_USERNAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_delete(self.request, TEST_USERNAME)

        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_user_get(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.get(TEST_USERNAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_get(self.request, TEST_USERNAME)

        self.assertIsInstance(ret_val, api.User)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_user_list(self):
        users = (TEST_USERNAME, TEST_USERNAME + '2')

        keystoneclient = self.stub_keystoneclient()
        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.list(tenant_id=None).AndReturn(users)

        self.mox.ReplayAll()

        ret_val = api.user_list(self.request)

        self.assertEqual(len(ret_val), len(users))
        for user in ret_val:
            self.assertIsInstance(user, api.User)
            self.assertIn(user._apiresource, users)

        self.mox.VerifyAll()

    def test_user_update_email(self):
        keystoneclient = self.stub_keystoneclient()
        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.update_email(TEST_USERNAME,
                                       TEST_EMAIL).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_update_email(self.request, TEST_USERNAME,
                                        TEST_EMAIL)

        self.assertIsInstance(ret_val, api.User)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_user_update_password(self):
        keystoneclient = self.stub_keystoneclient()
        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.update_password(TEST_USERNAME,
                                          TEST_PASSWORD).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_update_password(self.request, TEST_USERNAME,
                                           TEST_PASSWORD)

        self.assertIsInstance(ret_val, api.User)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_user_update_tenant(self):
        keystoneclient = self.stub_keystoneclient()
        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.update_tenant(TEST_USERNAME,
                                        TEST_TENANT_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_update_tenant(self.request, TEST_USERNAME,
                                           TEST_TENANT_ID)

        self.assertIsInstance(ret_val, api.User)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()


class RoleAPITests(APITestCase):
    def test_role_add_for_tenant_user(self):
        keystoneclient = self.stub_keystoneclient()

        role = api.Role(APIResource.get_instance())
        role.id = TEST_RETURN
        role.name = TEST_RETURN

        keystoneclient.roles = self.mox.CreateMockAnything()
        keystoneclient.roles.add_user_to_tenant(TEST_TENANT_ID,
                                                  TEST_USERNAME,
                                                  TEST_RETURN).AndReturn(role)
        api._get_role = self.mox.CreateMockAnything()
        api._get_role(IsA(http.HttpRequest), IsA(str)).AndReturn(role)

        self.mox.ReplayAll()
        ret_val = api.role_add_for_tenant_user(self.request,
                                               TEST_TENANT_ID,
                                               TEST_USERNAME,
                                               TEST_RETURN)
        self.assertEqual(ret_val, role)

        self.mox.VerifyAll()


class AdminApiTests(APITestCase):
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
        api.url_for(IsA(http.HttpRequest), 'compute', True).AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'compute', True).AndReturn(TEST_URL)

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

    def test_service_get(self):
        NAME = 'serviceName'

        admin_api = self.stub_admin_api()
        admin_api.services = self.mox.CreateMockAnything()
        admin_api.services.get(NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.service_get(self.request, NAME)

        self.assertIsInstance(ret_val, api.Services)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_service_list(self):
        services = (TEST_RETURN, TEST_RETURN + '2')

        admin_api = self.stub_admin_api()
        admin_api.services = self.mox.CreateMockAnything()
        admin_api.services.list().AndReturn(services)

        self.mox.ReplayAll()

        ret_val = api.service_list(self.request)

        for service in ret_val:
            self.assertIsInstance(service, api.Services)
            self.assertIn(service._apiresource, services)

        self.mox.VerifyAll()

    def test_service_update(self):
        ENABLED = True
        NAME = 'serviceName'

        admin_api = self.stub_admin_api()
        admin_api.services = self.mox.CreateMockAnything()
        admin_api.services.update(NAME, ENABLED).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.service_update(self.request, NAME, ENABLED)

        self.assertIsInstance(ret_val, api.Services)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()


class TokenApiTests(APITestCase):
    def setUp(self):
        super(TokenApiTests, self).setUp()
        self._prev_OPENSTACK_KEYSTONE_URL = getattr(settings,
                                                    'OPENSTACK_KEYSTONE_URL',
                                                    None)
        settings.OPENSTACK_KEYSTONE_URL = TEST_URL

    def tearDown(self):
        super(TokenApiTests, self).tearDown()
        settings.OPENSTACK_KEYSTONE_URL = self._prev_OPENSTACK_KEYSTONE_URL

    def test_token_create(self):
        catalog = {
                'access': {
                    'token': {
                        'id': TEST_TOKEN_ID,
                    },
                    'user': {
                        'roles': [],
                    }
                }
            }
        test_token = Token(TEST_TOKEN_ID, TEST_USERNAME,
                           TEST_TENANT_ID, TEST_TENANT_NAME)

        keystoneclient = self.stub_keystoneclient()

        keystoneclient.tokens = self.mox.CreateMockAnything()
        keystoneclient.tokens.authenticate(username=TEST_USERNAME,
                                           password=TEST_PASSWORD,
                                           tenant=TEST_TENANT_ID
                                          ).AndReturn(test_token)

        self.mox.ReplayAll()

        ret_val = api.token_create(self.request, TEST_TENANT_ID,
                                   TEST_USERNAME, TEST_PASSWORD)

        self.assertEqual(test_token.tenant['id'], ret_val.tenant['id'])

        self.mox.VerifyAll()


class ComputeApiTests(APITestCase):
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
        api.url_for(IsA(http.HttpRequest), 'compute').AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'compute').AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'compute').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        compute_api = api.compute_api(self.request)

        self.assertIsNotNone(compute_api)
        self.assertEqual(compute_api.client.auth_token, TEST_TOKEN)
        self.assertEqual(compute_api.client.management_url, TEST_URL)

        self.mox.VerifyAll()

    def test_flavor_get(self):
        FLAVOR_ID = 6

        novaclient = self.stub_novaclient()

        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.get(FLAVOR_ID).AndReturn(TEST_RETURN)

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

    def test_server_reboot(self):
        INSTANCE_ID = '2'
        HARDNESS = 'diamond'

        self.mox.StubOutWithMock(api, 'server_get')

        server = self.mox.CreateMock(OSCompute.Server)
        server.reboot(OSCompute.servers.REBOOT_HARD).AndReturn(TEST_RETURN)
        api.server_get(IsA(http.HttpRequest), INSTANCE_ID).AndReturn(server)

        server = self.mox.CreateMock(OSCompute.Server)
        server.reboot(HARDNESS).AndReturn(TEST_RETURN)
        api.server_get(IsA(http.HttpRequest), INSTANCE_ID).AndReturn(server)

        self.mox.ReplayAll()

        ret_val = api.server_reboot(self.request, INSTANCE_ID)
        self.assertIsNone(ret_val)

        ret_val = api.server_reboot(self.request, INSTANCE_ID,
                                    hardness=HARDNESS)
        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_server_create(self):
        NAME = 'server'
        IMAGE = 'anImage'
        FLAVOR = 'cherry'
        USER_DATA = {'nuts': 'berries'}
        KEY = 'user'
        SECGROUP = self.mox.CreateMock(api.SecurityGroup)

        server = self.mox.CreateMock(OSCompute.Server)
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.create(NAME, IMAGE, FLAVOR, userdata=USER_DATA,
                                  security_groups=[SECGROUP], key_name=KEY)\
                                  .AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.server_create(self.request, NAME, IMAGE, FLAVOR,
                                    KEY, USER_DATA, [SECGROUP])

        self.assertIsInstance(ret_val, api.Server)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()


class ExtrasApiTests(APITestCase):

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
        api.url_for(IsA(http.HttpRequest), 'compute').AndReturn(TEST_URL)
        api.url_for(IsA(http.HttpRequest), 'compute').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        self.assertIsNotNone(api.extras_api(self.request))

        self.mox.VerifyAll()

    def test_console_create(self):
        extras_api = self.stub_extras_api(count=2)
        extras_api.consoles = self.mox.CreateMockAnything()
        extras_api.consoles.create(
                TEST_INSTANCE_ID, TEST_CONSOLE_KIND).AndReturn(TEST_RETURN)
        extras_api.consoles.create(
                TEST_INSTANCE_ID, 'text').AndReturn(TEST_RETURN + '2')

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
        novaclient = self.stub_novaclient()
        novaclient.flavors = self.mox.CreateMockAnything()
        novaclient.flavors.list().AndReturn(flavors)

        self.mox.ReplayAll()

        ret_val = api.flavor_list(self.request)

        self.assertEqual(len(ret_val), len(flavors))
        for flavor in ret_val:
            self.assertIsInstance(flavor, api.Flavor)
            self.assertIn(flavor._apiresource, flavors)

        self.mox.VerifyAll()

    def test_server_list(self):
        servers = (TEST_RETURN, TEST_RETURN + '2')

        extras_api = self.stub_extras_api()

        extras_api.servers = self.mox.CreateMockAnything()
        extras_api.servers.list().AndReturn(servers)

        self.mox.ReplayAll()

        ret_val = api.server_list(self.request)

        self.assertEqual(len(ret_val), len(servers))
        for server in ret_val:
            self.assertIsInstance(server, api.Server)
            self.assertIn(server._apiresource, servers)

        self.mox.VerifyAll()

    def test_usage_get(self):
        extras_api = self.stub_extras_api()

        extras_api.usage = self.mox.CreateMockAnything()
        extras_api.usage.get(TEST_TENANT_ID, 'start',
                             'end').AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.usage_get(self.request, TEST_TENANT_ID, 'start', 'end')

        self.assertIsInstance(ret_val, api.Usage)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_usage_list(self):
        usages = (TEST_RETURN, TEST_RETURN + '2')

        extras_api = self.stub_extras_api()

        extras_api.usage = self.mox.CreateMockAnything()
        extras_api.usage.list('start', 'end').AndReturn(usages)

        self.mox.ReplayAll()

        ret_val = api.usage_list(self.request, 'start', 'end')

        self.assertEqual(len(ret_val), len(usages))
        for usage in ret_val:
            self.assertIsInstance(usage, api.Usage)
            self.assertIn(usage._apiresource, usages)

        self.mox.VerifyAll()

    def test_server_get(self):
        INSTANCE_ID = '2'

        extras_api = self.stub_extras_api()
        extras_api.servers = self.mox.CreateMockAnything()
        extras_api.servers.get(INSTANCE_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.server_get(self.request, INSTANCE_ID)

        self.assertIsInstance(ret_val, api.Server)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()


class VolumeTests(APITestCase):
    def setUp(self):
        super(VolumeTests, self).setUp()
        volume = api.Volume(APIResource.get_instance())
        volume.id = 1
        volume.displayName = "displayName"
        volume.attachments = [{"device": "/dev/vdb",
                               "serverId": 1,
                               "id": 1,
                               "volumeId": 1}]
        self.volume = volume
        self.volumes = [volume, ]

        self.novaclient = self.stub_novaclient()
        self.novaclient.volumes = self.mox.CreateMockAnything()

    def test_volume_list(self):
        self.novaclient.volumes.list().AndReturn(self.volumes)
        self.mox.ReplayAll()

        volumes = api.volume_list(self.request)

        self.assertIsInstance(volumes[0], api.Volume)
        self.mox.VerifyAll()

    def test_volume_get(self):
        self.novaclient.volumes.get(IsA(int)).AndReturn(self.volume)
        self.mox.ReplayAll()

        volume = api.volume_get(self.request, 1)

        self.assertIsInstance(volume, api.Volume)
        self.mox.VerifyAll()

    def test_volume_instance_list(self):
        self.novaclient.volumes.get_server_volumes(IsA(int)).AndReturn(
                self.volume.attachments)
        self.mox.ReplayAll()

        attachments = api.volume_instance_list(self.request, 1)

        self.assertEqual(attachments, self.volume.attachments)
        self.mox.VerifyAll()

    def test_volume_create(self):
        self.novaclient.volumes.create(IsA(int), IsA(str), IsA(str)).AndReturn(
                self.volume)
        self.mox.ReplayAll()

        new_volume = api.volume_create(self.request,
                                       10,
                                       "new volume",
                                       "new description")

        self.assertIsInstance(new_volume, api.Volume)
        self.mox.VerifyAll()

    def test_volume_delete(self):
        self.novaclient.volumes.delete(IsA(int))
        self.mox.ReplayAll()

        ret_val = api.volume_delete(self.request, 1)

        self.assertIsNone(ret_val)
        self.mox.VerifyAll()

    def test_volume_attach(self):
        self.novaclient.volumes.create_server_volume(
                IsA(int), IsA(int), IsA(str))
        self.mox.ReplayAll()

        ret_val = api.volume_attach(self.request, 1, 1, "/dev/vdb")

        self.assertIsNone(ret_val)
        self.mox.VerifyAll()

    def test_volume_detach(self):
        self.novaclient.volumes.delete_server_volume(IsA(int), IsA(int))
        self.mox.ReplayAll()

        ret_val = api.volume_detach(self.request, 1, 1)

        self.assertIsNone(ret_val)
        self.mox.VerifyAll()


class APIExtensionTests(APITestCase):

    def setUp(self):
        super(APIExtensionTests, self).setUp()
        keypair = api.KeyPair(APIResource.get_instance())
        keypair.id = 1
        keypair.name = TEST_RETURN

        self.keypair = keypair
        self.keypairs = [keypair, ]

        floating_ip = api.FloatingIp(APIResource.get_instance())
        floating_ip.id = 1
        floating_ip.fixed_ip = '10.0.0.4'
        floating_ip.instance_id = 1
        floating_ip.ip = '58.58.58.58'

        self.floating_ip = floating_ip
        self.floating_ips = [floating_ip, ]

        server = api.Server(APIResource.get_instance(), self.request)
        server.id = 1

        self.server = server
        self.servers = [server, ]

    def test_server_snapshot_create(self):
        novaclient = self.stub_novaclient()

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.create_image(IsA(int), IsA(str)).\
                                                        AndReturn(self.server)
        self.mox.ReplayAll()

        server = api.snapshot_create(self.request, 1, 'test-snapshot')

        self.assertIsInstance(server, api.Server)
        self.mox.VerifyAll()

    def test_tenant_floating_ip_list(self):
        novaclient = self.stub_novaclient()

        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.list().AndReturn(self.floating_ips)
        self.mox.ReplayAll()

        floating_ips = api.tenant_floating_ip_list(self.request)

        self.assertEqual(len(floating_ips), len(self.floating_ips))
        self.assertIsInstance(floating_ips[0], api.FloatingIp)
        self.mox.VerifyAll()

    def test_tenant_floating_ip_get(self):
        novaclient = self.stub_novaclient()

        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.get(IsA(int)).AndReturn(self.floating_ip)
        self.mox.ReplayAll()

        floating_ip = api.tenant_floating_ip_get(self.request, 1)

        self.assertIsInstance(floating_ip, api.FloatingIp)
        self.mox.VerifyAll()

    def test_tenant_floating_ip_allocate(self):
        novaclient = self.stub_novaclient()

        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.create().AndReturn(self.floating_ip)
        self.mox.ReplayAll()

        floating_ip = api.tenant_floating_ip_allocate(self.request)

        self.assertIsInstance(floating_ip, api.FloatingIp)
        self.mox.VerifyAll()

    def test_tenant_floating_ip_release(self):
        novaclient = self.stub_novaclient()

        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.delete(1).AndReturn(self.floating_ip)
        self.mox.ReplayAll()

        floating_ip = api.tenant_floating_ip_release(self.request, 1)

        self.assertIsInstance(floating_ip, api.FloatingIp)
        self.mox.VerifyAll()

    def test_server_remove_floating_ip(self):
        novaclient = self.stub_novaclient()

        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.floating_ips = self.mox.CreateMockAnything()

        novaclient.servers.get(IsA(int)).AndReturn(self.server)
        novaclient.floating_ips.get(IsA(int)).AndReturn(self.floating_ip)
        novaclient.servers.remove_floating_ip(IsA(self.server.__class__),
                                           IsA(self.floating_ip.__class__)) \
                                           .AndReturn(self.server)
        self.mox.ReplayAll()

        server = api.server_remove_floating_ip(self.request, 1, 1)

        self.assertIsInstance(server, api.Server)
        self.mox.VerifyAll()

    def test_server_add_floating_ip(self):
        novaclient = self.stub_novaclient()

        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.servers = self.mox.CreateMockAnything()

        novaclient.servers.get(IsA(int)).AndReturn(self.server)
        novaclient.floating_ips.get(IsA(int)).AndReturn(self.floating_ip)
        novaclient.servers.add_floating_ip(IsA(self.server.__class__),
                                           IsA(self.floating_ip.__class__)) \
                                           .AndReturn(self.server)
        self.mox.ReplayAll()

        server = api.server_add_floating_ip(self.request, 1, 1)

        self.assertIsInstance(server, api.Server)
        self.mox.VerifyAll()

    def test_keypair_create(self):
        novaclient = self.stub_novaclient()

        novaclient.keypairs = self.mox.CreateMockAnything()
        novaclient.keypairs.create(IsA(str)).AndReturn(self.keypair)
        self.mox.ReplayAll()

        ret_val = api.keypair_create(self.request, TEST_RETURN)
        self.assertIsInstance(ret_val, api.KeyPair)
        self.assertEqual(ret_val.name, self.keypair.name)

        self.mox.VerifyAll()

    def test_keypair_import(self):
        novaclient = self.stub_novaclient()

        novaclient.keypairs = self.mox.CreateMockAnything()
        novaclient.keypairs.create(IsA(str), IsA(str)).AndReturn(self.keypair)
        self.mox.ReplayAll()

        ret_val = api.keypair_import(self.request, TEST_RETURN, TEST_RETURN)
        self.assertIsInstance(ret_val, api.KeyPair)
        self.assertEqual(ret_val.name, self.keypair.name)

        self.mox.VerifyAll()

    def test_keypair_delete(self):
        novaclient = self.stub_novaclient()

        novaclient.keypairs = self.mox.CreateMockAnything()
        novaclient.keypairs.delete(IsA(int))

        self.mox.ReplayAll()

        ret_val = api.keypair_delete(self.request, self.keypair.id)
        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_keypair_list(self):
        novaclient = self.stub_novaclient()

        novaclient.keypairs = self.mox.CreateMockAnything()
        novaclient.keypairs.list().AndReturn(self.keypairs)

        self.mox.ReplayAll()

        ret_val = api.keypair_list(self.request)

        self.assertEqual(len(ret_val), len(self.keypairs))
        for keypair in ret_val:
            self.assertIsInstance(keypair, api.KeyPair)

        self.mox.VerifyAll()


class GlanceApiTests(APITestCase):
    def stub_glance_api(self, count=1):
        self.mox.StubOutWithMock(api, 'glance_api')
        glance_api = self.mox.CreateMock(glance_client.Client)
        glance_api.token = TEST_TOKEN
        for i in range(count):
            api.glance_api(IsA(http.HttpRequest)).AndReturn(glance_api)
        return glance_api

    def test_get_glance_api(self):
        self.mox.StubOutClassWithMocks(glance_client, 'Client')
        client_instance = glance_client.Client(TEST_HOSTNAME, TEST_PORT,
                                                        auth_tok=TEST_TOKEN)
        # Normally ``auth_tok`` is set in ``Client.__init__``, but mox doesn't
        # duplicate that behavior so we set it manually.
        client_instance.auth_tok = TEST_TOKEN

        self.mox.StubOutWithMock(api, 'url_for')
        api.url_for(IsA(http.HttpRequest), 'image').AndReturn(TEST_URL)

        self.mox.ReplayAll()

        ret_val = api.glance_api(self.request)
        self.assertIsNotNone(ret_val)
        self.assertEqual(ret_val.auth_tok, TEST_TOKEN)

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


class SwiftApiTests(APITestCase):
    def setUp(self):
        self.mox = mox.Mox()

        self.request = http.HttpRequest()
        self.request.session = dict()
        self.request.session['token'] = TEST_TOKEN

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_swift_api(self, count=1):
        self.mox.StubOutWithMock(api, 'swift_api')
        swift_api = self.mox.CreateMock(cloudfiles.connection.Connection)
        for i in range(count):
            api.swift_api(IsA(http.HttpRequest)).AndReturn(swift_api)
        return swift_api

    def test_swift_get_containers(self):
        containers = (TEST_RETURN, TEST_RETURN + '2')

        swift_api = self.stub_swift_api()

        swift_api.get_all_containers(limit=10000,
                                     marker=None).AndReturn(containers)

        self.mox.ReplayAll()

        ret_val = api.swift_get_containers(self.request)

        self.assertEqual(len(ret_val), len(containers))
        for container in ret_val:
            self.assertIsInstance(container, api.Container)
            self.assertIn(container._apiresource, containers)

        self.mox.VerifyAll()

    def test_swift_create_container(self):
        NAME = 'containerName'

        swift_api = self.stub_swift_api()
        self.mox.StubOutWithMock(api, 'swift_container_exists')

        api.swift_container_exists(self.request,
                                   NAME).AndReturn(False)
        swift_api.create_container(NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_create_container(self.request, NAME)

        self.assertIsInstance(ret_val, api.Container)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

        self.mox.VerifyAll()

    def test_swift_delete_container(self):
        NAME = 'containerName'

        swift_api = self.stub_swift_api()

        swift_api.delete_container(NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_delete_container(self.request, NAME)

        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_swift_get_objects(self):
        NAME = 'containerName'

        swift_objects = (TEST_RETURN, TEST_RETURN + '2')
        container = self.mox.CreateMock(cloudfiles.container.Container)
        container.get_objects(limit=10000,
                              marker=None,
                              prefix=None).AndReturn(swift_objects)

        swift_api = self.stub_swift_api()

        swift_api.get_container(NAME).AndReturn(container)

        self.mox.ReplayAll()

        ret_val = api.swift_get_objects(self.request, NAME)

        self.assertEqual(len(ret_val), len(swift_objects))
        for swift_object in ret_val:
            self.assertIsInstance(swift_object, api.SwiftObject)
            self.assertIn(swift_object._apiresource, swift_objects)

        self.mox.VerifyAll()

    def test_swift_get_objects_with_prefix(self):
        NAME = 'containerName'
        PREFIX = 'prefacedWith'

        swift_objects = (TEST_RETURN, TEST_RETURN + '2')
        container = self.mox.CreateMock(cloudfiles.container.Container)
        container.get_objects(limit=10000,
                              marker=None,
                              prefix=PREFIX).AndReturn(swift_objects)

        swift_api = self.stub_swift_api()

        swift_api.get_container(NAME).AndReturn(container)

        self.mox.ReplayAll()

        ret_val = api.swift_get_objects(self.request,
                                        NAME,
                                        prefix=PREFIX)

        self.assertEqual(len(ret_val), len(swift_objects))
        for swift_object in ret_val:
            self.assertIsInstance(swift_object, api.SwiftObject)
            self.assertIn(swift_object._apiresource, swift_objects)

        self.mox.VerifyAll()

    def test_swift_upload_object(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'
        OBJECT_DATA = 'someData'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        swift_object = self.mox.CreateMock(cloudfiles.storage_object.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.create_object(OBJECT_NAME).AndReturn(swift_object)
        swift_object.write(OBJECT_DATA).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_upload_object(self.request,
                                          CONTAINER_NAME,
                                          OBJECT_NAME,
                                          OBJECT_DATA)

        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_swift_delete_object(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.delete_object(OBJECT_NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.swift_delete_object(self.request,
                                          CONTAINER_NAME,
                                          OBJECT_NAME)

        self.assertIsNone(ret_val)

        self.mox.VerifyAll()

    def test_swift_get_object_data(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'
        OBJECT_DATA = 'objectData'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        swift_object = self.mox.CreateMock(cloudfiles.storage_object.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.get_object(OBJECT_NAME).AndReturn(swift_object)
        swift_object.stream().AndReturn(OBJECT_DATA)

        self.mox.ReplayAll()

        ret_val = api.swift_get_object_data(self.request,
                                            CONTAINER_NAME,
                                            OBJECT_NAME)

        self.assertEqual(ret_val, OBJECT_DATA)

        self.mox.VerifyAll()

    def test_swift_object_exists(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        swift_object = self.mox.CreateMock(cloudfiles.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        container.get_object(OBJECT_NAME).AndReturn(swift_object)

        self.mox.ReplayAll()

        ret_val = api.swift_object_exists(self.request,
                                          CONTAINER_NAME,
                                          OBJECT_NAME)
        self.assertTrue(ret_val)

        self.mox.VerifyAll()

    def test_swift_copy_object(self):
        CONTAINER_NAME = 'containerName'
        OBJECT_NAME = 'objectName'

        swift_api = self.stub_swift_api()
        container = self.mox.CreateMock(cloudfiles.container.Container)
        self.mox.StubOutWithMock(api, 'swift_object_exists')

        swift_object = self.mox.CreateMock(cloudfiles.Object)

        swift_api.get_container(CONTAINER_NAME).AndReturn(container)
        api.swift_object_exists(self.request,
                                CONTAINER_NAME,
                                OBJECT_NAME).AndReturn(False)

        container.get_object(OBJECT_NAME).AndReturn(swift_object)
        swift_object.copy_to(CONTAINER_NAME, OBJECT_NAME)

        self.mox.ReplayAll()

        ret_val = api.swift_copy_object(self.request, CONTAINER_NAME,
                                        OBJECT_NAME, CONTAINER_NAME,
                                        OBJECT_NAME)

        self.assertIsNone(ret_val)
        self.mox.VerifyAll()
