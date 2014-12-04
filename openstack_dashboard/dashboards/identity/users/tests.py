# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mox import IgnoreArg
from mox import IsA  # noqa

from django import http
from django.contrib import auth as django_auth
from django.core.urlresolvers import reverse

from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


USERS_INDEX_URL = reverse('horizon:identity:users:index')
USER_CREATE_URL = reverse('horizon:identity:users:create')
USER_UPDATE_URL = reverse('horizon:identity:users:update', args=[1])


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

    @test.create_stubs({api.keystone: ('user_list',)})
    def test_index(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        users = self._get_users(domain_id)
        api.keystone.user_list(IgnoreArg(),
                               domain=domain_id).AndReturn(users)

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
            .MultipleTimes().AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(),
                                 domain=domain_id,
                                 user=None) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_create(IgnoreArg(),
                                 name=user.name,
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
                    'email': user.email,
                    'password': user.password,
                    'project': self.tenant.id,
                    'role_id': self.roles.first().id,
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
            .MultipleTimes().AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(),
                                 domain=domain_id,
                                 user=None) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_create(IgnoreArg(),
                                 name=user.name,
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
                    'email': "",
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
        api.keystone.tenant_list(IgnoreArg(), domain=domain_id, user=None) \
            .AndReturn([self.tenants.list(), False])
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
        api.keystone.tenant_list(IgnoreArg(), domain=domain_id, user=None) \
            .AndReturn([self.tenants.list(), False])
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
        api.keystone.tenant_list(IgnoreArg(), domain=domain_id, user=None) \
            .AndReturn([self.tenants.list(), False])
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
    def _update(self, user):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)
        test_password = 'normalpwd'
        email = getattr(user, 'email', '')

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest),
                                domain_id).AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(),
                                 domain=domain_id,
                                 user=user.id) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=email,
                                 name=u'test_user',
                                 password=test_password,
                                 project=self.tenant.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': email,
                    'password': test_password,
                    'project': self.tenant.id,
                    'confirm_password': test_password}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('user_get',
                                       'domain_get',
                                       'tenant_list',
                                       'user_update_tenant',
                                       'user_update_password',
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
        api.keystone.tenant_list(IgnoreArg(),
                                 domain=domain_id,
                                 user=user.id) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.user_update(IsA(http.HttpRequest),
                                 user.id,
                                 email=user.email,
                                 name=user.name,
                                 password=user.password,
                                 project=self.tenant.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': "",
                    'password': user.password,
                    'project': self.tenant.id,
                    'confirm_password': user.password}

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
        api.keystone.tenant_list(IgnoreArg(), domain=domain_id, user=user.id) \
            .AndReturn([self.tenants.list(), False])
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

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_list')})
    def test_update_validation_for_password_too_short(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(), domain=domain_id, user=user.id) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'password': 't',
                    'project': self.tenant.id,
                    'confirm_password': 't'}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('domain_get',
                                       'user_get',
                                       'tenant_list')})
    def test_update_validation_for_password_too_long(self):
        user = self.users.get(id="1")
        domain_id = user.domain_id
        domain = self.domains.get(id=domain_id)

        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(user)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(), domain=domain_id, user=user.id) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()

        formData = {'method': 'UpdateUserForm',
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'password': 'ThisIsASuperLongPassword',
                    'project': self.tenant.id,
                    'confirm_password': 'ThisIsASuperLongPassword'}

        res = self.client.post(USER_UPDATE_URL, formData)

        self.assertFormError(
            res, "form", 'password',
            ['Password must be between 8 and 18 characters.'])

    @test.create_stubs({api.keystone: ('user_update_enabled', 'user_list')})
    def test_enable_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        user = self.users.get(id="2")
        users = self._get_users(domain_id)
        user.enabled = False

        api.keystone.user_list(IgnoreArg(), domain=domain_id).AndReturn(users)
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         True).AndReturn(user)

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_update_enabled', 'user_list')})
    def test_disable_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        user = self.users.get(id="2")
        users = self._get_users(domain_id)

        self.assertTrue(user.enabled)

        api.keystone.user_list(IgnoreArg(), domain=domain_id) \
            .AndReturn(users)
        api.keystone.user_update_enabled(IgnoreArg(),
                                         user.id,
                                         False).AndReturn(user)

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_update_enabled', 'user_list')})
    def test_enable_disable_user_exception(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        user = self.users.get(id="2")
        users = self._get_users(domain_id)
        user.enabled = False

        api.keystone.user_list(IgnoreArg(), domain=domain_id) \
            .AndReturn(users)
        api.keystone.user_update_enabled(IgnoreArg(), user.id, True) \
                    .AndRaise(self.exceptions.keystone)
        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % user.id}
        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, USERS_INDEX_URL)

    @test.create_stubs({api.keystone: ('user_list',)})
    def test_disabling_current_user(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        users = self._get_users(domain_id)
        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg(), domain=domain_id) \
                .AndReturn(users)

        self.mox.ReplayAll()

        formData = {'action': 'users__toggle__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You cannot disable the user you are currently '
                         u'logged in as.')

    @test.create_stubs({api.keystone: ('user_list',)})
    def test_delete_user_with_improper_permissions(self):
        domain = self._get_default_domain()
        domain_id = domain.id
        users = self._get_users(domain_id)
        for i in range(0, 2):
            api.keystone.user_list(IgnoreArg(), domain=domain_id) \
                .AndReturn(users)

        self.mox.ReplayAll()

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)

        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You are not allowed to delete user: %s'
                         % self.request.user.username)


class SeleniumTests(test.SeleniumAdminTestCase):
    def _get_default_domain(self):
        domain = {"id": None, "name": None}
        return api.base.APIDictWrapper(domain)

    @test.create_stubs({api.keystone: ('get_default_domain',
                                       'tenant_list',
                                       'get_default_role',
                                       'role_list',
                                       'user_list')})
    def test_modal_create_user_with_passwords_not_matching(self):
        domain = self._get_default_domain()

        api.keystone.get_default_domain(IgnoreArg()) \
            .AndReturn(domain)
        api.keystone.tenant_list(IgnoreArg(), domain=None, user=None) \
            .AndReturn([self.tenants.list(), False])
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.user_list(IgnoreArg(), domain=None) \
            .AndReturn(self.users.list())
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

    @test.create_stubs({api.keystone: ('tenant_list',
                                       'user_get',
                                       'domain_get')})
    def test_update_user_with_passwords_not_matching(self):
        api.keystone.user_get(IsA(http.HttpRequest), '1',
                              admin=True).AndReturn(self.user)
        api.keystone.domain_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.domain)
        api.keystone.tenant_list(IgnoreArg(),
                                 domain=self.user.domain_id,
                                 user=self.user.id) \
            .AndReturn([self.tenants.list(), False])
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
