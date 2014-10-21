# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from django import http

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


ROLES_INDEX_URL = reverse('horizon:identity:roles:index')
ROLES_CREATE_URL = reverse('horizon:identity:roles:create')
ROLES_UPDATE_URL = reverse('horizon:identity:roles:update', args=[1])


class RolesViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('role_list',)})
    def test_index(self):
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())

        self.mox.ReplayAll()

        res = self.client.get(ROLES_INDEX_URL)
        self.assertContains(res, 'Create Role')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Role')

        self.assertTemplateUsed(res, 'identity/roles/index.html')
        self.assertItemsEqual(res.context['table'].data, self.roles.list())

    @test.create_stubs({api.keystone: ('role_list',
                                       'keystone_can_edit_role', )})
    def test_index_with_keystone_can_edit_role_false(self):
        api.keystone.role_list(IgnoreArg()).AndReturn(self.roles.list())
        api.keystone.keystone_can_edit_role() \
            .MultipleTimes().AndReturn(False)
        self.mox.ReplayAll()

        res = self.client.get(ROLES_INDEX_URL)

        self.assertNotContains(res, 'Create Role')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Role')

        self.assertTemplateUsed(res, 'identity/roles/index.html')
        self.assertItemsEqual(res.context['table'].data, self.roles.list())

    @test.create_stubs({api.keystone: ('role_create', )})
    def test_create(self):
        role = self.roles.first()

        api.keystone.role_create(IgnoreArg(), role.name).AndReturn(role)

        self.mox.ReplayAll()

        formData = {'method': 'CreateRoleForm', 'name': role.name}
        res = self.client.post(ROLES_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('role_get', 'role_update')})
    def test_update(self):
        role = self.roles.first()
        new_role_name = 'test_name'

        api.keystone.role_get(IsA(http.HttpRequest), role.id).AndReturn(role)
        api.keystone.role_update(IsA(http.HttpRequest),
                                 role.id,
                                 new_role_name).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateRoleForm',
                    'id': role.id,
                    'name': new_role_name}

        res = self.client.post(ROLES_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('role_list', 'role_delete')})
    def test_delete(self):
        role = self.roles.first()

        api.keystone.role_list(IsA(http.HttpRequest)) \
            .AndReturn(self.roles.list())
        api.keystone.role_delete(IsA(http.HttpRequest),
                                 role.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'action': 'roles__delete__%s' % role.id}
        res = self.client.post(ROLES_INDEX_URL, formData)

        self.assertNoFormErrors(res)
