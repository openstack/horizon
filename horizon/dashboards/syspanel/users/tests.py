# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import http
from django.core.urlresolvers import reverse
from keystoneclient import exceptions as keystone_exceptions
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test


USERS_INDEX_URL = reverse('horizon:syspanel:users:index')
USER_CREATE_URL = reverse('horizon:syspanel:users:create')
USER_UPDATE_URL = reverse('horizon:syspanel:users:update', args=[1])


class UsersViewTests(test.BaseAdminViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(api.keystone, 'user_list')
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        self.mox.ReplayAll()

        res = self.client.get(USERS_INDEX_URL)
        self.assertTemplateUsed(res, 'syspanel/users/index.html')
        self.assertItemsEqual(res.context['table'].data, self.users.list())

    def test_create_user(self):
        user = self.users.get(id="1")
        role = self.roles.first()
        self.mox.StubOutWithMock(api, 'user_create')
        self.mox.StubOutWithMock(api, 'tenant_list')
        self.mox.StubOutWithMock(api.keystone, 'get_default_role')
        self.mox.StubOutWithMock(api, 'add_tenant_user_role')
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        api.user_create(IgnoreArg(),
                        user.name,
                        user.email,
                        user.password,
                        self.tenant.id,
                        True).AndReturn(user)
        api.keystone.get_default_role(IgnoreArg()).AndReturn(role)
        api.add_tenant_user_role(IgnoreArg(), self.tenant.id, user.id, role.id)
        self.mox.ReplayAll()

        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'tenant_id': self.tenant.id,
                    'confirm_password': user.password}
        res = self.client.post(USER_CREATE_URL, formData)
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    def test_create_user_password_mismatch(self):
        user = self.users.get(id="1")
        self.mox.StubOutWithMock(api, 'tenant_list')
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'tenant_id': self.tenant.id,
                    'confirm_password': "doesntmatch"}

        res = self.client.post(USER_CREATE_URL, formData)
        self.assertFormError(res, "form", None, ['Passwords do not match.'])

    def test_create_user_field_validation(self):
        user = self.users.get(id="1")
        self.mox.StubOutWithMock(api, 'tenant_list')
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': 'four',
                    'tenant_id': self.tenant.id,
                    'confirm_password': 'four'}

        res = self.client.post(USER_CREATE_URL, formData)
        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

        # check password max-len verification
        formData['password'] = 'MoreThanEighteenChars'
        formData['confirm_password'] = 'MoreThanEighteenChars'

        res = self.client.post(USER_CREATE_URL, formData)
        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    def test_update_user_field_validation(self):
        user = self.users.get(id="1")
        self.mox.StubOutWithMock(api, 'tenant_list')
        self.mox.StubOutWithMock(api, 'user_get')
        self.mox.StubOutWithMock(api.keystone, 'user_update')
        self.mox.StubOutWithMock(api, 'user_update_tenant')
        self.mox.StubOutWithMock(api, 'user_update_password')

        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=u'test@example.com',
                                 name=u'test_user').AndReturn(None)
        api.user_update_tenant(IsA(http.HttpRequest),
                               user.id,
                               self.tenant.id).AndReturn(None)
        api.user_update_password(IsA(http.HttpRequest),
                               user.id,
                               IgnoreArg()).AndReturn(None)
        api.user_get(IsA(http.HttpRequest), '1', admin=True).AndReturn(user)
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        api.user_get(IsA(http.HttpRequest), '1', admin=True).AndReturn(user)
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        api.user_get(IsA(http.HttpRequest), '1', admin=True).AndReturn(user)
        api.tenant_list(IgnoreArg(), admin=True).AndReturn(self.tenants.list())
        self.mox.ReplayAll()
        user.tenantId = 1

        formData = {'method': 'UpdateUserForm',
                    'id': 1,
                    'name': user.name,
                    'email': user.email,
                    'password': 'normalpwd',
                    'tenant_id': self.tenant.id,
                    'confirm_password': 'normalpwd'}

        # check successful update
        res = self.client.post(USER_UPDATE_URL, formData)
        self.assertNoFormErrors(res)

        # check password min-len verification
        formData['password'] = 'four'
        formData['confirm_password'] = 'four'

        res = self.client.post(USER_UPDATE_URL, formData)
        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

        # check password max-len verification
        formData['password'] = 'MoreThanEighteenChars'
        formData['confirm_password'] = 'MoreThanEighteenChars'

        res = self.client.post(USER_UPDATE_URL, formData)
        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    def test_enable_user(self):
        user = self.users.get(id="2")
        self.mox.StubOutWithMock(api.keystone, 'user_update_enabled')
        self.mox.StubOutWithMock(api.keystone, 'user_list')
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         True).AndReturn(user)
        self.mox.ReplayAll()

        formData = {'action': 'users__enable__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    def test_disable_user(self):
        user = self.users.get(id="2")

        self.mox.StubOutWithMock(api.keystone, 'user_update_enabled')
        self.mox.StubOutWithMock(api.keystone, 'user_list')
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         False).AndReturn(user)
        self.mox.ReplayAll()

        formData = {'action': 'users__disable__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    def test_enable_disable_user_exception(self):
        user = self.users.get(id="2")
        self.mox.StubOutWithMock(api.keystone, 'user_update_enabled')
        self.mox.StubOutWithMock(api.keystone, 'user_list')
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api_exception = keystone_exceptions.ClientException('apiException',
                                                    message='apiException')
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         True).AndRaise(api_exception)
        self.mox.ReplayAll()

        formData = {'action': 'users__enable__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    def test_shoot_yourself_in_the_foot(self):
        self.mox.StubOutWithMock(api.keystone, 'user_list')
        # Four times... one for each post and one for each followed redirect
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())

        self.mox.ReplayAll()

        formData = {'action': 'users__disable__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You cannot disable the user you are currently '
                         u'logged in as.')

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You do not have permission to delete user: %s'
                         % self.request.user.username)
