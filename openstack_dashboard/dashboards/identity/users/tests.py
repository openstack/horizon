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

from socket import timeout as socket_timeout

from django.test.utils import override_settings
from django.urls import reverse

import mock

from openstack_dashboard import api
from openstack_dashboard.dashboards.identity.users import tabs
from openstack_dashboard.test import helpers as test


USERS_INDEX_URL = reverse('horizon:identity:users:index')
USER_CREATE_URL = reverse('horizon:identity:users:create')
USER_UPDATE_URL = reverse('horizon:identity:users:update', args=[1])
USER_DETAIL_URL = reverse('horizon:identity:users:detail', args=[1])
USER_CHANGE_PASSWORD_URL = reverse('horizon:identity:users:change_password',
                                   args=[1])


class UsersViewTests(test.BaseAdminViewTests):

    def _get_default_domain(self):
        domain = {"id": self.request.session.get('domain_context',
                                                 None),
                  "name": self.request.session.get('domain_context_name',
                                                   None)}
        return api.base.APIDictWrapper(domain)

    def _get_users(self, domain_id):
        if not domain_id:
            users = self.users.list()
        else:
            users = [user for user in self.users.list()
                     if user.domain_id == domain_id]
        return users

    @test.create_mocks({api.keystone: ('user_list',
                                       'get_effective_domain_id',
                                       'domain_lookup')})
    def test_index(self, with_domain=False):
        domain = self._get_default_domain()
        domain_id = domain.id
        filters = {}
        users = self._get_users(domain_id)

        if not with_domain:
            self.mock_get_effective_domain_id.return_value = domain_id
        self.mock_user_list.return_value = users
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        res = self.client.get(USERS_INDEX_URL)
        self.assertTemplateUsed(res, 'identity/users/index.html')
        self.assertItemsEqual(res.context['table'].data, users)

        if domain_id:
            for user in res.context['table'].data:
                self.assertItemsEqual(user.domain_id, domain_id)

        if with_domain:
            self.mock_get_effective_domain_id.assert_not_called()
        else:
            self.mock_get_effective_domain_id.assert_called_once_with(
                test.IsHttpRequest())
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain_id,
                                                    filters=filters)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())

    def test_index_with_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_index(with_domain=True)

    @override_settings(USER_TABLE_EXTRA_INFO={'phone_num': 'Phone Number'})
    @test.create_mocks({api.keystone: ('user_create',
                                       'get_default_domain',
                                       'tenant_list',
                                       'add_tenant_user_role',
                                       'get_default_role',
                                       'roles_for_user',
                                       'role_list')})
    def test_create(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id
        phone_number = "+81-3-1234-5678"

        role = self.roles.first()

        self.mock_get_default_domain.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        self.mock_user_create.return_value = user
        self.mock_role_list.return_value = self.roles.list()
        self.mock_get_default_role.return_value = role
        self.mock_roles_for_user.return_value = []
        self.mock_add_tenant_user_role.return_value = None

        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'password': user.password,
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'enabled': True,
                    'confirm_password': user.password,
                    'phone_num': phone_number}

        # django.test.client doesn't like None fields in forms
        for key in list(formData):
            if formData[key] is None:
                del formData[key]

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_get_default_domain.assert_has_calls([
            mock.call(test.IsHttpRequest()),
            mock.call(test.IsHttpRequest(), False),
        ])
        self.assertEqual(2, self.mock_get_default_domain.call_count)

        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), user=None)

        kwargs = {'phone_num': phone_number}
        self.mock_user_create.assert_called_once_with(
            test.IsHttpRequest(), name=user.name, description=user.description,
            email=user.email, password=user.password, project=self.tenant.id,
            enabled=True, domain=domain_id, **kwargs)
        self.mock_role_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_get_default_role.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_roles_for_user.assert_called_once_with(
            test.IsHttpRequest(), user.id, self.tenant.id)
        self.mock_add_tenant_user_role.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id, user.id, role.id)

    def test_create_with_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_create()

    @test.create_mocks({api.keystone: ('user_create',
                                       'get_default_domain',
                                       'add_tenant_user_role',
                                       'tenant_list',
                                       'get_default_role',
                                       'roles_for_user',
                                       'role_list')})
    def test_create_with_empty_email(self):
        user = self.users.get(id="5")
        domain = self._get_default_domain()
        domain_id = domain.id
        role = self.roles.first()

        self.mock_get_default_domain.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_user_create.return_value = user
        self.mock_role_list.return_value = self.roles.list()
        self.mock_get_default_role.return_value = role
        self.mock_add_tenant_user_role.return_value = None
        self.mock_roles_for_user.return_value = []

        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'description': user.description,
                    'email': "",
                    'enabled': True,
                    'password': user.password,
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': user.password}

        # django.test.client doesn't like None fields in forms
        for key in list(formData):
            if formData[key] is None:
                del formData[key]

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_get_default_domain.assert_has_calls([
            mock.call(test.IsHttpRequest()),
            mock.call(test.IsHttpRequest(), False),
        ])
        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), user=user.id)
        self.mock_user_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=user.name,
            description=user.description,
            email=user.email,
            password=user.password,
            project=self.tenant.id,
            enabled=True,
            domain=domain_id)
        self.mock_role_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_get_default_role.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_add_tenant_user_role.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id, user.id, role.id)
        self.mock_roles_for_user.assert_called_once_with(
            test.IsHttpRequest(), user.id, self.tenant.id)

    @test.create_mocks({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_with_password_mismatch(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id

        self.mock_get_default_domain.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_role_list.return_value = self.roles.list()
        self.mock_get_default_role.return_value = self.roles.first()

        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': "doesntmatch"}

        # django.test.client doesn't like None fields in forms
        for key in list(formData):
            if formData[key] is None:
                del formData[key]

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(res, "form", None, ['Passwords do not match.'])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_domain, 2,
            mock.call(test.IsHttpRequest()))
        if api.keystone.VERSIONS.active >= 3:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_tenant_list, 2,
                mock.call(test.IsHttpRequest(), domain=domain_id))
        else:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_tenant_list, 2,
                mock.call(test.IsHttpRequest(), user=None))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_validation_for_password_too_short(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id

        self.mock_get_default_domain.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_role_list.return_value = self.roles.list()
        self.mock_get_default_role.return_value = self.roles.first()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'four',
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': 'four'}

        # django.test.client doesn't like None fields in forms
        for key in list(formData):
            if formData[key] is None:
                del formData[key]

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_domain, 2,
            mock.call(test.IsHttpRequest()))
        if api.keystone.VERSIONS.active >= 3:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_tenant_list, 2,
                mock.call(test.IsHttpRequest(), domain=domain_id))
        else:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_tenant_list, 2,
                mock.call(test.IsHttpRequest(), user=None))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_validation_for_password_too_long(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id

        self.mock_get_default_domain.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_role_list.return_value = self.roles.list()
        self.mock_get_default_role.return_value = self.roles.first()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'MoreThanEighteenChars',
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': 'MoreThanEighteenChars'}

        # django.test.client doesn't like None fields in forms
        for key in list(formData):
            if formData[key] is None:
                del formData[key]

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_domain, 2,
            mock.call(test.IsHttpRequest()))
        if api.keystone.VERSIONS.active >= 3:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_tenant_list, 2,
                mock.call(test.IsHttpRequest(), domain=domain_id))
        else:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_tenant_list, 2,
                mock.call(test.IsHttpRequest(), user=None))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))

    @override_settings(USER_TABLE_EXTRA_INFO={'phone_num': 'Phone Number'})
    @test.create_mocks({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update',)})
    def test_update(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)
        phone_number = "+81-3-1234-5678"

        self.mock_user_get.return_value = user
        self.mock_domain_get.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_user_update.return_value = None

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'project': self.tenant.id,
                    'phone_num': phone_number}
        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), user=user.id)
        kwargs = {'phone_num': phone_number}
        self.mock_user_update.assert_called_once_with(test.IsHttpRequest(),
                                                      user.id,
                                                      email=user.email,
                                                      name=user.name,
                                                      **kwargs)

    @test.create_mocks({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update',)})
    def test_update_default_project(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)
        new_project_id = self.tenants.get(id="3").id

        self.mock_user_get.return_value = user
        self.mock_domain_get.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_user_update.return_value = None

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'project': new_project_id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), user=user.id)
        self.mock_user_update.assert_called_once_with(test.IsHttpRequest(),
                                                      user.id,
                                                      email=user.email,
                                                      name=user.name,
                                                      project=new_project_id)

    @test.create_mocks({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update',)})
    def test_update_with_no_email_attribute(self):
        user = self.users.get(id="5")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        self.mock_user_get.return_value = user
        self.mock_domain_get.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_user_update.return_value = None

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': user.description,
                    'email': "",
                    'project': self.tenant.id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), user=user.id)
        self.mock_user_update.assert_called_once_with(test.IsHttpRequest(),
                                                      user.id,
                                                      email=user.email or "",
                                                      name=user.name,
                                                      project=self.tenant.id)

    @test.create_mocks({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'keystone_can_edit_user', )})
    def test_update_with_keystone_can_edit_user_false(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        self.mock_user_get.return_value = user
        self.mock_domain_get.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_keystone_can_edit_user.return_value = False

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'project': self.tenant.id, }

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(
                test.IsHttpRequest(), user=user.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_keystone_can_edit_user, 2,
            mock.call())

    @test.create_mocks({api.keystone: ('user_get',
                                       'user_update_password')})
    def test_change_password(self):
        user = self.users.get(id="5")
        test_password = 'normalpwd'

        self.mock_user_get.return_value = user
        self.mock_user_update_password.return_value = None

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': test_password,
                    'confirm_password': test_password}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_user_update_password.assert_called_once_with(
            test.IsHttpRequest(), user.id, test_password, admin=False)

    @test.create_mocks({api.keystone: ('user_get',
                                       'user_verify_admin_password')})
    @override_settings(ENFORCE_PASSWORD_CHECK=True)
    def test_change_password_validation_for_admin_password(self):
        user = self.users.get(id="1")
        test_password = 'normalpwd'
        admin_password = 'secret'

        self.mock_user_get.return_value = user
        self.mock_user_verify_admin_password.return_value = None

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': test_password,
                    'confirm_password': test_password,
                    'admin_password': admin_password}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertFormError(res, "form", None,
                             ['The admin password is incorrect.'])
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_user_verify_admin_password.assert_called_once_with(
            test.IsHttpRequest(), admin_password)

    @test.create_mocks({api.keystone: ('user_get',)})
    def test_update_validation_for_password_too_short(self):
        user = self.users.get(id="1")

        self.mock_user_get.return_value = user

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': 't',
                    'confirm_password': 't'}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)

    @test.create_mocks({api.keystone: ('user_get',)})
    def test_update_validation_for_password_too_long(self):
        user = self.users.get(id="1")

        self.mock_user_get.return_value = user

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': 'ThisIsASuperLongPassword',
                    'confirm_password': 'ThisIsASuperLongPassword'}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_update_enabled',
                                       'user_list',
                                       'domain_lookup')})
    def test_enable_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        filters = {}
        user = self.users.get(id="2")
        users = self._get_users(domain_id)
        user.enabled = False

        self.mock_get_effective_domain_id.return_value = None
        self.mock_user_list.return_value = users
        self.mock_user_update_enabled.return_value = user
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_user_list.assert_called_once_with(
            test.IsHttpRequest(), domain=domain_id, filters=filters)
        self.mock_user_update_enabled.assert_called_once_with(
            test.IsHttpRequest(), user.id, True)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_update_enabled',
                                       'user_list',
                                       'domain_lookup')})
    def test_disable_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        filters = {}
        user = self.users.get(id="2")
        users = self._get_users(domain_id)

        self.assertTrue(user.enabled)

        self.mock_get_effective_domain_id.return_value = None
        self.mock_user_list.return_value = users
        self.mock_user_update_enabled.return_value = user
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_user_list.assert_called_once_with(
            test.IsHttpRequest(), domain=domain_id, filters=filters)
        self.mock_user_update_enabled.assert_called_once_with(
            test.IsHttpRequest(), user.id, False)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_update_enabled',
                                       'user_list',
                                       'domain_lookup')})
    def test_enable_disable_user_exception(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        filters = {}
        user = self.users.get(id="2")
        users = self._get_users(domain_id)
        user.enabled = False

        self.mock_get_effective_domain_id.return_value = None
        self.mock_user_list.return_value = users
        self.mock_user_update_enabled.side_effect = self.exceptions.keystone
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_user_list.assert_called_once_with(
            test.IsHttpRequest(), domain=domain_id, filters=filters)
        self.mock_user_update_enabled.assert_called_once_with(
            test.IsHttpRequest(), user.id, True)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_list',
                                       'domain_lookup')})
    def test_disabling_current_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        filters = {}
        users = self._get_users(domain_id)

        self.mock_get_effective_domain_id.return_value = None
        self.mock_user_list.return_value = users
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        formData = {'action': 'users__toggle__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to disable user: '
                         u'test_user')

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_effective_domain_id, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_user_list, 2,
            mock.call(test.IsHttpRequest(), domain=domain_id, filters=filters))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_domain_lookup, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_list',
                                       'domain_lookup')})
    def test_disabling_current_user_domain_name(self):
        domain = self._get_default_domain()
        domains = self.domains.list()
        filters = {}
        domain_id = domain.id
        users = self._get_users(domain_id)
        domain_lookup = dict((d.id, d.name) for d in domains)

        self.mock_get_effective_domain_id.return_value = None
        for u in users:
            u.domain_name = domain_lookup.get(u.domain_id)
        self.mock_domain_lookup.return_value = domain_lookup
        self.mock_user_list.return_value = users

        formData = {'action': 'users__toggle__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to disable user: '
                         u'test_user')

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_effective_domain_id, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_domain_lookup, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_user_list, 2,
            mock.call(test.IsHttpRequest(), domain=domain_id, filters=filters))

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_list',
                                       'domain_lookup')})
    def test_delete_user_with_improper_permissions(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        filters = {}
        users = self._get_users(domain_id)

        self.mock_get_effective_domain_id.return_value = None
        self.mock_user_list.return_value = users
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to delete user: %s'
                         % self.request.user.username)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_effective_domain_id, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_user_list, 2,
            mock.call(test.IsHttpRequest(), domain=domain_id, filters=filters))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_domain_lookup, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_list',
                                       'domain_lookup')})
    def test_delete_user_with_improper_permissions_domain_name(self):
        domain = self._get_default_domain()
        domains = self.domains.list()
        domain_id = domain.id
        filters = {}
        users = self._get_users(domain_id)
        domain_lookup = dict((d.id, d.name) for d in domains)

        self.mock_get_effective_domain_id.return_value = None
        for u in users:
            u.domain_name = domain_lookup.get(u.domain_id)
        self.mock_user_list.return_value = users
        self.mock_domain_lookup.return_value = domain_lookup

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to delete user: %s'
                         % self.request.user.username)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_effective_domain_id, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_user_list, 2,
            mock.call(test.IsHttpRequest(), domain=domain_id, filters=filters))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_domain_lookup, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get')})
    def test_detail_view(self):
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)

        self.mock_domain_get.return_value = domain
        self.mock_user_get.return_value = user
        self.mock_tenant_get.return_value = tenant

        res = self.client.get(USER_DETAIL_URL, args=[user.id])

        # The first tab is overview, it is the one loaded without query param
        # in the url.
        self.assertTemplateUsed(res, 'identity/users/_detail_overview.html')
        self.assertEqual(res.context['user'].name, user.name)
        self.assertEqual(res.context['user'].id, user.id)
        self.assertEqual(res.context['project_name'], tenant.name)

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     user.project_id)

    @test.create_mocks({api.keystone: ('user_get',)})
    def test_detail_view_with_exception(self):
        user = self.users.get(id="1")

        self.mock_user_get.side_effect = self.exceptions.keystone

        res = self.client.get(USER_DETAIL_URL, args=[user.id])

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get')})
    def test_detail_view_overview_tab(self):
        """Test the overview tab of the detail view .

        Test the overview tab using directly the url targeting the tab.
        """
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)

        self.mock_domain_get.return_value = domain
        self.mock_user_get.return_value = user
        self.mock_tenant_get.return_value = tenant

        # Url of the overview tab of the detail view
        url = USER_DETAIL_URL % [user.id]
        detail_view = tabs.UserDetailTabs(self.request, user=user)
        overview_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("overview").get_id()
        )
        url += overview_tab_link

        res = self.client.get(url)

        self.assertTemplateUsed(res, 'identity/users/_detail_overview.html')
        self.assertEqual(res.context['user'].name, user.name)
        self.assertEqual(res.context['user'].id, user.id)
        self.assertEqual(res.context['project_name'], tenant.name)

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     user.project_id)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get',
                                       'role_assignments_list',
                                       'group_list')})
    def test_detail_view_role_assignments_tab(self):
        """Test the role assignments tab of the detail view ."""
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)
        user_role_assignments = self.role_assignments.filter(
            user={'id': user.id})
        user_group = self.groups.first()
        group_role_assignments = self.role_assignments.filter(
            group={'id': user_group.id})

        self.mock_domain_get.return_value = domain
        self.mock_user_get.return_value = user
        self.mock_tenant_get.return_value = tenant
        self.mock_group_list.return_value = [user_group]

        def _role_assignments_list_side_effect(request, user=None, group=None,
                                               include_subtree=False,
                                               include_names=True):
            # role assignments should be called twice, once with the user and
            # another one with the group.
            if group:
                return group_role_assignments
            return user_role_assignments

        self.mock_role_assignments_list.side_effect = \
            _role_assignments_list_side_effect

        # Url of the role assignment tab of the detail view
        url = USER_DETAIL_URL % [user.id]
        detail_view = tabs.UserDetailTabs(self.request, user=user)
        role_assignments_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("roleassignments").get_id()
        )
        url += role_assignments_tab_link

        res = self.client.get(url)

        # Check the template expected has been used
        self.assertTemplateUsed(res,
                                "horizon/common/_detail_table.html")

        # Check the table contains the expected data
        role_assignments_expected = user_role_assignments
        role_assignments_expected.extend(group_role_assignments)
        role_assignments_observed = res.context["table"].data
        self.assertItemsEqual(role_assignments_expected,
                              role_assignments_observed)

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     user.project_id)
        # role assignments should be called twice, once with the user and
        # another one with the group.
        calls = [mock.call(test.IsHttpRequest(), user=user,
                           include_subtree=False, include_names=True),
                 mock.call(test.IsHttpRequest(), group=user_group,
                           include_subtree=False, include_names=True), ]
        self.mock_role_assignments_list.assert_has_calls(calls)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get',
                                       'role_assignments_list')})
    def test_detail_view_role_assignments_tab_with_exception(self):
        """Test the role assignments tab with exception.

        The table is displayed empty and an error message pop if the role
        assignment request fails.
        """
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)

        self.mock_domain_get.return_value = domain
        self.mock_user_get.return_value = user
        self.mock_tenant_get.return_value = tenant
        self.mock_role_assignments_list.side_effect = self.exceptions.keystone

        # Url of the role assignment tab of the detail view
        url = USER_DETAIL_URL % [user.id]
        detail_view = tabs.UserDetailTabs(self.request, user=user)
        role_assignments_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("roleassignments").get_id()
        )
        url += role_assignments_tab_link

        res = self.client.get(url)

        # Check the role assignment table is empty
        self.assertEqual(res.context["table"].data, [])
        # Check one error message is displayed
        self.assertMessageCount(res, error=1)

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     user.project_id)
        self.mock_role_assignments_list.assert_called_once_with(
            test.IsHttpRequest(), user=user, include_subtree=False,
            include_names=True)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get',
                                       'group_list')})
    def test_detail_view_groups_tab(self):
        """Test the groups tab of the detail view ."""
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)
        groups = self.groups.list()

        self.mock_domain_get.return_value = domain
        self.mock_user_get.return_value = user
        self.mock_tenant_get.return_value = tenant
        self.mock_group_list.return_value = groups

        # Url of the role assignment tab of the detail view
        url = USER_DETAIL_URL % [user.id]
        detail_view = tabs.UserDetailTabs(self.request, user=user)
        group_tab_link = "?%s=%s" % (detail_view.param_name,
                                     detail_view.get_tab("groups").get_id())
        url += group_tab_link

        res = self.client.get(url)

        # Check the template expected has been used
        self.assertTemplateUsed(res, "horizon/common/_detail_table.html")

        # Check the table contains the good data
        groups_expected = groups
        groups_observed = res.context["table"].data
        self.assertItemsEqual(groups_expected, groups_observed)

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     user.project_id)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     user=user.id)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get',
                                       'group_list')})
    def test_detail_view_groups_tab_with_exception(self):
        """Test the groups tab of the detail view .

        The table is displayed empty and an error message pop if the groups
        request fails.
        """
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)

        self.mock_domain_get.return_value = domain
        self.mock_user_get.return_value = user
        self.mock_tenant_get.return_value = tenant
        self.mock_group_list.side_effect = self.exceptions.keystone

        # Url of the role assignment tab of the detail view
        url = USER_DETAIL_URL % [user.id]
        detail_view = tabs.UserDetailTabs(self.request, user=user)
        group_tab_link = "?%s=%s" % (detail_view.param_name,
                                     detail_view.get_tab("groups").get_id())
        url += group_tab_link

        res = self.client.get(url)

        # Check the groups table is empty
        self.assertEqual(res.context["table"].data, [])
        # Check one error message is displayed
        self.assertMessageCount(res, error=1)

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     user.project_id)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     user=user.id)

    @test.create_mocks({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',)})
    def test_get_update_form_init_values(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        self.mock_user_get.return_value = user
        self.mock_domain_get.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        res = self.client.get(USER_UPDATE_URL)

        # Check that the form contains the default values as initialized by
        # the UpdateView
        self.assertEqual(res.context['form']['name'].value(), user.name)
        self.assertEqual(res.context['form']['email'].value(), user.email)
        self.assertEqual(res.context['form']['description'].value(),
                         user.description)
        self.assertEqual(res.context['form']['project'].value(),
                         user.project_id)
        self.assertEqual(res.context['form']['domain_id'].value(),
                         user.domain_id)
        self.assertEqual(res.context['form']['domain_name'].value(),
                         domain.name)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                      domain=domain_id)

    @test.create_mocks({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update',)})
    def test_update_different_description(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        self.mock_user_get.return_value = user
        self.mock_domain_get.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_user_update.return_value = None

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': 'changed',
                    'email': user.email,
                    'project': self.tenant.id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        if api.keystone.VERSIONS.active >= 3:
            self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                          domain=domain.id)
        else:
            self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                          user=user.id)
        self.mock_user_update.assert_called_once_with(test.IsHttpRequest(),
                                                      user.id,
                                                      email=user.email,
                                                      name=user.name,
                                                      description='changed')

    @test.update_settings(FILTER_DATA_FIRST={'identity.users': True})
    def test_index_with_filter_first(self):
        res = self.client.get(USERS_INDEX_URL)
        self.assertTemplateUsed(res, 'identity/users/index.html')
        users = res.context['table'].data
        self.assertItemsEqual(users, [])


class SeleniumTests(test.SeleniumAdminTestCase):
    def _get_default_domain(self):
        domain = {"id": None, "name": None}
        return api.base.APIDictWrapper(domain)

    @test.create_mocks({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'get_default_role',
                                       'role_list',
                                       'user_list',
                                       'domain_lookup')})
    def test_modal_create_user_with_passwords_not_matching(self):
        domain = self._get_default_domain()

        self.mock_get_default_domain.return_value = domain
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_role_list.return_value = self.roles.list()
        self.mock_user_list.return_value = self.users.list()
        self.mock_domain_lookup.return_value = {None: None}
        self.mock_get_default_role.return_value = self.roles.first()

        self.selenium.get("%s%s" % (self.live_server_url, USERS_INDEX_URL))

        # Open the modal menu
        self.selenium.find_element_by_id("users__action_create").click()
        wait = self.ui.WebDriverWait(self.selenium, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: self.selenium.find_element_by_id("id_name"))

        self.assertFalse(self._is_element_present("id_confirm_password_error"),
                         "Password error element shouldn't yet exist.")
        self.selenium.find_element_by_id("id_name").send_keys("Test User")
        self.selenium.find_element_by_id("id_password").send_keys("test")
        self.selenium.find_element_by_id("id_confirm_password").send_keys("te")
        self.selenium.find_element_by_id("id_email").send_keys("a@b.com")

        wait.until(lambda x: self.selenium.find_element_by_id(
            "id_confirm_password_error"))

        self.assertTrue(self._is_element_present("id_confirm_password_error"),
                        "Couldn't find password error element.")

        self.assertEqual(2, self.mock_get_default_domain.call_count)
        self.mock_get_default_domain.assert_has_calls([
            mock.call(test.IsHttpRequest()),
            mock.call(test.IsHttpRequest()),
        ])

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                      domain=None)
        self.mock_role_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=None, filters={})
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())
        self.mock_get_default_role.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('user_get',)})
    def test_update_user_with_passwords_not_matching(self):
        self.mock_user_get.return_value = self.user

        self.selenium.get("%s%s" % (self.live_server_url,
                                    USER_CHANGE_PASSWORD_URL))

        self.assertFalse(self._is_element_present("id_confirm_password_error"),
                         "Password error element shouldn't yet exist.")
        self.selenium.find_element_by_id("id_password").send_keys("test")
        self.selenium.find_element_by_id("id_confirm_password").send_keys("te")
        self.selenium.find_element_by_id("id_name").click()
        self.assertTrue(self._is_element_present("id_confirm_password_error"),
                        "Couldn't find password error element.")
        self.mock_user_get.assert_called_once_with(test.IsHttpRequest(), '1',
                                                   admin=False)

    def _is_element_present(self, element_id):
        try:
            self.selenium.find_element_by_id(element_id)
            return True
        except Exception:
            return False
