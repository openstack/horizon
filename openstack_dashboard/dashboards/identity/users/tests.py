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

from socket import timeout as socket_timeout  # noqa

import django
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings

from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
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

    @test.create_stubs({api.keystone: ('user_list',
                                       'get_effective_domain_id',
                                       'domain_lookup')})
    def test_index(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        users = self._get_users(domain_id)

        api.keystone.get_effective_domain_id(IgnoreArg()).AndReturn(domain_id)

        api.keystone.user_list(IgnoreArg(),
                               domain=domain_id).AndReturn(users)
        api.keystone.domain_lookup(IgnoreArg()).AndReturn({domain.id:
                                                           domain.name})

        self.mox.ReplayAll()
        res = self.client.get(USERS_INDEX_URL)
        self.assertTemplateUsed(res, 'identity/users/index.html')
        self.assertItemsEqual(res.context['table'].data, users)

        if domain_id:
            for user in res.context['table'].data:
                self.assertItemsEqual(user.domain_id, domain_id)

    def test_index_with_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_index()

    @test.create_stubs({api.keystone: ('user_create',
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

        role = self.roles.first()

        api.keystone.get_default_domain(IgnoreArg()) \
            .AndReturn(domain)
        api.keystone.get_default_domain(IgnoreArg(), False) \
            .AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain.id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=None).AndReturn(
                [self.tenants.list(), False])

        api.keystone.user_create(IgnoreArg(),
                                 name=user.name,
                                 description=user.description,
                                 email=user.email,
                                 password=user.password,
                                 project=self.tenant.id,
                                 enabled=True,
                                 domain=domain_id).AndReturn(user)
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()).AndReturn(role)
        api.keystone.roles_for_user(IgnoreArg(), user.id, self.tenant.id)
        api.keystone.add_tenant_user_role(IgnoreArg(), self.tenant.id,
                                          user.id, role.id)

        self.mox.ReplayAll()

        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'password': user.password,
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'enabled': True,
                    'confirm_password': user.password}
        res = self.client.post(USER_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    def test_create_with_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_create()

    @test.create_stubs({api.keystone: ('user_create',
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
        api.keystone.get_default_domain(IgnoreArg()) \
            .AndReturn(domain)
        api.keystone.get_default_domain(IgnoreArg(), False) \
            .AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain.id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=user.id).AndReturn(
                [self.tenants.list(), False])

        api.keystone.user_create(IgnoreArg(),
                                 name=user.name,
                                 description=user.description,
                                 email=user.email,
                                 password=user.password,
                                 project=self.tenant.id,
                                 enabled=True,
                                 domain=domain_id).AndReturn(user)
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()).AndReturn(role)
        api.keystone.add_tenant_user_role(IgnoreArg(), self.tenant.id,
                                          user.id, role.id)
        api.keystone.roles_for_user(IgnoreArg(), user.id, self.tenant.id)

        self.mox.ReplayAll()
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
        res = self.client.post(USER_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_with_password_mismatch(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id

        api.keystone.get_default_domain(IgnoreArg()) \
            .MultipleTimes().AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain_id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=None).AndReturn(
                [self.tenants.list(), False])

        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())
        if django.VERSION >= (1, 9):
            if api.keystone.VERSIONS.active >= 3:
                api.keystone.tenant_list(
                    IgnoreArg(), domain=domain_id).AndReturn(
                    [self.tenants.list(), False])
            else:
                api.keystone.tenant_list(
                    IgnoreArg(), user=None).AndReturn(
                    [self.tenants.list(), False])

            api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
            api.keystone.get_default_role(IgnoreArg()) \
                .AndReturn(self.roles.first())

        self.mox.ReplayAll()

        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': "doesntmatch"}

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(res, "form", None, ['Passwords do not match.'])

    @test.create_stubs({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_validation_for_password_too_short(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id

        api.keystone.get_default_domain(IgnoreArg()) \
            .MultipleTimes().AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain_id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=None).AndReturn(
                [self.tenants.list(), False])

        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())
        if django.VERSION >= (1, 9):
            if api.keystone.VERSIONS.active >= 3:
                api.keystone.tenant_list(
                    IgnoreArg(), domain=domain_id).AndReturn(
                    [self.tenants.list(), False])
            else:
                api.keystone.tenant_list(
                    IgnoreArg(), user=None).AndReturn(
                    [self.tenants.list(), False])

            api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
            api.keystone.get_default_role(IgnoreArg()) \
                .AndReturn(self.roles.first())

        self.mox.ReplayAll()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'four',
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': 'four'}

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_validation_for_password_too_long(self):
        user = self.users.get(id="1")
        domain = self._get_default_domain()
        domain_id = domain.id

        api.keystone.get_default_domain(IgnoreArg()) \
            .MultipleTimes().AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain_id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=None).AndReturn(
                [self.tenants.list(), False])

        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())
        if django.VERSION >= (1, 9):
            if api.keystone.VERSIONS.active >= 3:
                api.keystone.tenant_list(
                    IgnoreArg(), domain=domain_id).AndReturn(
                    [self.tenants.list(), False])
            else:
                api.keystone.tenant_list(
                    IgnoreArg(), user=None).AndReturn(
                    [self.tenants.list(), False])

            api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
            api.keystone.get_default_role(IgnoreArg()) \
                .AndReturn(self.roles.first())

        self.mox.ReplayAll()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'domain_id': domain_id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'MoreThanEighteenChars',
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': 'MoreThanEighteenChars'}

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'user_update_password',
                                       'user_update',
                                       'roles_for_user', )})
    def test_update(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest),
                                domain_id).AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain.id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=user.id).AndReturn(
                [self.tenants.list(), False])

        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=user.email,
                                 name=user.name).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'project': self.tenant.id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'user_update_password',
                                       'user_update',
                                       'roles_for_user', )})
    def test_update_default_project(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)
        new_project_id = self.tenants.get(id="3").id

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest),
                                domain_id).AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain.id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=user.id).AndReturn(
                [self.tenants.list(), False])

        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=user.email,
                                 name=user.name,
                                 project=new_project_id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'project': new_project_id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'user_update',
                                       'roles_for_user', )})
    def test_update_with_no_email_attribute(self):
        user = self.users.get(id="5")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest),
                                domain_id).AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain_id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=user.id).AndReturn(
                [self.tenants.list(), False])

        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=user.email,
                                 name=user.name,
                                 project=self.tenant.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': user.description,
                    'email': "",
                    'project': self.tenant.id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'keystone_can_edit_user',
                                       'roles_for_user', )})
    def test_update_with_keystone_can_edit_user_false(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest),
                              '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(domain)
        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain_id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=user.id).AndReturn(
                [self.tenants.list(), False])

        api.keystone.keystone_can_edit_user().AndReturn(False)
        api.keystone.keystone_can_edit_user().AndReturn(False)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'project': self.tenant.id, }

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)

    @test.create_stubs({api.keystone: ('user_get',
                                       'user_update_password')})
    def test_change_password(self):
        user = self.users.get(id="5")
        test_password = 'normalpwd'

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.user_update_password(IsA(http.HttpRequest),
                                          user.id,
                                          test_password).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': test_password,
                    'confirm_password': test_password}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('user_get',
                                       'user_verify_admin_password')})
    @override_settings(ENFORCE_PASSWORD_CHECK=True)
    def test_change_password_validation_for_admin_password(self):
        user = self.users.get(id="1")
        test_password = 'normalpwd'
        admin_password = 'secret'

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.user_verify_admin_password(
            IsA(http.HttpRequest), admin_password).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': test_password,
                    'confirm_password': test_password,
                    'admin_password': admin_password}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertFormError(res, "form", None,
                             ['The admin password is incorrect.'])

    @test.create_stubs({api.keystone: ('user_get',)})
    def test_update_validation_for_password_too_short(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)

        self.mox.ReplayAll()

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': 't',
                    'confirm_password': 't'}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('user_get',)})
    def test_update_validation_for_password_too_long(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)

        self.mox.ReplayAll()

        formData = {'method': 'ChangePasswordForm',
                    'id': user.id,
                    'name': user.name,
                    'password': 'ThisIsASuperLongPassword',
                    'confirm_password': 'ThisIsASuperLongPassword'}

        res = self.client.post(USER_CHANGE_PASSWORD_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_update_enabled',
                                       'user_list',
                                       'domain_lookup')})
    def test_enable_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        user = self.users.get(id="2")
        users = self._get_users(domain_id)
        user.enabled = False

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.user_list(IgnoreArg(), domain=domain_id).AndReturn(users)
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         True).AndReturn(user)
        api.keystone.domain_lookup(IgnoreArg()).AndReturn({domain.id:
                                                           domain.name})

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_update_enabled',
                                       'user_list',
                                       'domain_lookup')})
    def test_disable_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        user = self.users.get(id="2")
        users = self._get_users(domain_id)

        self.assertTrue(user.enabled)

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.user_list(IgnoreArg(), domain=domain_id) \
            .AndReturn(users)
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         False).AndReturn(user)
        api.keystone.domain_lookup(IgnoreArg()).AndReturn({domain.id:
                                                           domain.name})

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_update_enabled',
                                       'user_list',
                                       'domain_lookup')})
    def test_enable_disable_user_exception(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        user = self.users.get(id="2")
        users = self._get_users(domain_id)
        user.enabled = False

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.user_list(IgnoreArg(), domain=domain_id) \
            .AndReturn(users)
        api.keystone.user_update_enabled(IgnoreArg(), user.id, True) \
                    .AndRaise(self.exceptions.keystone)
        api.keystone.domain_lookup(IgnoreArg()).AndReturn({domain.id:
                                                           domain.name})
        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_list',
                                       'domain_lookup')})
    def test_disabling_current_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        users = self._get_users(domain_id)
        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg(), domain=domain_id) \
                .AndReturn(users)
            api.keystone.domain_lookup(IgnoreArg()).AndReturn({domain.id:
                                                               domain.name})

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to disable user: '
                         u'test_user')

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_list',
                                       'domain_lookup')})
    def test_disabling_current_user_domain_name(self):
        domain = self._get_default_domain()
        domains = self.domains.list()
        domain_id = domain.id
        users = self._get_users(domain_id)
        domain_lookup = dict((d.id, d.name) for d in domains)

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        for u in users:
            u.domain_name = domain_lookup.get(u.domain_id)

        for i in range(0, 2):
            api.keystone.domain_lookup(IgnoreArg()).AndReturn(domain_lookup)
            api.keystone.user_list(IgnoreArg(), domain=domain_id) \
                .AndReturn(users)

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to disable user: '
                         u'test_user')

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_list',
                                       'domain_lookup')})
    def test_delete_user_with_improper_permissions(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        users = self._get_users(domain_id)
        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg(), domain=domain_id) \
                .AndReturn(users)
            api.keystone.domain_lookup(IgnoreArg()).AndReturn({domain.id:
                                                               domain.name})

        self.mox.ReplayAll()

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to delete user: %s'
                         % self.request.user.username)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_list',
                                       'domain_lookup')})
    def test_delete_user_with_improper_permissions_domain_name(self):
        domain = self._get_default_domain()
        domains = self.domains.list()
        domain_id = domain.id
        users = self._get_users(domain_id)
        domain_lookup = dict((d.id, d.name) for d in domains)

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        for u in users:
            u.domain_name = domain_lookup.get(u.domain_id)

        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg(), domain=domain_id) \
                .AndReturn(users)
            api.keystone.domain_lookup(IgnoreArg()).AndReturn(domain_lookup)

        self.mox.ReplayAll()

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to delete user: %s'
                         % self.request.user.username)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_get')})
    def test_detail_view(self):
        domain = self._get_default_domain()
        user = self.users.get(id="1")
        tenant = self.tenants.get(id=user.project_id)

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.user_get(IsA(http.HttpRequest), '1').AndReturn(user)
        api.keystone.tenant_get(IsA(http.HttpRequest), user.project_id) \
            .AndReturn(tenant)
        self.mox.ReplayAll()

        res = self.client.get(USER_DETAIL_URL, args=[user.id])

        self.assertTemplateUsed(res, 'identity/users/detail.html')
        self.assertEqual(res.context['user'].name, user.name)
        self.assertEqual(res.context['user'].id, user.id)
        self.assertEqual(res.context['tenant_name'], tenant.name)

    @test.create_stubs({api.keystone: ('user_get',)})
    def test_detail_view_with_exception(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest), '1').\
            AndRaise(self.exceptions.keystone)
        self.mox.ReplayAll()

        res = self.client.get(USER_DETAIL_URL, args=[user.id])

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',)})
    def test_get_update_form_init_values(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest),
                                domain_id).AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(),
                                 domain=domain_id,
                                 user=user.id) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()

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

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'user_update_password',
                                       'user_update',
                                       'roles_for_user', )})
    def test_update_different_description(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest),
                                domain_id).AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=domain.id).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=user.id).AndReturn(
                [self.tenants.list(), False])

        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=user.email,
                                 name=user.name,
                                 description='changed').AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'description': 'changed',
                    'email': user.email,
                    'project': self.tenant.id}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)


