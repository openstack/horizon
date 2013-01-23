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

from socket import timeout as socket_timeout

from django import http
from django.core.urlresolvers import reverse

from mox import IgnoreArg, IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


USERS_INDEX_URL = reverse('horizon:admin:users:index')
USER_CREATE_URL = reverse('horizon:admin:users:create')
USER_UPDATE_URL = reverse('horizon:admin:users:update', args=[1])


class UsersViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('user_list',)})
    def test_index(self):
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())

        self.mox.ReplayAll()

        res = self.client.get(USERS_INDEX_URL)

        self.assertTemplateUsed(res, 'admin/users/index.html')
        self.assertItemsEqual(res.context['table'].data, self.users.list())

    @test.create_stubs({api.keystone: ('user_create',
                                       'tenant_list',
                                       'add_tenant_user_role',
                                       'get_default_role',
                                       'role_list')})
    def test_create(self):
        user = self.users.get(id="1")
        role = self.roles.first()

        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        api.keystone.user_create(IgnoreArg(),
                                 user.name,
                                 user.email,
                                 user.password,
                                 self.tenant.id,
                                 True).AndReturn(user)
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()).AndReturn(role)
        api.keystone.add_tenant_user_role(IgnoreArg(), self.tenant.id,
                                          user.id, role.id)

        self.mox.ReplayAll()

        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'tenant_id': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': user.password}
        res = self.client.post(USER_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_with_password_mismatch(self):
        user = self.users.get(id="1")

        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())

        self.mox.ReplayAll()

        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'tenant_id': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': "doesntmatch"}

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(res, "form", None, ['Passwords do not match.'])

    @test.create_stubs({api.keystone: ('tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_validation_for_password_too_short(self):
        user = self.users.get(id="1")

        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())

        self.mox.ReplayAll()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': 'four',
                    'tenant_id': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': 'four'}

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('tenant_list',
                                       'role_list',
                                       'get_default_role')})
    def test_create_validation_for_password_too_long(self):
        user = self.users.get(id="1")

        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.get_default_role(IgnoreArg()) \
                    .AndReturn(self.roles.first())

        self.mox.ReplayAll()

        # check password min-len verification
        formData = {'method': 'CreateUserForm',
                    'name': user.name,
                    'email': user.email,
                    'password': 'MoreThanEighteenChars',
                    'tenant_id': self.tenant.id,
                    'role_id': self.roles.first().id,
                    'confirm_password': 'MoreThanEighteenChars'}

        res = self.client.post(USER_CREATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('user_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'user_update_password',
                                       'user_update',
                                       'roles_for_user', )})
    def test_update(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                     admin=True).AndReturn(user)
        api.keystone.tenant_list(IgnoreArg(),
                        admin=True).AndReturn(self.tenants.list())
        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=u'test@example.com',
                                 name=u'test_user').AndReturn(None)
        api.keystone.user_update_tenant(IsA(http.HttpRequest),
                               user.id,
                               self.tenant.id).AndReturn(None)
        api.keystone.roles_for_user(IsA(http.HttpRequest),
                                    user.id,
                                    self.tenant.id).AndReturn(None)
        api.keystone.user_update_password(IsA(http.HttpRequest),
                                          user.id,
                                          IgnoreArg()).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'normalpwd',
                    'tenant_id': self.tenant.id,
                    'confirm_password': 'normalpwd'}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(warning=1)

    @test.create_stubs({api.keystone: ('user_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'keystone_can_edit_user',
                                       'roles_for_user', )})
    def test_update_with_keystone_can_edit_user_false(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest),
                     '1',
                     admin=True).AndReturn(user)
        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        api.keystone.keystone_can_edit_user().AndReturn(False)
        api.keystone.keystone_can_edit_user().AndReturn(False)
        api.keystone.user_update_tenant(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(None)
        api.keystone.roles_for_user(IsA(http.HttpRequest),
                                    user.id,
                                    self.tenant.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'tenant_id': self.tenant.id, }

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(warning=1)

    @test.create_stubs({api.keystone: ('user_get', 'tenant_list')})
    def test_update_validation_for_password_too_short(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.tenant_list(IgnoreArg(),
                                 admin=True).AndReturn(self.tenants.list())

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'password': 't',
                    'tenant_id': self.tenant.id,
                    'confirm_password': 't'}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertFormError(
                res, "form", 'password',
                ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('user_get', 'tenant_list')})
    def test_update_validation_for_password_too_long(self):
        user = self.users.get(id="1")

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.tenant_list(IgnoreArg(),
                                 admin=True).AndReturn(self.tenants.list())

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'ThisIsASuperLongPassword',
                    'tenant_id': self.tenant.id,
                    'confirm_password': 'ThisIsASuperLongPassword'}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertFormError(
                res, "form", 'password',
                ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('user_update_enabled', 'user_list')})
    def test_enable_user(self):
        user = self.users.get(id="2")
        user.enabled = False
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         True).AndReturn(user)

        self.mox.ReplayAll()

        formData = {'action': 'users__enable__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_update_enabled', 'user_list')})
    def test_disable_user(self):
        user = self.users.get(id="2")
        self.assertTrue(user.enabled)

        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         False).AndReturn(user)

        self.mox.ReplayAll()

        formData = {'action': 'users__enable__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_update_enabled', 'user_list')})
    def test_enable_disable_user_exception(self):
        user = self.users.get(id="2")
        user.enabled = False
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
        api.keystone.user_update_enabled(IgnoreArg(), user.id, True) \
                    .AndRaise(self.exceptions.keystone)
        self.mox.ReplayAll()

        formData = {'action': 'users__enable__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_list',)})
    def test_disabling_current_user(self):
        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())

        self.mox.ReplayAll()

        formData = {'action': 'users__enable__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You cannot disable the user you are currently '
                         u'logged in as.')

    @test.create_stubs({api.keystone: ('user_list',)})
    def test_delete_user_with_improper_permissions(self):
        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())

        self.mox.ReplayAll()

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You do not have permission to delete user: %s'
                         % self.request.user.username)


