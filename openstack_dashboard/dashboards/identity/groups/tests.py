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

from mox3.mox import IgnoreArg
from mox3.mox import IsA

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

    @test.create_stubs({api.keystone: ('domain_get',
                                       'group_list',)})
    def test_index(self):
        domain_id = self._get_domain_id()
        groups = self._get_groups(domain_id)
        filters = {}
        api.keystone.group_list(IgnoreArg(),
                                domain=domain_id,
                                filters=filters) \
            .AndReturn(groups)

        self.mox.ReplayAll()

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, groups)
        if domain_id:
            for group in res.context['table'].data:
                self.assertItemsEqual(group.domain_id, domain_id)

        self.assertContains(res, 'Create Group')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Group')

    @test.create_stubs({api.keystone: ('group_list',
                                       'get_effective_domain_id')})
    def test_index_with_domain(self):
        domain = self.domains.get(id="1")
        filters = {}
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        groups = self._get_groups(domain.id)

        api.keystone.group_list(IsA(http.HttpRequest),
                                domain=domain.id,
                                filters=filters).AndReturn(groups)

        self.mox.ReplayAll()

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, groups)
        if domain.id:
            for group in res.context['table'].data:
                self.assertItemsEqual(group.domain_id, domain.id)

        self.assertContains(res, 'Create Group')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Group')

    @test.create_stubs({api.keystone: ('domain_get',
                                       'group_list',
                                       'keystone_can_edit_group')})
    def test_index_with_keystone_can_edit_group_false(self):
        domain_id = self._get_domain_id()
        groups = self._get_groups(domain_id)
        filters = {}
        api.keystone.group_list(IgnoreArg(),
                                domain=domain_id,
                                filters=filters) \
            .AndReturn(groups)
        api.keystone.keystone_can_edit_group() \
            .MultipleTimes().AndReturn(False)

        self.mox.ReplayAll()

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, groups)

        self.assertNotContains(res, 'Create Group')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Group')

    @test.create_stubs({api.keystone: ('group_create',
                                       'domain_get')})
    def test_create(self):
        domain_id = self._get_domain_id()
        domain = self.domains.get(id="1")
        group = self.groups.get(id="1")

        api.keystone.domain_get(IsA(http.HttpRequest), '1') \
            .AndReturn(domain)
        api.keystone.group_create(IsA(http.HttpRequest),
                                  description=group.description,
                                  domain_id=domain_id,
                                  name=group.name).AndReturn(group)

        self.mox.ReplayAll()

        formData = {'method': 'CreateGroupForm',
                    'name': group.name,
                    'description': group.description}
        res = self.client.post(GROUP_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('group_create',)})
    def test_create_with_domain(self):
        domain = self.domains.get(id="3")
        group = self.groups.get(id="1")

        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)

        api.keystone.group_create(IsA(http.HttpRequest),
                                  description=group.description,
                                  domain_id=domain.id,
                                  name=group.name).AndReturn(group)

        self.mox.ReplayAll()

        formData = {'method': 'CreateGroupForm',
                    'name': group.name,
                    'description': group.description}
        res = self.client.post(GROUP_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('group_get',
                                       'group_update')})
    def test_update(self):
        group = self.groups.get(id="1")
        test_description = 'updated description'

        api.keystone.group_get(IsA(http.HttpRequest), '1').AndReturn(group)
        api.keystone.group_update(IsA(http.HttpRequest),
                                  description=test_description,
                                  group_id=group.id,
                                  name=group.name).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateGroupForm',
                    'group_id': group.id,
                    'name': group.name,
                    'description': test_description}

        res = self.client.post(GROUP_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'group_list',
                                       'group_delete')})
    def test_delete_group(self):
        domain_id = self._get_domain_id()
        filters = {}
        group = self.groups.get(id="2")

        api.keystone.group_list(IgnoreArg(),
                                domain=domain_id,
                                filters=filters) \
            .AndReturn(self.groups.list())
        api.keystone.group_delete(IgnoreArg(), group.id)

        self.mox.ReplayAll()

        formData = {'action': 'groups__delete__%s' % group.id}
        res = self.client.post(GROUPS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, GROUPS_INDEX_URL)

    @test.create_stubs({api.keystone: ('get_effective_domain_id',
                                       'group_get',
                                       'user_list',)})
    def test_manage(self):
        group = self.groups.get(id="1")
        group_members = self.users.list()
        domain_id = self._get_domain_id()

        api.keystone.group_get(IsA(http.HttpRequest), group.id).\
            AndReturn(group)

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.get_effective_domain_id(
                IgnoreArg()).AndReturn(domain_id)
            api.keystone.user_list(
                IgnoreArg(), group=group.id, domain=domain_id).AndReturn(
                group_members)

        else:
            api.keystone.user_list(
                IgnoreArg(), group=group.id).AndReturn(group_members)
        self.mox.ReplayAll()

        res = self.client.get(GROUP_MANAGE_URL)

        self.assertTemplateUsed(res, constants.GROUPS_MANAGE_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, group_members)

    @test.create_stubs({api.keystone: ('get_effective_domain_id',
                                       'user_list',
                                       'remove_group_user')})
    def test_remove_user(self):
        group = self.groups.get(id="1")
        user = self.users.get(id="2")
        domain_id = self._get_domain_id()

        if api.keystone.VERSIONS.active >= 3:
            api.keystone.get_effective_domain_id(
                IgnoreArg()).AndReturn(domain_id)

            api.keystone.user_list(
                IgnoreArg(), group=group.id, domain=domain_id).AndReturn(
                self.users.list())
        else:
            api.keystone.user_list(
                IgnoreArg(), group=group.id).AndReturn(self.users.list())

        api.keystone.remove_group_user(IgnoreArg(),
                                       group_id=group.id,
                                       user_id=user.id)
        self.mox.ReplayAll()

        formData = {'action': 'group_members__removeGroupMember__%s' % user.id}
        res = self.client.post(GROUP_MANAGE_URL, formData)

        self.assertRedirectsNoFollow(res, GROUP_MANAGE_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('get_effective_domain_id',
                                       'group_get',
                                       'user_list',
                                       'add_group_user')})
    def test_add_user(self):
        group = self.groups.get(id="1")
        user = self.users.get(id="2")
        domain_id = group.domain_id

        api.keystone.get_effective_domain_id(IgnoreArg()).AndReturn(domain_id)

        api.keystone.group_get(IsA(http.HttpRequest), group.id).\
            AndReturn(group)

        api.keystone.user_list(IgnoreArg(), domain=domain_id).\
            AndReturn(self.users.list())

        api.keystone.user_list(IgnoreArg(), domain=domain_id, group=group.id).\
            AndReturn(self.users.list()[2:])

        api.keystone.add_group_user(IgnoreArg(),
                                    group_id=group.id,
                                    user_id=user.id)

        self.mox.ReplayAll()

        formData = {'action': 'group_non_members__add__%s' % user.id}
        res = self.client.post(GROUP_ADD_MEMBER_URL, formData)

        self.assertRedirectsNoFollow(res, GROUP_MANAGE_URL)
        self.assertMessageCount(success=1)

    @test.update_settings(FILTER_DATA_FIRST={'identity.groups': True})
    def test_index_with_filter_first(self):
        res = self.client.get(GROUPS_INDEX_URL)
        self.assertTemplateUsed(res, constants.GROUPS_INDEX_VIEW_TEMPLATE)
        groups = res.context['table'].data
        self.assertItemsEqual(groups, [])