class SeleniumTests(test.SeleniumAdminTestCase):
    def _get_default_domain(self):
        domain = {"id": None, "name": None}
        return api.base.APIDictWrapper(domain)

    @test.create_stubs({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'get_default_role',
                                       'role_list',
                                       'user_list',
                                       'domain_lookup')})
    def test_modal_create_user_with_passwords_not_matching(self):
        domain = self._get_default_domain()

        api.keystone.get_default_domain(IgnoreArg()) \
            .MultipleTimes().AndReturn(domain)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.tenant_list(
                IgnoreArg(), domain=None).AndReturn(
                [self.tenants.list(), False])
        else:
            api.keystone.tenant_list(
                IgnoreArg(), user=None).AndReturn(
                [self.tenants.list(), False])

        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.user_list(IgnoreArg(), domain=None) \
            .AndReturn(self.users.list())
        api.keystone.domain_lookup(IgnoreArg()).AndReturn({None: None})
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())
        self.mox.ReplayAll()

        self.selenium.get("%s%s" % (self.live_server_url, USERS_INDEX_URL))

        # Open the modal menu
        self.selenium.find_element_by_id("users__action_create") \
                     .send_keys("\n")
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

    @test.create_stubs({api.keystone: ('user_get',)})
    def test_update_user_with_passwords_not_matching(self):
        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(self.user)
        self.mox.ReplayAll()

        self.selenium.get("%s%s" % (self.live_server_url,
                                    USER_CHANGE_PASSWORD_URL))

        self.assertFalse(self._is_element_present("id_confirm_password_error"),
                         "Password error element shouldn't yet exist.")
        self.selenium.find_element_by_id("id_password").send_keys("test")
        self.selenium.find_element_by_id("id_confirm_password").send_keys("te")
        self.selenium.find_element_by_id("id_name").click()
        self.assertTrue(self._is_element_present("id_confirm_password_error"),
                        "Couldn't find password error element.")

    def _is_element_present(self, element_id):
        try:
            self.selenium.find_element_by_id(element_id)
            return True
        except Exception:
            return False
