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

from django.urls import reverse

import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


ROLES_INDEX_URL = reverse('horizon:identity:roles:index')
ROLES_CREATE_URL = reverse('horizon:identity:roles:create')
ROLES_UPDATE_URL = reverse('horizon:identity:roles:update', args=[1])
INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class RolesViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.keystone: ('role_list',)})
    def test_index(self):
        filters = {}

        self.mock_role_list.return_value = self.roles.list()

        res = self.client.get(ROLES_INDEX_URL)
        self.assertContains(res, 'Create Role')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Role')

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.roles.list())

        self.mock_role_list.assert_called_once_with(test.IsHttpRequest(),
                                                    filters=filters)

    @test.create_mocks({api.keystone: ('role_list',
                                       'keystone_can_edit_role', )})
    def test_index_with_keystone_can_edit_role_false(self):
        filters = {}

        self.mock_role_list.return_value = self.roles.list()
        self.mock_keystone_can_edit_role.return_value = False

        res = self.client.get(ROLES_INDEX_URL)

        self.assertNotContains(res, 'Create Role')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Role')

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.roles.list())

        self.mock_role_list.assert_called_once_with(test.IsHttpRequest(),
                                                    filters=filters)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_keystone_can_edit_role, 8, mock.call())

    @test.create_mocks({api.keystone: ('role_create', )})
    def test_create(self):
        role = self.roles.first()

        self.mock_role_create.return_value = role

        formData = {'method': 'CreateRoleForm', 'name': role.name}
        res = self.client.post(ROLES_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_role_create.assert_called_once_with(test.IsHttpRequest(),
                                                      role.name)

    @test.create_mocks({api.keystone: ('role_get', 'role_update')})
    def test_update(self):
        role = self.roles.first()
        new_role_name = 'test_name'

        self.mock_role_get.return_value = role
        self.mock_role_update.return_value = None

        formData = {'method': 'UpdateRoleForm',
                    'id': role.id,
                    'name': new_role_name}

        res = self.client.post(ROLES_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_role_get.assert_called_once_with(test.IsHttpRequest(),
                                                   role.id)
        self.mock_role_update.assert_called_once_with(test.IsHttpRequest(),
                                                      role.id,
                                                      new_role_name)

    @test.create_mocks({api.keystone: ('role_list', 'role_delete')})
    def test_delete(self):
        role = self.roles.first()
        filters = {}

        self.mock_role_list.return_value = self.roles.list()
        self.mock_role_delete.return_value = None

        formData = {'action': 'roles__delete__%s' % role.id}
        res = self.client.post(ROLES_INDEX_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_role_list.assert_called_once_with(test.IsHttpRequest(),
                                                    filters=filters)
        self.mock_role_delete.assert_called_once_with(test.IsHttpRequest(),
                                                      role.id)

    @test.update_settings(FILTER_DATA_FIRST={'identity.roles': True})
    def test_index_with_filter_first(self):
        res = self.client.get(ROLES_INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        roles = res.context['table'].data
        self.assertItemsEqual(roles, [])
