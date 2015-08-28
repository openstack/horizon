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

from __future__ import absolute_import

from keystoneclient.v2_0 import client as keystone_client
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class FakeConnection(object):
    pass


class ClientConnectionTests(test.TestCase):
    def setUp(self):
        super(ClientConnectionTests, self).setUp()
        self.mox.StubOutWithMock(keystone_client, "Client")
        self.internal_url = api.base.url_for(self.request,
                                             'identity',
                                             endpoint_type='internalURL')
        self.admin_url = api.base.url_for(self.request,
                                          'identity',
                                          endpoint_type='adminURL')
        self.conn = FakeConnection()


class RoleAPITests(test.APITestCase):
    def setUp(self):
        super(RoleAPITests, self).setUp()
        self.role = self.roles.member
        self.roles = self.roles.list()

    def test_remove_tenant_user(self):
        """Tests api.keystone.remove_tenant_user

        Verifies that remove_tenant_user is called with the right arguments
        after iterating the user's roles.

        There are no assertions in this test because the checking is handled
        by mox in the VerifyAll() call in tearDown().
        """
        keystoneclient = self.stub_keystoneclient()
        tenant = self.tenants.first()

        keystoneclient.roles = self.mox.CreateMockAnything()
        keystoneclient.roles.roles_for_user(self.user.id,
                                            tenant.id).AndReturn(self.roles)
        for role in self.roles:
            keystoneclient.roles.revoke(role.id,
                                        domain=None,
                                        group=None,
                                        project=tenant.id,
                                        user=self.user.id)
        self.mox.ReplayAll()
        api.keystone.remove_tenant_user(self.request, tenant.id, self.user.id)

    def test_get_default_role(self):
        keystoneclient = self.stub_keystoneclient()
        keystoneclient.roles = self.mox.CreateMockAnything()
        keystoneclient.roles.list().AndReturn(self.roles)
        self.mox.ReplayAll()
        role = api.keystone.get_default_role(self.request)
        self.assertEqual(self.role, role)
        # Verify that a second call doesn't hit the API again,
        # (it would show up in mox as an unexpected method call)
        role = api.keystone.get_default_role(self.request)


class ServiceAPITests(test.APITestCase):
    def test_service_wrapper(self):
        catalog = self.service_catalog
        identity_data = api.base.get_service_from_catalog(catalog, "identity")
        identity_data['id'] = 1
        region = identity_data["endpoints"][0]["region"]
        service = api.keystone.Service(identity_data, region)
        self.assertEqual(u"identity (native backend)", six.text_type(service))
        self.assertEqual(identity_data["endpoints"][0]["region"],
                         service.region)
        self.assertEqual("http://int.keystone.example.com:5000/v2.0",
                         service.url)
        self.assertEqual("http://public.keystone.example.com:5000/v2.0",
                         service.public_url)
        self.assertEqual("int.keystone.example.com", service.host)

    def test_service_wrapper_service_in_region(self):
        catalog = self.service_catalog
        compute_data = api.base.get_service_from_catalog(catalog, "compute")
        compute_data['id'] = 1
        region = compute_data["endpoints"][1]["region"]
        service = api.keystone.Service(compute_data, region)
        self.assertEqual(u"compute", six.text_type(service))
        self.assertEqual(compute_data["endpoints"][1]["region"],
                         service.region)
        self.assertEqual("http://int.nova2.example.com:8774/v2",
                         service.url)
        self.assertEqual("http://public.nova2.example.com:8774/v2",
                         service.public_url)
        self.assertEqual("int.nova2.example.com", service.host)
