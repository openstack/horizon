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

from openstack_dashboard.dashboards.identity.groups import constants


GROUPS_INDEX_URL = reverse(constants.GROUPS_INDEX_URL)
GROUP_CREATE_URL = reverse(constants.GROUPS_CREATE_URL)
GROUP_UPDATE_URL = reverse(constants.GROUPS_UPDATE_URL, args=[1])
GROUP_MANAGE_URL = reverse(constants.GROUPS_MANAGE_URL, args=[1])
GROUP_ADD_MEMBER_URL = reverse(constants.GROUPS_ADD_MEMBER_URL, args=[1])


class GroupsViewTests(test.BaseAdminViewTests):

    def _get_domain_id(self):
        return self.request.session.get('domain_context', None)

    def _get_groups(self, domain_id):
        if not domain_id:
            groups = self.groups.list()
        else:
            groups = [group for group in self.groups.list()
                      if group.domain_id == domain_id]
        return groups

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'group_list',)})
    def test_index(self):
        domain_id = self._get_domain_id()
        groups = self._get_groups(domain_id)
        filters = {}

        self.mock_get_effective_domain_id.return_value = None
        self.mock_group_list.return_value = groups

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, groups)
        if domain_id:
            for group in res.context['table'].data:
                self.assertItemsEqual(group.domain_id, domain_id)

        self.assertContains(res, 'Create Group')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Group')

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id,
                                                     filters=filters)

    @test.create_mocks({api.keystone: ('group_list',)})
    def test_index_with_domain(self):
        domain = self.domains.get(id="1")
        filters = {}
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        groups = self._get_groups(domain.id)

        self.mock_group_list.return_value = groups

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, groups)
        if domain.id:
            for group in res.context['table'].data:
                self.assertItemsEqual(group.domain_id, domain.id)

        self.assertContains(res, 'Create Group')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Group')

        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain.id,
                                                     filters=filters)

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'group_list',
                                       'keystone_can_edit_group')})
    def test_index_with_keystone_can_edit_group_false(self):
        domain_id = self._get_domain_id()
        groups = self._get_groups(domain_id)
        filters = {}
        self.mock_get_effective_domain_id.return_value = domain_id
        self.mock_group_list.return_value = groups
        self.mock_keystone_can_edit_group.return_value = False

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, groups)

        self.assertNotContains(res, 'Create Group')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Group')

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_list.assert_called_once_with(
            test.IsHttpRequest(),
            domain=domain_id,
            filters=filters)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_keystone_can_edit_group, 19, mock.call())

    @test.create_mocks({api.keystone: ('group_create',
                                       'get_effective_domain_id')})
    def test_create(self):
        domain_id = self._get_domain_id()
        group = self.groups.get(id="1")

        self.mock_get_effective_domain_id.return_value = None
        self.mock_group_create.return_value = group

        formData = {'method': 'CreateGroupForm',
                    'name': group.name,
                    'description': group.description}
        res = self.client.post(GROUP_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_create.assert_called_once_with(
            test.IsHttpRequest(),
            description=group.description,
            domain_id=domain_id,
            name=group.name)

    @test.create_mocks({api.keystone: ('group_create',)})
    def test_create_with_domain(self):
        domain = self.domains.get(id="3")
        group = self.groups.get(id="1")

        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)

        self.mock_group_create.return_value = group

        formData = {'method': 'CreateGroupForm',
                    'name': group.name,
                    'description': group.description}
        res = self.client.post(GROUP_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_group_create.assert_called_once_with(
            test.IsHttpRequest(),
            description=group.description,
            domain_id=domain.id,
            name=group.name)

    @test.create_mocks({api.keystone: ('group_get',
                                       'group_update')})
    def test_update(self):
        group = self.groups.get(id="1")
        test_description = 'updated description'

        self.mock_group_get.return_value = group
        self.mock_group_update.return_value = None

        formData = {'method': 'UpdateGroupForm',
                    'group_id': group.id,
                    'name': group.name,
                    'description': test_description}

        res = self.client.post(GROUP_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.mock_group_update.assert_called_once_with(
            test.IsHttpRequest(),
            description=test_description,
            group_id=group.id,
            name=group.name)

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'group_list',
                                       'group_delete')})
    def test_delete_group(self):
        domain_id = self._get_domain_id()
        filters = {}
        group = self.groups.get(id="2")

        self.mock_get_effective_domain_id.return_value = domain_id
        self.mock_group_list.return_value = self.groups.list()
        self.mock_group_delete.return_value = None

        formData = {'action': 'groups__delete__%s' % group.id}
        res = self.client.post(GROUPS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, GROUPS_INDEX_URL)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id,
                                                     filters=filters)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id)

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'group_get',
                                       'user_list',)})
    def test_manage(self):
        group = self.groups.get(id="1")
        group_members = self.users.list()
        domain_id = self._get_domain_id()

        self.mock_group_get.return_value = group
        self.mock_get_effective_domain_id.return_value = domain_id
        self.mock_user_list.return_value = group_members

        res = self.client.get(GROUP_MANAGE_URL)

        self.assertTemplateUsed(res, constants.GROUPS_MANAGE_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, group_members)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        if api.keystone.VERSIONS.active >= 3:
            self.mock_get_effective_domain_id.assert_called_once_with(
                test.IsHttpRequest())
            self.mock_user_list.assert_called_once_with(
                test.IsHttpRequest(), group=group.id, domain=domain_id)
        else:
            self.mock_get_effective_domain_id.assert_not_called()
            self.mock_user_list.assert_called_once_with(
                test.IsHttpRequest(), group=group.id)

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'user_list',
                                       'remove_group_user')})
    def test_remove_user(self):
        group = self.groups.get(id="1")
        user = self.users.get(id="2")
        domain_id = self._get_domain_id()

        self.mock_get_effective_domain_id.return_value = domain_id
        self.mock_user_list.return_value = self.users.list()
        self.mock_remove_group_user.return_value = None

        formData = {'action': 'group_members__removeGroupMember__%s' % user.id}
        res = self.client.post(GROUP_MANAGE_URL, formData)

        self.assertRedirectsNoFollow(res, GROUP_MANAGE_URL)
        self.assertMessageCount(success=1)

        if api.keystone.VERSIONS.active >= 3:
            self.mock_get_effective_domain_id.assert_called_once_with(
                test.IsHttpRequest())
            self.mock_user_list.assert_called_once_with(
                test.IsHttpRequest(), group=group.id, domain=domain_id)
        else:
            self.mock_get_effective_domain_id.assert_not_called()
            self.mock_user_list.assert_called_once_with(
                test.IsHttpRequest(), group=group.id)

        self.mock_remove_group_user.assert_called_once_with(
            test.IsHttpRequest(),
            group_id=group.id,
            user_id=user.id)

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'group_get',
                                       'user_list',
                                       'add_group_user')})
    def test_add_user(self):
        group = self.groups.get(id="1")
        user = self.users.get(id="2")
        domain_id = group.domain_id

        self.mock_get_effective_domain_id.return_value = domain_id
        self.mock_group_get.return_value = group
        self.mock_user_list.side_effect = [
            self.users.list(),
            self.users.list()[2:],
        ]
        self.mock_add_group_user.return_value = None

        formData = {'action': 'group_non_members__add__%s' % user.id}
        res = self.client.post(GROUP_ADD_MEMBER_URL, formData)

        self.assertRedirectsNoFollow(res, GROUP_MANAGE_URL)
        self.assertMessageCount(success=1)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_user_list.assert_has_calls([
            mock.call(test.IsHttpRequest(), domain=domain_id),
            mock.call(test.IsHttpRequest(), domain=domain_id, group=group.id),
        ])
        self.mock_add_group_user.assert_called_once_with(test.IsHttpRequest(),
                                                         group_id=group.id,
                                                         user_id=user.id)

    @test.update_settings(FILTER_DATA_FIRST={'identity.groups': True})
    def test_index_with_filter_first(self):
        res = self.client.get(GROUPS_INDEX_URL)
        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        groups = res.context['table'].data
        self.assertItemsEqual(groups, [])
