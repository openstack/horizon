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

from __future__ import absolute_import

from django import http
from django.conf import settings
from mox import IsA
from openstackx import admin as OSAdmin

from horizon.tests.api_tests.utils import *


class Token(object):
    """ More or less fakes what the api is looking for """
    def __init__(self, id, username, tenant_id,
                 tenant_name, serviceCatalog=None):
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


class KeystoneAdminApiTests(APITestCase):
    def stub_admin_api(self, count=1):
        self.mox.StubOutWithMock(api.keystone, 'admin_api')
        admin_api = self.mox.CreateMock(OSAdmin.Admin)
        for i in range(count):
            api.keystone.admin_api(IsA(http.HttpRequest)) \
                    .AndReturn(admin_api)
        return admin_api


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
                                           tenant_id=TEST_TENANT_ID)\
                                           .AndReturn(test_token)

        self.mox.ReplayAll()

        ret_val = api.token_create(self.request, TEST_TENANT_ID,
                                   TEST_USERNAME, TEST_PASSWORD)

        self.assertEqual(test_token.tenant['id'], ret_val.tenant['id'])


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
        api.keystone._get_role = self.mox.CreateMockAnything()
        api.keystone._get_role(IsA(http.HttpRequest), IsA(str)).AndReturn(role)

        self.mox.ReplayAll()
        ret_val = api.role_add_for_tenant_user(self.request,
                                               TEST_TENANT_ID,
                                               TEST_USERNAME,
                                               TEST_RETURN)
        self.assertEqual(ret_val, role)


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

    def test_tenant_get(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.tenants = self.mox.CreateMockAnything()
        keystoneclient.tenants.get(TEST_TENANT_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.tenant_get(self.request, TEST_TENANT_ID)

        self.assertIsInstance(ret_val, api.Tenant)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

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

    def test_user_delete(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.delete(TEST_USERNAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_delete(self.request, TEST_USERNAME)

        self.assertIsNone(ret_val)

    def test_user_get(self):
        keystoneclient = self.stub_keystoneclient()

        keystoneclient.users = self.mox.CreateMockAnything()
        keystoneclient.users.get(TEST_USERNAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        ret_val = api.user_get(self.request, TEST_USERNAME)

        self.assertIsInstance(ret_val, api.User)
        self.assertEqual(ret_val._apiresource, TEST_RETURN)

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