class SeleniumTests(test.SeleniumAdminTestCase):
    @test.create_stubs({api.keystone: ('tenant_list',
                                       'get_default_role',
                                       'role_list',
                                       'user_list')})
    def test_modal_create_user_with_passwords_not_matching(self):
        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.user_list(IgnoreArg()).AndReturn(self.users.list())
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

        body = self.selenium.find_element_by_tag_name("body")
        self.assertFalse("Passwords do not match" in body.text,
                         "Error message should not be visible at loading time")
        self.selenium.find_element_by_id("id_name").send_keys("Test User")
        self.selenium.find_element_by_id("id_password").send_keys("test")
        self.selenium.find_element_by_id("id_confirm_password").send_keys("te")
        self.selenium.find_element_by_id("id_email").send_keys("a@b.com")
        body = self.selenium.find_element_by_tag_name("body")
        self.assertTrue("Passwords do not match" in body.text,
                        "Error message not found in body")

    @test.create_stubs({api.keystone: ('tenant_list', 'user_get')})
    def test_update_user_with_passwords_not_matching(self):
        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(self.user)
        api.keystone.tenant_list(IgnoreArg(), admin=True) \
            .AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        self.selenium.get("%s%s" % (self.live_server_url, USER_UPDATE_URL))

        body = self.selenium.find_element_by_tag_name("body")
        self.assertFalse("Passwords do not match" in body.text,
                         "Error message should not be visible at loading time")
        self.selenium.find_element_by_id("id_password").send_keys("test")
        self.selenium.find_element_by_id("id_confirm_password").send_keys("te")
        self.selenium.find_element_by_id("id_email").clear()
        body = self.selenium.find_element_by_tag_name("body")
        self.assertTrue("Passwords do not match" in body.text,
                        "Error message not found in body")
