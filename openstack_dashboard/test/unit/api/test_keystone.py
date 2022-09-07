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
from random import choice
from unittest import mock


from django.test.utils import override_settings
from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.test import helpers as test


class RoleAPITests(test.APIMockTestCase):
    def setUp(self):
        super().setUp()
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

    @mock.patch.object(api.keystone, 'keystoneclient')
    @mock.patch.object(api.keystone, 'DEFAULT_ROLE', new=None)
    def test_get_case_insensitive_default_role(self, mock_keystoneclient):
        def convert_to_random_case(role_):
            new_name = list()
            for char in list(role_.name):
                new_name.append(getattr(char, choice(["lower", "upper"]))())
            role_.name = role_._info["name"] = "".join(new_name)
            return role_
        keystoneclient = mock_keystoneclient.return_value
        keystoneclient.roles.list.return_value = list()
        for role in self.roles:
            role = convert_to_random_case(role)
            keystoneclient.roles.list.return_value.append(role)
        role = api.keystone.get_default_role(self.request)
        self.assertEqual(self.role.name.lower(), role.name.lower())
        # Verify that a second call doesn't hit the API again,
        # so we use assert_called_once_with() here.
        api.keystone.get_default_role(self.request)
        keystoneclient.roles.list.assert_called_once_with()


class ServiceAPITests(test.APIMockTestCase):
    @override_settings(OPENSTACK_ENDPOINT_TYPE='internalURL')
    def test_service_wrapper_for_internal_endpoint_type(self):
        catalog = self.service_catalog
        identity_data = api.base.get_service_from_catalog(catalog, "identity")
        # 'Service' class below requires 'id', so populate it here.
        identity_data['id'] = 1
        service = api.keystone.Service(identity_data, "RegionOne")
        self.assertEqual(u"identity (native backend)", str(service))
        self.assertEqual("RegionOne", service.region)
        self.assertEqual("http://int.keystone.example.com/identity/v3",
                         service.url)
        self.assertEqual("http://public.keystone.example.com/identity/v3",
                         service.public_url)
        self.assertEqual("int.keystone.example.com", service.host)

    @override_settings(OPENSTACK_ENDPOINT_TYPE='publicURL')
    def test_service_wrapper_for_public_endpoint_type(self):
        catalog = self.service_catalog
        identity_data = api.base.get_service_from_catalog(catalog, "identity")
        # 'Service' class below requires 'id', so populate it here.
        identity_data['id'] = 1
        service = api.keystone.Service(identity_data, "RegionOne")
        self.assertEqual(u"identity (native backend)", str(service))
        self.assertEqual("RegionOne", service.region)
        self.assertEqual("http://public.keystone.example.com/identity/v3",
                         service.url)
        self.assertEqual("http://public.keystone.example.com/identity/v3",
                         service.public_url)
        self.assertEqual("public.keystone.example.com", service.host)

    @override_settings(OPENSTACK_ENDPOINT_TYPE='internalURL')
    def test_service_wrapper_in_region_for_internal_endpoint_type(self):
        catalog = self.service_catalog
        compute_data = api.base.get_service_from_catalog(catalog, "compute")
        # 'Service' class below requires 'id', so populate it here.
        compute_data['id'] = 1
        service = api.keystone.Service(compute_data, 'RegionTwo')
        self.assertEqual(u"compute", str(service))
        self.assertEqual("RegionTwo", service.region)
        self.assertEqual("http://int.nova2.example.com:8774/v2",
                         service.url)
        self.assertEqual("http://public.nova2.example.com:8774/v2",
                         service.public_url)
        self.assertEqual("int.nova2.example.com", service.host)

    @override_settings(OPENSTACK_ENDPOINT_TYPE='publicURL')
    def test_service_wrapper_service_in_region_for_public_endpoint_type(self):
        catalog = self.service_catalog
        compute_data = api.base.get_service_from_catalog(catalog, "compute")
        # 'Service' class below requires 'id', so populate it here.
        compute_data['id'] = 1
        service = api.keystone.Service(compute_data, 'RegionTwo')
        self.assertEqual(u"compute", str(service))
        self.assertEqual("RegionTwo", service.region)
        self.assertEqual("http://public.nova2.example.com:8774/v2",
                         service.url)
        self.assertEqual("http://public.nova2.example.com:8774/v2",
                         service.public_url)
        self.assertEqual("public.nova2.example.com", service.host)


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


class ApplicationCredentialsAPITests(test.APIMockTestCase):

    @mock.patch.object(policy, 'check')
    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_application_credential_create_domain_token_removed(
            self, mock_keystoneclient, mock_policy):
        self.request.session['domain_token'] = 'some_token'
        mock_policy.return_value = False
        api.keystone.application_credential_create(self.request, None)
        mock_keystoneclient.assert_called_once_with(
            self.request, force_scoped=True)

    @mock.patch.object(policy, 'check')
    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_application_credential_create_domain_token_not_removed_policy_true(
            self, mock_keystoneclient, mock_policy):
        self.request.session['domain_token'] = 'some_token'
        mock_policy.return_value = True
        api.keystone.application_credential_create(self.request, None)
        mock_keystoneclient.assert_called_once_with(
            self.request, force_scoped=False)

    @mock.patch.object(policy, 'check')
    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_application_credential_create_domain_token_not_removed_no_token(
            self, mock_keystoneclient, mock_policy):
        mock_policy.return_value = True
        api.keystone.application_credential_create(self.request, None)
        mock_keystoneclient.assert_called_once_with(
            self.request, force_scoped=False)

    @mock.patch.object(policy, 'check')
    @mock.patch.object(api.keystone, 'keystoneclient')
    def test_application_credential_create_domain_token_not_removed_no_project(
            self, mock_keystoneclient, mock_policy):
        self.request.session['domain_token'] = 'some_token'
        mock_policy.return_value = True
        self.request.user.project_id = None
        api.keystone.application_credential_create(self.request, None)
        mock_keystoneclient.assert_called_once_with(
            self.request, force_scoped=False)
