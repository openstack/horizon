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

from django.core.urlresolvers import reverse
from mox import IgnoreArg
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import test


USERS_INDEX_URL = reverse('horizon:syspanel:users:index')


class UsersViewTests(test.BaseAdminViewTests):
    def setUp(self):
        super(UsersViewTests, self).setUp()

        self.user = api.User(None)
        self.user.enabled = True
        self.user.id = self.TEST_USER_ID
        self.user.name = self.TEST_USER
        self.user.roles = self.TEST_ROLES
        self.user.tenantId = self.TEST_TENANT

        self.users = [self.user]

    def test_index(self):
        self.mox.StubOutWithMock(api, 'user_list')
        api.user_list(IgnoreArg()).AndReturn(self.users)

        self.mox.ReplayAll()

        res = self.client.get(USERS_INDEX_URL)

        self.assertTemplateUsed(res, 'syspanel/users/index.html')
        self.assertItemsEqual(res.context['table'].data, self.users)

    def test_enable_user(self):
        formData = {'action': 'users__enable__%s' % self.user.id}

        self.mox.StubOutWithMock(api.keystone, 'user_update_enabled')
        api.keystone.user_update_enabled(IgnoreArg(), self.user.id, True) \
                    .AndReturn(self.mox.CreateMock(api.User))

        self.mox.ReplayAll()

        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirects(res, USERS_INDEX_URL)

    def test_disable_user(self):
        OTHER_USER_ID = '5'
        formData = {'action': 'users__disable__%s' % OTHER_USER_ID}

        self.mox.StubOutWithMock(api.keystone, 'user_update_enabled')
        api.keystone.user_update_enabled(IgnoreArg(), OTHER_USER_ID, False) \
                    .AndReturn(self.mox.CreateMock(api.User))

        self.mox.ReplayAll()

        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirects(res, USERS_INDEX_URL)

    def test_enable_disable_user_exception(self):
        OTHER_USER_ID = '5'
        formData = {'action': 'users__enable__%s' % OTHER_USER_ID}

        self.mox.StubOutWithMock(api.keystone, 'user_update_enabled')
        api_exception = api_exceptions.ApiException('apiException',
                                                    message='apiException')
        api.keystone.user_update_enabled(IgnoreArg(), OTHER_USER_ID, True) \
                    .AndRaise(api_exception)

        self.mox.ReplayAll()

        res = self.client.post(USERS_INDEX_URL, formData)

        self.assertRedirects(res, USERS_INDEX_URL)

    def test_shoot_yourself_in_the_foot(self):
        self.mox.StubOutWithMock(api, 'user_list')
        # Four times... one for each post and one for each followed redirect
        api.user_list(IgnoreArg()).AndReturn(self.users)
        api.user_list(IgnoreArg()).AndReturn(self.users)
        api.user_list(IgnoreArg()).AndReturn(self.users)
        api.user_list(IgnoreArg()).AndReturn(self.users)

        self.mox.ReplayAll()

        formData = {'action': 'users__disable__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You cannot disable the user you are currently '
                         u'logged in as.')

        formData = {'action': 'users__delete__%s' % self.request.user.id}
        res = self.client.post(USERS_INDEX_URL, formData, follow=True)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'You do not have permission to delete user: test')
