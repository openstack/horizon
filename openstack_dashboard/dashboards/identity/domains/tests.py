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

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.identity.domains import constants
from openstack_dashboard.dashboards.identity.domains import workflows
from openstack_dashboard.test import helpers as test


DOMAINS_INDEX_URL = reverse(constants.DOMAINS_INDEX_URL)
DOMAIN_CREATE_URL = reverse(constants.DOMAINS_CREATE_URL)
DOMAIN_UPDATE_URL = reverse(constants.DOMAINS_UPDATE_URL, args=[1])
USER_ROLE_PREFIX = constants.DOMAIN_USER_MEMBER_SLUG + "_role_"
GROUP_ROLE_PREFIX = constants.DOMAIN_GROUP_MEMBER_SLUG + "_role_"


class DomainsViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.keystone: ('domain_list',)})
    def test_index(self):
        self.mock_domain_list.return_value = self.domains.list()

        res = self.client.get(DOMAINS_INDEX_URL)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertContains(res, 'Create Domain')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Domain')
        self.assertContains(res, 'Disable Domain')
        self.assertContains(res, 'Enable Domain')

        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('domain_list',
                                       'keystone_can_edit_domain')})
    def test_index_with_keystone_can_edit_domain_false(self):
        self.mock_domain_list.return_value = self.domains.list()
        self.mock_keystone_can_edit_domain.return_value = False

        res = self.client.get(DOMAINS_INDEX_URL)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertNotContains(res, 'Create Domain')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Domain')
        self.assertNotContains(res, 'Disable Domain')
        self.assertNotContains(res, 'Enable Domain')

        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_keystone_can_edit_domain, 20, mock.call())

    @test.create_mocks({api.keystone: ('domain_list',
                                       'domain_delete')})
    def test_delete_domain(self):
        domain = self.domains.get(id="2")

        self.mock_domain_list.return_value = self.domains.list()
        self.mock_domain_delete.return_value = None

        formData = {'action': 'domains__delete__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_domain_delete.assert_called_once_with(test.IsHttpRequest(),
                                                        domain.id)

    @test.create_mocks({api.keystone: ('domain_list', )})
    def test_delete_with_enabled_domain(self):
        domain = self.domains.get(id="1")

        self.mock_domain_list.return_value = self.domains.list()

        formData = {'action': 'domains__delete__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
        self.assertMessageCount(error=2)

        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('domain_list',
                                       'domain_update')})
    def test_disable(self):
        domain = self.domains.get(id="1")

        self.mock_domain_list.return_value = self.domains.list()
        self.mock_domain_update.return_value = None

        formData = {'action': 'domains__disable__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
        self.assertMessageCount(error=0)

        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_domain_update.assert_called_once_with(
            test.IsHttpRequest(),
            description=domain.description,
            domain_id=domain.id,
            enabled=False,
            name=domain.name)

    @test.create_mocks({api.keystone: ('domain_list',
                                       'domain_update')})
    def test_enable(self):
        domain = self.domains.get(id="2")

        self.mock_domain_list.return_value = self.domains.list()
        self.mock_domain_update.return_value = None

        formData = {'action': 'domains__enable__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
        self.assertMessageCount(error=0)

        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_domain_update.assert_called_once_with(
            test.IsHttpRequest(),
            description=domain.description,
            domain_id=domain.id,
            enabled=True,
            name=domain.name)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'domain_list', )})
    def test_set_clear_domain_context(self):
        domain = self.domains.get(id="3")

        self.mock_domain_get.return_value = domain
        self.mock_domain_list.return_value = self.domains.list()

        formData = {'action': 'domains__set_domain_context__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, [domain, ])
        self.assertContains(res, "<em>another_test_domain:</em>")

        formData = {'action': 'domains__clear_domain_context__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertNotContains(res, "<em>test_domain:</em>")
        self.assertNotContains(res, "<em>another_test_domain:</em>")

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_domain_get, 2,
            mock.call(test.IsHttpRequest(), domain.id))
        self.mock_domain_list.assert_called_once_with(test.IsHttpRequest())


class CreateDomainWorkflowTests(test.BaseAdminViewTests):

    def _get_domain_info(self, domain):
        domain_info = {"name": domain.name,
                       "description": domain.description,
                       "enabled": domain.enabled}
        return domain_info

    def _get_workflow_data(self, domain):
        domain_info = self._get_domain_info(domain)
        return domain_info

    def test_add_domain_get(self):
        url = reverse('horizon:identity:domains:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.CreateDomain.name)

        self.assertQuerysetEqual(workflow.steps,
                                 ['<CreateDomainInfo: create_domain>', ])

    @test.create_mocks({api.keystone: ('domain_create', )})
    def test_add_domain_post(self):
        domain = self.domains.get(id="1")

        self.mock_domain_create.return_value = domain

        workflow_data = self._get_workflow_data(domain)

        res = self.client.post(DOMAIN_CREATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

        self.mock_domain_create.assert_called_once_with(
            test.IsHttpRequest(),
            description=domain.description,
            enabled=domain.enabled,
            name=domain.name)


class UpdateDomainWorkflowTests(test.BaseAdminViewTests):

    def _get_domain_info(self, domain):
        domain_info = {"domain_id": domain.id,
                       "name": domain.name,
                       "description": domain.description,
                       "enabled": domain.enabled}
        return domain_info

    def _get_workflow_data(self, domain):
        domain_info = self._get_domain_info(domain)
        return domain_info

    def _get_all_users(self, domain_id=None):
        if not domain_id:
            users = self.users.list()
        else:
            users = [user for user in self.users.list()
                     if user.domain_id == domain_id]
        return users

    def _get_all_groups(self, domain_id):
        if not domain_id:
            groups = self.groups.list()
        else:
            groups = [group for group in self.groups.list()
                      if group.domain_id == domain_id]
        return groups

    def _get_domain_groups(self, domain_id):
        # all domain groups have role assignments
        return self._get_all_groups(domain_id)

    def _get_domain_role_assignment(self, domain_id):
        domain_scope = {'domain': {'id': domain_id}}
        return self.role_assignments.filter(scope=domain_scope)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'get_default_role',
                                       'role_list',
                                       'user_list',
                                       'role_assignments_list',
                                       'group_list',
                                       'roles_for_group')})
    def test_update_domain_get(self):
        default_role = self.roles.first()
        domain = self.domains.get(id="1")
        users = self._get_all_users(domain.id)
        groups = self._get_all_groups(domain.id)
        roles = self.roles.list()
        role_assignments = self._get_domain_role_assignment(domain.id)

        self.mock_domain_get.return_value = domain
        self.mock_get_default_role.return_value = default_role
        self.mock_role_list.return_value = roles
        self.mock_user_list.return_value = users
        self.mock_role_assignments_list.return_value = role_assignments
        self.mock_group_list.return_value = groups
        self.mock_roles_for_group.return_value = roles

        res = self.client.get(DOMAIN_UPDATE_URL)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.UpdateDomain.name)

        step = workflow.get_step("update_domain")
        self.assertEqual(step.action.initial['name'], domain.name)
        self.assertEqual(step.action.initial['description'],
                         domain.description)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<UpdateDomainInfo: update_domain>',
             '<UpdateDomainUsers: update_user_members>',
             '<UpdateDomainGroups: update_group_members>'])

        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2, mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2, mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain.id)
        self.mock_role_assignments_list.assert_called_once_with(
            test.IsHttpRequest(),
            domain=domain.id,
            include_subtree=False)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain.id)
        self.mock_roles_for_group.assert_has_calls(
            [mock.call(test.IsHttpRequest(), group=group.id, domain=domain.id)
             for group in groups])

    @test.create_mocks({api.keystone: ('domain_get',
                                       'domain_update',
                                       'get_default_role',
                                       'role_list',
                                       'user_list',
                                       'role_assignments_list',
                                       'roles_for_user',
                                       'add_domain_user_role',
                                       'remove_domain_user_role',
                                       'group_list',
                                       'roles_for_group',
                                       'remove_group_role',
                                       'add_group_role',)})
    def test_update_domain_post(self):
        default_role = self.roles.first()
        domain = self.domains.get(id="1")
        test_description = 'updated description'
        users = self._get_all_users(domain.id)
        groups = self._get_all_groups(domain.id)
        domain_groups = self._get_domain_groups(domain.id)
        roles = self.roles.list()
        role_assignments = self._get_domain_role_assignment(domain.id)

        self.mock_domain_get.return_value = domain
        self.mock_get_default_role.return_value = default_role
        self.mock_role_list.return_value = roles
        self.mock_user_list.return_value = users
        self.mock_role_assignments_list.return_value = role_assignments
        expected_group_list = []
        retvals_group_list = []
        self.mock_group_list.side_effect = retvals_group_list
        expected_roles_for_group = []
        retvals_roles_for_group = []
        self.mock_roles_for_group.side_effect = retvals_roles_for_group
        expected_remove_group_role = []
        expected_add_group_role = []
        self.mock_remove_group_role.return_value = None
        self.mock_add_group_role.return_value = None

        expected_group_list.append(
            mock.call(test.IsHttpRequest(), domain=domain.id))
        retvals_group_list.append(groups)

        for group in groups:
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(),
                          group=group.id,
                          domain=domain.id))
            retvals_roles_for_group.append(roles)

        workflow_data = self._get_workflow_data(domain)
        # update some fields
        workflow_data['description'] = test_description
        # User assignment form data
        workflow_data[USER_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[USER_ROLE_PREFIX + "2"] = ['2']  # member role
        # Group assignment form data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['2']  # member role

        # handle
        self.mock_domain_update.return_value = None

        # Give user 3 role 1
        self.mock_add_domain_user_role.return_value = None

        # remove role 2 from user 3
        self.mock_remove_domain_user_role.return_value = None

        # Group assignments
        expected_group_list.append(
            mock.call(test.IsHttpRequest(), domain=domain.id))
        retvals_group_list.append(domain_groups)

        # admin group - try to remove all roles on current domain
        expected_roles_for_group.append(
            mock.call(test.IsHttpRequest(), group='1', domain=domain.id))
        retvals_roles_for_group.append(roles)
        for role in roles:
            expected_remove_group_role.append(
                mock.call(test.IsHttpRequest(),
                          role=role.id, group='1', domain=domain.id))

        # member group 1 - has role 1, will remove it
        expected_roles_for_group.append(
            mock.call(test.IsHttpRequest(), group='2', domain=domain.id))
        retvals_roles_for_group.append((roles[0],))
        # remove role 1
        expected_remove_group_role.append(
            mock.call(test.IsHttpRequest(),
                      role='1', group='2', domain=domain.id))
        # add role 2
        expected_add_group_role.append(
            mock.call(test.IsHttpRequest(),
                      role='2', group='2', domain=domain.id))

        # member group 3 - has role 2
        expected_roles_for_group.append(
            mock.call(test.IsHttpRequest(), group='3', domain=domain.id))
        retvals_roles_for_group.append((roles[1],))
        # remove role 2
        expected_remove_group_role.append(
            mock.call(test.IsHttpRequest(),
                      role='2', group='3', domain=domain.id))
        # add role 1
        expected_add_group_role.append(
            mock.call(test.IsHttpRequest(),
                      role='1', group='3', domain=domain.id))

        res = self.client.post(DOMAIN_UPDATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

        # init and handle
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(), '1')
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 6,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_user_list, 2,
            mock.call(test.IsHttpRequest(), domain=domain.id))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_assignments_list, 2,
            mock.call(test.IsHttpRequest(),
                      domain=domain.id, include_subtree=False))
        self.mock_domain_update.assert_called_once_with(
            test.IsHttpRequest(),
            domain.id,
            name=domain.name,
            description=test_description,
            enabled=domain.enabled)

        # Give user 3 role 1
        self.mock_add_domain_user_role.assert_called_once_with(
            test.IsHttpRequest(), domain=domain.id, user='3', role='1')
        # remove role 2 from user 3
        self.mock_remove_domain_user_role.assert_called_once_with(
            test.IsHttpRequest(), domain=domain.id, user='3', role='2')

        self.mock_group_list.assert_has_calls(
            expected_group_list)
        self.assertEqual(len(expected_group_list),
                         self.mock_group_list.call_count)
        self.mock_roles_for_group.assert_has_calls(
            expected_roles_for_group)
        self.assertEqual(len(expected_roles_for_group),
                         self.mock_roles_for_group.call_count)
        self.mock_remove_group_role.assert_has_calls(
            expected_remove_group_role)
        self.assertEqual(len(expected_remove_group_role),
                         self.mock_remove_group_role.call_count)
        self.mock_add_group_role.assert_has_calls(
            expected_add_group_role)
        self.assertEqual(len(expected_add_group_role),
                         self.mock_add_group_role.call_count)

    @test.create_mocks({api.keystone: ('domain_get',)})
    def test_update_domain_get_error(self):
        domain = self.domains.get(id="1")

        self.mock_domain_get.side_effect = self.exceptions.keystone

        res = self.client.get(DOMAIN_UPDATE_URL)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)

    @test.create_mocks({api.keystone: ('domain_get',
                                       'domain_update',
                                       'get_default_role',
                                       'role_list',
                                       'user_list',
                                       'role_assignments_list',
                                       'group_list',
                                       'roles_for_group')})
    def test_update_domain_post_error(self):
        default_role = self.roles.first()
        domain = self.domains.get(id="1")
        test_description = 'updated description'
        users = self._get_all_users(domain.id)
        groups = self._get_all_groups(domain.id)
        roles = self.roles.list()
        role_assignments = self._get_domain_role_assignment(domain.id)

        self.mock_domain_get(test.IsHttpRequest(), '1').AndReturn(domain)
        self.mock_get_default_role(test.IsHttpRequest()) \
            .MultipleTimes().AndReturn(default_role)
        self.mock_role_list(test.IsHttpRequest()) \
            .MultipleTimes().AndReturn(roles)
        self.mock_user_list(test.IsHttpRequest(), domain=domain.id) \
            .AndReturn(users)
        self.mock_role_assignments_list(test.IsHttpRequest(),
                                        domain=domain.id,
                                        include_subtree=False) \
            .AndReturn(role_assignments)
        self.mock_group_list(test.IsHttpRequest(), domain=domain.id) \
            .AndReturn(groups)

        for group in groups:
            self.mock_roles_for_group(test.IsHttpRequest(),
                                      group=group.id,
                                      domain=domain.id) \
                .AndReturn(roles)

        workflow_data = self._get_workflow_data(domain)
        # update some fields
        workflow_data['description'] = test_description

        # User assignment form data
        workflow_data[USER_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[USER_ROLE_PREFIX + "2"] = ['2']  # member role
        # Group assignment form data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['2']  # member role

        # handle
        self.mock_domain_update.side_effect = self.exceptions.keystone

        res = self.client.post(DOMAIN_UPDATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

        self.mock_domain_update.assert_called_once_with(
            test.IsHttpRequest(),
            domain.id,
            name=domain.name,
            description=test_description,
            enabled=domain.enabled)
