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

import mock
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class RoleAPITests(test.APIMockTestCase):
    def setUp(self):
        super(RoleAPITests, self).setUp()
        self.role = self.roles.member
        self.roles = self.roles.list()

    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_remove_tenant_user(self, mock_keystoneclient):
        """Tests api.keystone.remove_tenant_user

        Verifies that remove_tenant_user is called with the right arguments
        after iterating the user's roles.
        """
        keystoneclient = mock_keystoneclient.return_value
        tenant = self.tenants.first()

        keystoneclient.roles.roles_for_user.return_value = self.roles
        keystoneclient.roles.revoke.side_effect = [None for role in self.roles]

        api.keystone.remove_tenant_user(self.request, tenant.id, self.user.id)

        keystoneclient.roles.roles_for_user.assert_called_once_with(
            self.user.id, tenant.id)
        keystoneclient.roles.revoke.assert_has_calls(
            [mock.call(role.id,
                       domain=None,
                       group=None,
                       project=tenant.id,
                       user=self.user.id)
             for role in self.roles]
        )

    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_get_default_role(self, mock_keystoneclient):
        keystoneclient = mock_keystoneclient.return_value
        keystoneclient.roles.list.return_value = self.roles

        role = api.keystone.get_default_role(self.request)
        self.assertEqual(self.role, role)

        # Verify that a second call doesn't hit the API again,
        # so we use assert_called_once_with() here.
        role = api.keystone.get_default_role(self.request)
        keystoneclient.roles.list.assert_called_once_with()


class ServiceAPITests(test.APIMockTestCase):
    def test_service_wrapper(self):
        catalog = self.service_catalog
        identity_data = api.base.get_service_from_catalog(catalog, "identity")
        identity_data['id'] = 1
        region = identity_data["endpoints"][0]["region"]
        service = api.keystone.Service(identity_data, region)
        self.assertEqual(u"identity (native backend)", six.text_type(service))
        self.assertEqual(identity_data["endpoints"][0]["region"],
                         service.region)
        self.assertEqual("http://int.keystone.example.com:5000/v3",
                         service.url)
        self.assertEqual("http://public.keystone.example.com:5000/v3",
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


class APIVersionTests(test.APIMockTestCase):
    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_get_identity_api_version(self, mock_keystoneclient):
        keystoneclient = mock_keystoneclient.return_value
        endpoint_data = mock.Mock()
        endpoint_data.api_version = (3, 10)
        keystoneclient.session.get_endpoint_data.return_value = endpoint_data
        api_version = api.keystone.get_identity_api_version(self.request)
        keystoneclient.session.get_endpoint_data.assert_called_once_with(
            service_type='identity')
        self.assertEqual((3, 10), api_version)
