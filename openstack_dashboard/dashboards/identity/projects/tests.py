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

import datetime
import logging

from django.test import tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

import mock

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.identity.projects import tabs
from openstack_dashboard.dashboards.identity.projects import workflows
from openstack_dashboard.test import helpers as test
from openstack_dashboard import usage
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:identity:projects:index')
USER_ROLE_PREFIX = workflows.PROJECT_USER_MEMBER_SLUG + "_role_"
GROUP_ROLE_PREFIX = workflows.PROJECT_GROUP_MEMBER_SLUG + "_role_"
PROJECT_DETAIL_URL = reverse('horizon:identity:projects:detail', args=[1])


class TenantsViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.keystone: ('get_effective_domain_id',
                                       'tenant_list',
                                       'domain_lookup'),
                        quotas: ('enabled_quotas',)})
    def test_index(self):
        domain = self.domains.get(id="1")
        filters = {}
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_domain_lookup.return_value = {domain.id: domain.name}
        self.mock_enabled_quotas.return_value = ('instances',)
        self.mock_get_effective_domain_id.return_value = None

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'identity/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants.list())

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                      domain=None,
                                                      paginate=True,
                                                      filters=filters,
                                                      marker=None)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_enabled_quotas, 3,
            mock.call(test.IsHttpRequest()))
        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('tenant_list',
                                       'domain_lookup'),
                        quotas: ('enabled_quotas',)})
    def test_index_with_domain_context(self):
        domain = self.domains.get(id="1")
        filters = {}
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)

        domain_tenants = [tenant for tenant in self.tenants.list()
                          if tenant.domain_id == domain.id]

        self.mock_tenant_list.return_value = [domain_tenants, False]
        self.mock_domain_lookup.return_value = {domain.id: domain.name}
        self.mock_enabled_quotas.return_value = ('instances',)

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'identity/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, domain_tenants)
        self.assertContains(res, "<em>test_domain:</em>")

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                      domain=domain.id,
                                                      paginate=True,
                                                      marker=None,
                                                      filters=filters)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())

    @test.update_settings(FILTER_DATA_FIRST={'identity.projects': True})
    def test_index_with_filter_first(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'identity/projects/index.html')
        projects = res.context['table'].data
        self.assertItemsEqual(projects, [])


class ProjectsViewNonAdminTests(test.TestCase):

    @override_settings(POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.keystone: ('tenant_list',
                                       'domain_lookup')})
    def test_index(self):
        domain = self.domains.get(id="1")
        filters = {}
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_domain_lookup.return_value = {domain.id: domain.name}

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'identity/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants.list())

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest(),
                                                      user=self.user.id,
                                                      paginate=True,
                                                      marker=None,
                                                      filters=filters,
                                                      admin=False)
        self.mock_domain_lookup.assert_called_once_with(test.IsHttpRequest())


class CreateProjectWorkflowTests(test.BaseAdminViewTests):

    def _get_project_info(self, project):
        domain = self._get_default_domain()
        project_info = {"name": project.name,
                        "description": project.description,
                        "enabled": project.enabled,
                        "domain": domain.id}
        return project_info

    def _get_workflow_fields(self, project):
        domain = self._get_default_domain()
        project_info = {"domain_id": domain.id,
                        "domain_name": domain.name,
                        "name": project.name,
                        "description": project.description,
                        "enabled": project.enabled}
        return project_info

    def _get_workflow_data(self, project):
        project_info = self._get_workflow_fields(project)
        return project_info

    def _get_default_domain(self):
        default_domain = self.domain
        domain = {"id": self.request.session.get('domain_context',
                                                 default_domain.id),
                  "name": self.request.session.get('domain_context_name',
                                                   default_domain.name)}
        return api.base.APIDictWrapper(domain)

    def _get_all_users(self, domain_id):
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

    @test.create_mocks({api.keystone: ('get_default_domain',
                                       'get_default_role',
                                       'user_list',
                                       'group_list',
                                       'role_list')})
    def test_add_project_get(self):
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        self.mock_get_default_domain.return_value = default_domain
        self.mock_get_default_role.return_value = default_role
        self.mock_user_list.return_value = users
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        url = reverse('horizon:identity:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.CreateProject.name)

        self.assertQuerysetEqual(
            workflow.steps,
            ['<CreateProjectInfo: createprojectinfoaction>',
             '<UpdateProjectMembers: update_members>',
             '<UpdateProjectGroups: update_group_members>'])

        self.mock_get_default_domain.assert_called_once_with(
            test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id)

    def test_add_project_get_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_get()

    @override_settings(PROJECT_TABLE_EXTRA_INFO={'phone_num': 'Phone Number'})
    @test.create_mocks({api.keystone: ('get_default_role',
                                       'add_group_role',
                                       'add_tenant_user_role',
                                       'tenant_create',
                                       'user_list',
                                       'group_list',
                                       'role_list',
                                       'domain_get')})
    def test_add_project_post(self):
        project = self.tenants.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()
        # extra info
        phone_number = "+81-3-1234-5678"

        # init
        self.mock_get_default_role.return_value = default_role
        self.mock_user_list.return_value = users
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        # handle
        project_details = self._get_project_info(project)
        # add extra info
        project_details.update({'phone_num': phone_number})
        self.mock_tenant_create.return_value = project

        workflow_data = {}
        expected_add_tenant_user_roles = []
        expected_add_group_role = []
        self.mock_add_tenant_user_role.return_value = None
        self.mock_add_group_role.return_value = None
        for role in roles:
            if USER_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[USER_ROLE_PREFIX + role.id]
                for user_id in ulist:
                    expected_add_tenant_user_roles.append(
                        mock.call(test.IsHttpRequest(),
                                  project=self.tenant.id,
                                  user=user_id,
                                  role=role.id))
        for role in roles:
            if GROUP_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[GROUP_ROLE_PREFIX + role.id]
                for group_id in ulist:
                    expected_add_group_role.append(
                        mock.call(test.IsHttpRequest(),
                                  role=role.id,
                                  group=group_id,
                                  project=self.tenant.id))

        workflow_data.update(self._get_workflow_data(project))
        workflow_data.update({'phone_num': phone_number})

        url = reverse('horizon:identity:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 6,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id)
        self.mock_tenant_create.assert_called_once_with(test.IsHttpRequest(),
                                                        **project_details)
        self.mock_add_tenant_user_role.assert_has_calls(
            expected_add_tenant_user_roles)
        self.assertEqual(len(expected_add_tenant_user_roles),
                         self.mock_add_tenant_user_role.call_count)
        self.mock_add_group_role.assert_has_calls(expected_add_group_role)
        self.assertEqual(len(expected_add_group_role),
                         self.mock_add_group_role.call_count)

    def test_add_project_post_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_post()

    @test.create_mocks({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role')})
    def test_add_project_tenant_create_error(self):
        project = self.tenants.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        self.mock_get_default_domain.return_value = default_domain
        self.mock_get_default_role.return_value = default_role
        self.mock_user_list.return_value = users
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        # handle
        project_details = self._get_project_info(project)

        self.mock_tenant_create.side_effect = self.exceptions.keystone

        workflow_data = self._get_workflow_data(project)

        url = reverse('horizon:identity:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_get_default_domain.assert_called_once_with(
            test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 4,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id)
        self.mock_tenant_create.assert_called_once_with(test.IsHttpRequest(),
                                                        **project_details)

    def test_add_project_tenant_create_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_tenant_create_error()

    @test.create_mocks({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role',
                                       'add_tenant_user_role')})
    def test_add_project_user_update_error(self):
        project = self.tenants.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        self.mock_get_default_domain.return_value = default_domain
        self.mock_get_default_role.return_value = default_role
        self.mock_user_list.return_value = users
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        # handle
        project_details = self._get_project_info(project)
        self.mock_tenant_create.return_value = project

        workflow_data = {}
        expected_add_tenant_user_roles = []
        self.mock_add_tenant_user_role.side_effect = self.exceptions.keystone
        for role in roles:
            if USER_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[USER_ROLE_PREFIX + role.id]
                for user_id in ulist:
                    expected_add_tenant_user_roles.append(
                        mock.call(test.IsHttpRequest(),
                                  project=self.tenant.id,
                                  user=user_id,
                                  role=role.id))
                    break
            break

        workflow_data.update(self._get_workflow_data(project))

        url = reverse('horizon:identity:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_get_default_domain.assert_called_once_with(
            test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 6,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id)
        self.mock_tenant_create.assert_called_once_with(
            test.IsHttpRequest(), **project_details)
        self.mock_add_tenant_user_role.assert_has_calls(
            expected_add_tenant_user_roles)
        self.assertEqual(len(expected_add_tenant_user_roles),
                         self.mock_add_tenant_user_role.call_count)

    def test_add_project_user_update_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_user_update_error()

    @test.create_mocks({api.keystone: ('user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role')})
    def test_add_project_missing_field_error(self):
        project = self.tenants.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        self.mock_get_default_domain.return_value = default_domain
        self.mock_get_default_role.return_value = default_role
        self.mock_user_list.return_value = users
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        workflow_data = self._get_workflow_data(project)
        workflow_data["name"] = ""

        url = reverse('horizon:identity:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertContains(res, "field is required")

        self.mock_get_default_domain.assert_called_once_with(
            test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(test.IsHttpRequest(),
                                                    domain=domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 4,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id)

    def test_add_project_missing_field_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_missing_field_error()


class UpdateProjectWorkflowTests(test.BaseAdminViewTests):

    def _get_all_users(self, domain_id):
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

    def _get_proj_users(self, project_id):
        return [user for user in self.users.list()
                if user.project_id == project_id]

    def _get_proj_groups(self, project_id):
        return [group for group in self.groups.list()
                if group.project_id == project_id]

    def _get_proj_role_assignment(self, project_id):
        project_scope = {'project': {'id': project_id}}
        return self.role_assignments.filter(scope=project_scope)

    @test.create_mocks({api.keystone: ('get_default_role',
                                       'roles_for_user',
                                       'tenant_get',
                                       'domain_get',
                                       'user_list',
                                       'roles_for_group',
                                       'group_list',
                                       'role_list',
                                       'role_assignments_list')})
    def test_update_project_get(self):
        keystone_api_version = api.keystone.VERSIONS.active

        project = self.tenants.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()
        proj_users = self._get_proj_users(project.id)
        role_assignments = self._get_proj_role_assignment(project.id)

        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = self.domain

        self.mock_get_default_role.return_value = default_role
        retvals_user_list = [users]
        expected_user_list = [
            mock.call(test.IsHttpRequest(), domain=domain_id)
        ]
        self.mock_user_list.side_effect = retvals_user_list
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        if keystone_api_version >= 3:
            self.mock_role_assignments_list.return_value = role_assignments
        else:
            retvals_user_list.append(proj_users)
            expected_user_list.append(
                mock.call(test.IsHttpRequest(), project=self.tenant.id))
            self.mock_roles_for_user.return_value = roles

        url = reverse('horizon:identity:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.UpdateProject.name)

        step = workflow.get_step("update_info")
        self.assertEqual(step.action.initial['name'], project.name)
        self.assertEqual(step.action.initial['description'],
                         project.description)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<UpdateProjectInfo: update_info>',
             '<UpdateProjectMembers: update_members>',
             '<UpdateProjectGroups: update_group_members>'])

        self.mock_tenant_get.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id, admin=True)
        self.mock_domain_get.assert_called_once_with(
            test.IsHttpRequest(), domain_id)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_has_calls(expected_user_list)
        self.assertEqual(len(expected_user_list),
                         self.mock_user_list.call_count)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(
            test.IsHttpRequest(), domain=domain_id)

        if keystone_api_version >= 3:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_role_assignments_list, 2,
                mock.call(test.IsHttpRequest(), project=self.tenant.id))
            self.mock_roles_for_user.assert_not_called()
        else:
            self.mock_roles_for_user.assert_has_calls(
                [mock.call(test.IsHttpRequest(), user.id, self.tenant.id)
                 for user in proj_users])
            self.mock_role_assignments_list.assert_not_called()

    @test.create_mocks({api.keystone: ('tenant_get',
                                       'domain_get',
                                       'get_effective_domain_id',
                                       'tenant_update',
                                       'get_default_role',
                                       'roles_for_user',
                                       'remove_tenant_user_role',
                                       'add_tenant_user_role',
                                       'user_list',
                                       'roles_for_group',
                                       'remove_group_role',
                                       'add_group_role',
                                       'group_list',
                                       'role_list',
                                       'role_assignments_list')})
    def test_update_project_save(self):
        keystone_api_version = api.keystone.VERSIONS.active

        project = self.tenants.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        proj_users = self._get_proj_users(project.id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()
        role_assignments = self._get_proj_role_assignment(project.id)

        # get/init
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = self.domain

        self.mock_get_default_role.return_value = default_role
        retvals_user_list = [users]
        expected_user_list = [
            mock.call(test.IsHttpRequest(), domain=domain_id)
        ]
        self.mock_user_list.side_effect = retvals_user_list
        self.mock_role_list.return_value = roles
        retvals_group_list = [groups]
        expected_group_list = [
            mock.call(test.IsHttpRequest(), domain=domain_id)
        ]
        self.mock_group_list.side_effect = retvals_group_list

        workflow_data = {}

        retvals_roles_for_user = []
        expected_roles_for_user = []
        self.mock_roles_for_user.side_effect = retvals_roles_for_user

        if keystone_api_version < 3:
            retvals_user_list.append(proj_users)
            expected_user_list.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id))
            for user in proj_users:
                retvals_roles_for_user.append(roles)
                expected_roles_for_user.append(
                    mock.call(test.IsHttpRequest(), user.id, self.tenant.id))

        workflow_data[USER_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[USER_ROLE_PREFIX + "2"] = ['2']  # member role
        # Group assignment form  data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['2']  # member role

        # update some fields
        project._info["domain_id"] = domain_id
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"

        # called once for tenant_update
        self.mock_get_effective_domain_id.return_value = domain_id

        # handle
        self.mock_tenant_update.return_value = project

        retvals_user_list.append(users)
        expected_user_list.append(
            mock.call(test.IsHttpRequest(), domain=domain_id))

        retvals_add_tenant_user_role = []
        expected_add_tenant_user_role = []
        self.mock_add_tenant_user_role.side_effect = \
            retvals_add_tenant_user_role
        retvals_remove_tenant_user_role = []
        expected_remove_tenant_user_role = []
        self.mock_remove_tenant_user_role.side_effect = \
            retvals_remove_tenant_user_role
        retvals_roles_for_group = []
        expected_roles_for_group = []
        self.mock_roles_for_group.side_effect = retvals_roles_for_group
        retvals_remove_group_role = []
        expected_remove_group_role = []
        self.mock_remove_group_role.side_effect = retvals_remove_group_role

        if keystone_api_version >= 3:
            # admin role with attempt to remove current admin, results in
            # warning message
            workflow_data[USER_ROLE_PREFIX + "1"] = ['3']

            # member role
            workflow_data[USER_ROLE_PREFIX + "2"] = ['1', '3']

            # admin role
            workflow_data[GROUP_ROLE_PREFIX + "1"] = ['2', '3']

            # member role
            workflow_data[GROUP_ROLE_PREFIX + "2"] = ['1', '2', '3']
            self.mock_role_assignments_list.return_value = role_assignments
            # Give user 1 role 2
            retvals_add_tenant_user_role.append(None)
            expected_add_tenant_user_role.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id,
                          user='1',
                          role='2',))
            # remove role 2 from user 2
            retvals_remove_tenant_user_role.append(None)
            expected_remove_tenant_user_role.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id,
                          user='2',
                          role='2'))

            # Give user 3 role 1
            retvals_add_tenant_user_role.append(None)
            expected_add_tenant_user_role.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id,
                          user='3',
                          role='1'))
            retvals_group_list.append(groups)
            expected_group_list.append(
                mock.call(test.IsHttpRequest(),
                          domain=self.domain.id,
                          project=self.tenant.id))
            retvals_roles_for_group.append(roles)
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(),
                          group='1',
                          project=self.tenant.id))
            retvals_remove_group_role.append(None)
            expected_remove_group_role.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id,
                          group='1',
                          role='1'))
            retvals_roles_for_group.append(roles)
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(),
                          group='2',
                          project=self.tenant.id))
            retvals_roles_for_group.append(roles)
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(),
                          group='3',
                          project=self.tenant.id))
        else:
            retvals_user_list.append(proj_users)
            expected_user_list.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id))

            # admin user - try to remove all roles on current project, warning
            retvals_roles_for_user.append(roles)
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(), '1', self.tenant.id))

            # member user 1 - has role 1, will remove it
            retvals_roles_for_user.append((roles[1],))
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(), '2', self.tenant.id))

            # member user 3 - has role 2
            retvals_roles_for_user.append((roles[0],))
            expected_roles_for_group.append(
                mock.call(test.IsHttpRequest(), '3', self.tenant.id))
            # add role 2
            retvals_add_tenant_user_role.append(self.exceptions.keystone)
            expected_add_tenant_user_role.append(
                mock.call(test.IsHttpRequest(),
                          project=self.tenant.id,
                          user='3',
                          role='2'))

        # submit form data
        project_data = {"domain_id": project._info["domain_id"],
                        "name": project._info["name"],
                        "id": project.id,
                        "description": project._info["description"],
                        "enabled": project.enabled}
        workflow_data.update(project_data)
        url = reverse('horizon:identity:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        def _check_mock_calls(mocked_call, expected_calls, any_order=False):
            mocked_call.assert_has_calls(expected_calls, any_order=any_order)
            self.assertEqual(len(expected_calls), mocked_call.call_count)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id,
                                                     admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        _check_mock_calls(self.mock_user_list, expected_user_list)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 5,
            mock.call(test.IsHttpRequest()))
        _check_mock_calls(self.mock_group_list, expected_group_list)
        _check_mock_calls(self.mock_roles_for_user, expected_roles_for_user)

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_update.assert_called_once_with(
            test.IsHttpRequest(),
            project.id,
            name=project._info["name"],
            description=project._info['description'],
            enabled=project.enabled,
            domain=domain_id)

        _check_mock_calls(self.mock_add_tenant_user_role,
                          expected_add_tenant_user_role, any_order=True)
        _check_mock_calls(self.mock_remove_tenant_user_role,
                          expected_remove_tenant_user_role, any_order=True)
        _check_mock_calls(self.mock_roles_for_group,
                          expected_roles_for_group)
        _check_mock_calls(self.mock_remove_group_role,
                          expected_remove_group_role)

        if keystone_api_version >= 3:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_role_assignments_list, 3,
                mock.call(test.IsHttpRequest(), project=self.tenant.id))
        else:
            self.mock_role_assignments_list.assert_not_called()

    @test.create_mocks({api.keystone: ('tenant_get',)})
    def test_update_project_get_error(self):
        self.mock_tenant_get.side_effect = self.exceptions.nova

        url = reverse('horizon:identity:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id,
                                                     admin=True)

    @test.create_mocks({api.keystone: ('tenant_get',
                                       'domain_get',
                                       'get_effective_domain_id',
                                       'tenant_update',
                                       'get_default_role',
                                       'roles_for_user',
                                       'remove_tenant_user',
                                       'add_tenant_user_role',
                                       'user_list',
                                       'roles_for_group',
                                       'remove_group_role',
                                       'add_group_role',
                                       'group_list',
                                       'role_list',
                                       'role_assignments_list')})
    def test_update_project_tenant_update_error(self):
        keystone_api_version = api.keystone.VERSIONS.active

        project = self.tenants.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()
        proj_users = self._get_proj_users(project.id)
        role_assignments = self.role_assignments.list()

        # get/init
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = self.domain

        self.mock_get_default_role.return_value = default_role
        retvals_user_list = [users]
        expected_user_list = [
            mock.call(test.IsHttpRequest(), domain=domain_id)
        ]
        self.mock_user_list.side_effect = retvals_user_list
        self.mock_role_list.return_value = roles
        self.mock_group_list.return_value = groups

        workflow_data = {}

        retvals_roles_for_user = []
        expected_roles_for_user = []
        self.mock_roles_for_user.side_effect = retvals_roles_for_user

        if keystone_api_version >= 3:
            self.mock_role_assignments_list.return_value = role_assignments
        else:
            retvals_user_list.append(proj_users)
            expected_roles_for_user.append(
                mock.call(test.IsHttpRequest(), project=self.tenant.id))
            for user in proj_users:
                retvals_roles_for_user.append(roles)
                expected_roles_for_user.append(
                    mock.call(test.IsHttpRequest(), user.id, self.tenant.id))

        role_ids = [role.id for role in roles]
        for user in proj_users:
            if role_ids:
                workflow_data.setdefault(USER_ROLE_PREFIX + role_ids[0], []) \
                             .append(user.id)

        role_ids = [role.id for role in roles]
        for group in groups:
            if role_ids:
                workflow_data.setdefault(GROUP_ROLE_PREFIX + role_ids[0], []) \
                             .append(group.id)

        # update some fields
        project._info["domain_id"] = domain_id
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"

        # handle
        self.mock_get_effective_domain_id.return_value = domain_id

        self.mock_tenant_update.side_effect = self.exceptions.keystone

        # submit form data
        project_data = {"domain_id": project._info["domain_id"],
                        "name": project._info["name"],
                        "id": project.id,
                        "description": project._info["description"],
                        "enabled": project.enabled}
        workflow_data.update(project_data)
        url = reverse('horizon:identity:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id,
                                                     admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_has_calls(expected_user_list)
        self.assertEqual(len(expected_user_list),
                         self.mock_user_list.call_count)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 4,
            mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                     domain=domain_id)
        self.mock_roles_for_user.assert_has_calls(expected_roles_for_user)
        self.assertEqual(len(expected_roles_for_user),
                         self.mock_roles_for_user.call_count)

        if keystone_api_version >= 3:
            self.assert_mock_multiple_calls_with_same_arguments(
                self.mock_role_assignments_list, 2,
                mock.call(test.IsHttpRequest(), project=self.tenant.id))
        else:
            self.mock_role_assignments_list.assert_not_called()

        self.mock_get_effective_domain_id.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_update.assert_called_once_with(
            test.IsHttpRequest(),
            project.id,
            name=project._info["name"],
            domain=domain_id,
            description=project._info['description'],
            enabled=project.enabled)

    @test.create_mocks({api.keystone: ('get_default_role',
                                       'tenant_get',
                                       'domain_get')})
    def test_update_project_when_default_role_does_not_exist(self):
        project = self.tenants.first()
        domain_id = project.domain_id

        self.mock_get_default_role.return_value = None
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = self.domain

        url = reverse('horizon:identity:projects:update',
                      args=[self.tenant.id])

        try:
            # Avoid the log message in the test output when the workflow's
            # step action cannot be instantiated
            logging.disable(logging.ERROR)
            res = self.client.get(url)
        finally:
            logging.disable(logging.NOTSET)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1, warning=0)

        self.mock_get_default_role.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id,
                                                     admin=True)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain_id)


class UpdateQuotasWorkflowTests(test.BaseAdminViewTests):

    def _get_quota_info(self, quota):
        cinder_quota = self.cinder_quotas.first()
        neutron_quota = self.neutron_quotas.first()
        quota_data = {}
        for field in quotas.NOVA_QUOTA_FIELDS:
            quota_data[field] = int(quota.get(field).limit)
        for field in quotas.CINDER_QUOTA_FIELDS:
            quota_data[field] = int(cinder_quota.get(field).limit)
        for field in quotas.NEUTRON_QUOTA_FIELDS:
            quota_data[field] = int(neutron_quota.get(field).limit)
        return quota_data

    @test.create_mocks({quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas')})
    def test_update_quotas_get(self):
        quota = self.quotas.first()

        self.mock_get_disabled_quotas.return_value = set()
        self.mock_get_tenant_quota_data.return_value = quota

        url = reverse('horizon:identity:projects:update_quotas',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.UpdateQuota.name)

        step = workflow.get_step("update_compute_quotas")
        self.assertEqual(step.action.initial['ram'], quota.get('ram').limit)
        self.assertEqual(step.action.initial['injected_files'],
                         quota.get('injected_files').limit)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<UpdateComputeQuota: update_compute_quotas>',
             '<UpdateVolumeQuota: update_volume_quotas>'])

        self.mock_get_disabled_quotas.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_get_tenant_quota_data.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)

    @test.create_mocks({
        api.nova: (('tenant_quota_update', 'nova_tenant_quota_update'),),
        api.cinder: (('tenant_quota_update', 'cinder_tenant_quota_update'),),
        quotas: ('get_tenant_quota_data',
                 'get_disabled_quotas',
                 'tenant_quota_usages',)})
    def _test_update_quotas_save(self, with_neutron=False):
        project = self.tenants.first()
        quota = self.quotas.first()
        quota_usages = self.quota_usages.first()

        # get/init
        self.mock_get_disabled_quotas.return_value = set()
        self.mock_get_tenant_quota_data.return_value = quota

        quota.metadata_items = 444
        quota.volumes = 444

        updated_quota = self._get_quota_info(quota)

        # handle
        expected_tenant_quota_usages = []
        self.mock_tenant_quota_usages.return_value = quota_usages
        expected_tenant_quota_usages.append(
            mock.call(test.IsHttpRequest(), tenant_id=project.id,
                      targets=tuple(quotas.NOVA_QUOTA_FIELDS)))
        self.mock_nova_tenant_quota_update.return_value = None
        expected_tenant_quota_usages.append(
            mock.call(test.IsHttpRequest(), tenant_id=project.id,
                      targets=tuple(quotas.CINDER_QUOTA_FIELDS)))
        self.mock_cinder_tenant_quota_update.return_value = None
        if with_neutron:
            self.mock_is_quotas_extension_supported.return_value = with_neutron
            expected_tenant_quota_usages.append(
                mock.call(test.IsHttpRequest(), tenant_id=project.id,
                          targets=tuple(quotas.NEUTRON_QUOTA_FIELDS)))
            self.mock_neutron_tenant_quota_update.return_value = None

        # submit form data
        workflow_data = {}
        workflow_data.update(updated_quota)
        url = reverse('horizon:identity:projects:update_quotas',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_get_disabled_quotas.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_get_tenant_quota_data.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        nova_updated_quota = {key: updated_quota[key] for key
                              in quotas.NOVA_QUOTA_FIELDS}
        self.mock_nova_tenant_quota_update.assert_called_once_with(
            test.IsHttpRequest(), project.id, **nova_updated_quota)

        cinder_updated_quota = {key: updated_quota[key] for key
                                in quotas.CINDER_QUOTA_FIELDS}
        self.mock_cinder_tenant_quota_update.assert_called_once_with(
            test.IsHttpRequest(), project.id, **cinder_updated_quota)
        if with_neutron:
            self.mock_is_quotas_extension_supported.assert_called_once_with(
                test.IsHttpRequest())
            neutron_updated_quota = {key: updated_quota[key] for key
                                     in quotas.NEUTRON_QUOTA_FIELDS}
            self.mock_neutron_tenant_quota_update.assert_called_once_with(
                test.IsHttpRequest(), self.tenant.id, **neutron_updated_quota)

        self.mock_tenant_quota_usages.assert_has_calls(
            expected_tenant_quota_usages)
        self.assertEqual(len(expected_tenant_quota_usages),
                         self.mock_tenant_quota_usages.call_count)

    def test_update_quotas_save(self):
        self._test_update_quotas_save()

    @test.create_mocks({
        api.neutron: ('is_quotas_extension_supported',
                      ('tenant_quota_update', 'neutron_tenant_quota_update'))
    })
    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_update_quotas_save_with_neutron(self):
        self._test_update_quotas_save(with_neutron=True)

    @test.create_mocks({
        quotas: ('get_tenant_quota_data',
                 'get_disabled_quotas',
                 'tenant_quota_usages',),
        api.cinder: (('tenant_quota_update', 'cinder_tenant_quota_update'),),
        api.nova: (('tenant_quota_update', 'nova_tenant_quota_update'),)})
    def test_update_quotas_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        quota_usages = self.quota_usages.first()

        # get/init
        self.mock_get_disabled_quotas.return_value = set()
        self.mock_get_tenant_quota_data.return_value = quota

        # update some fields
        quota[0].limit = 444
        quota[1].limit = -1

        updated_quota = self._get_quota_info(quota)

        # handle
        self.mock_tenant_quota_usages.return_value = quota_usages
        self.mock_nova_tenant_quota_update.side_effect = self.exceptions.nova
        # handle() of all steps are called even after one of handle() fails.
        self.mock_cinder_tenant_quota_update.return_value = None

        # submit form data
        url = reverse('horizon:identity:projects:update_quotas',
                      args=[self.tenant.id])
        res = self.client.post(url, updated_quota)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=2, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_get_disabled_quotas.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_get_tenant_quota_data.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.mock_tenant_quota_usages.assert_has_calls([
            mock.call(test.IsHttpRequest(), tenant_id=project.id,
                      targets=tuple(quotas.NOVA_QUOTA_FIELDS)),
            mock.call(test.IsHttpRequest(), tenant_id=project.id,
                      targets=tuple(quotas.CINDER_QUOTA_FIELDS)),
        ])
        self.assertEqual(2, self.mock_tenant_quota_usages.call_count)

        nova_updated_quota = {key: updated_quota[key]
                              for key in quotas.NOVA_QUOTA_FIELDS}
        self.mock_nova_tenant_quota_update.assert_called_once_with(
            test.IsHttpRequest(), project.id, **nova_updated_quota)
        # handle() of all steps are called even after one of handle() fails.
        cinder_updated_quota = {key: updated_quota[key] for key
                                in quotas.CINDER_QUOTA_FIELDS}
        self.mock_cinder_tenant_quota_update.assert_called_once_with(
            test.IsHttpRequest(), project.id, **cinder_updated_quota)


class UsageViewTests(test.BaseAdminViewTests):

    @override_settings(OVERVIEW_DAYS_RANGE=None)
    def test_usage_csv(self):
        self._test_usage_csv(nova_stu_enabled=True)

    def test_usage_csv_disabled(self):
        self._test_usage_csv(nova_stu_enabled=False)

    @override_settings(OVERVIEW_DAYS_RANGE=1)
    def test_usage_csv_1_day(self):
        self._test_usage_csv(nova_stu_enabled=True, overview_days_range=1)

    @test.create_mocks({api.nova: ('usage_get',
                                   'extension_supported')})
    def _test_usage_csv(self, nova_stu_enabled=True, overview_days_range=None):
        now = timezone.now()
        usage_obj = api.nova.NovaUsage(self.usages.first())
        self.mock_extension_supported.return_value = nova_stu_enabled
        if overview_days_range:
            start_day = now - datetime.timedelta(days=overview_days_range)
        else:
            start_day = datetime.date(now.year, now.month, 1)
        start = datetime.datetime(start_day.year, start_day.month,
                                  start_day.day, 0, 0, 0, 0)
        end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, 0)

        self.mock_usage_get.return_value = usage_obj

        project_id = self.tenants.first().id
        csv_url = reverse('horizon:identity:projects:usage',
                          args=[project_id]) + "?format=csv"
        res = self.client.get(csv_url)
        self.assertTemplateUsed(res, 'project/overview/usage.csv')

        self.assertIsInstance(res.context['usage'], usage.ProjectUsage)
        hdr = ('Instance Name,VCPUs,RAM (MB),Disk (GB),Usage (Hours),'
               'Age (Seconds),State')
        self.assertContains(res, '%s\r\n' % hdr)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_extension_supported, 2,
            mock.call('SimpleTenantUsage', test.IsHttpRequest()))
        if nova_stu_enabled:
            self.mock_usage_get.assert_called_once_with(test.IsHttpRequest(),
                                                        self.tenant.id,
                                                        start, end)
        else:
            self.mock_usage_get.assert_not_called()


class DetailProjectViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.keystone: ('tenant_get', 'domain_get'),
                        quotas: ('enabled_quotas',)})
    def test_detail_view(self):
        project = self.tenants.first()
        domain = self.domains.first()

        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = domain
        self.mock_enabled_quotas.return_value = ('instances',)

        res = self.client.get(PROJECT_DETAIL_URL, args=[project.id])

        # The first tab is overview, it is the one loaded without query param
        # in the url.
        self.assertTemplateUsed(res, 'identity/projects/_detail_overview.html')
        self.assertEqual(res.context['project'].name, project.name)
        self.assertEqual(res.context['project'].id, project.id)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('tenant_get',)})
    def test_detail_view_with_exception(self):
        project = self.tenants.first()

        self.mock_tenant_get.side_effect = self.exceptions.keystone

        res = self.client.get(PROJECT_DETAIL_URL, args=[project.id])

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)

    @test.create_mocks({api.keystone: ('tenant_get', 'domain_get'),
                        quotas: ('enabled_quotas',)})
    def test_detail_view_overview_tab(self):
        """Test the overview tab of the detail view .

        Test the overview tab using directly the url targeting the tab.
        """
        project = self.tenants.first()
        domain = self.domains.first()

        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = domain
        self.mock_enabled_quotas.return_value = ('instances',)

        # Url of the overview tab of the detail view
        url = PROJECT_DETAIL_URL % [project.id]
        detail_view = tabs.ProjectDetailTabs(self.request, project=project)
        overview_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("overview").get_id()
        )
        url += overview_tab_link

        res = self.client.get(url)

        self.assertTemplateUsed(res, 'identity/projects/_detail_overview.html')
        self.assertEqual(res.context['project'].name, project.name)
        self.assertEqual(res.context['project'].id, project.id)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())

    def _get_users_in_group(self, group_id):
        users_in_group = [membership["user_id"] for membership in
                          self.user_group_membership.list()
                          if membership["group_id"] == group_id]
        users = [user for user in self.users.list() if
                 user.id in users_in_group]
        return users

    def _project_user_roles(self, role_assignments):
        roles = {}
        for role_assignment in role_assignments:
            if hasattr(role_assignment, 'user'):
                roles[role_assignment.user['id']] = [
                    role_assignment.role["id"]]
        return roles

    def _project_group_roles(self, role_assignments):
        roles = {}
        for role_assignment in role_assignments:
            if hasattr(role_assignment, 'group'):
                roles[role_assignment.group['id']] = [
                    role_assignment.role["id"]]
        return roles

    @test.create_mocks({api.keystone: ('tenant_get',
                                       'domain_get',
                                       'user_list',
                                       'get_project_users_roles',
                                       'get_project_groups_roles',
                                       'role_list',
                                       'group_list'),
                        quotas: ('enabled_quotas',)})
    def test_detail_view_users_tab(self):
        project = self.tenants.first()
        domain = self.domains.first()
        users = self.users.filter(domain_id=project.domain_id)
        groups = self.groups.filter(domain_id=project.domain_id)
        role_assignments = self.role_assignments.filter(
            scope={'project': {'id': project.id}})
        # {user_id: [role_id1, role_id2]} as returned by the api
        project_users_roles = self._project_user_roles(role_assignments)
        # {group_id: [role_id1, role_id2]} as returned by the api
        project_groups_roles = self._project_group_roles(role_assignments)

        # Prepare mocks
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = domain
        self.mock_enabled_quotas.return_value = ('instances',)
        self.mock_role_list.return_value = self.roles.list()

        def _user_list_side_effect(request, group=None):
            if group:
                return self._get_users_in_group(group)
            return users
        self.mock_user_list.side_effect = _user_list_side_effect
        self.mock_group_list.return_value = groups
        self.mock_get_project_users_roles.return_value = project_users_roles
        self.mock_get_project_groups_roles.return_value = project_groups_roles

        # Get project details view on user tab
        url = PROJECT_DETAIL_URL % [project.id]
        detail_view = tabs.ProjectDetailTabs(self.request, group=project)
        users_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("users").get_id()
        )
        url += users_tab_link
        res = self.client.get(url)

        self.assertTemplateUsed(res, "horizon/common/_detail_table.html")

        # Check the content of the table
        users_expected = {
            '1': {'roles': ['admin'],
                  'roles_from_groups': [('_member_', 'group_one'), ], },
            '2': {'roles': ['_member_'],
                  'roles_from_groups': [], },
            '3': {'roles': ['_member_'],
                  'roles_from_groups': [('_member_', 'group_one'), ], },
            '4': {'roles': [],
                  'roles_from_groups': [('_member_', 'group_one'), ], }
        }

        users_id_observed = [user.id for user in
                             res.context["userstable_table"].data]
        self.assertItemsEqual(users_expected.keys(), users_id_observed)

        # Check the users groups and roles
        for user in res.context["userstable_table"].data:
            self.assertItemsEqual(users_expected[user.id]["roles"],
                                  user.roles)
            self.assertItemsEqual(users_expected[user.id]["roles_from_groups"],
                                  user.roles_from_groups)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())
        self.mock_role_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_get_project_users_roles.assert_called_once_with(
            test.IsHttpRequest(), project=project.id)
        self.mock_get_project_groups_roles.assert_called_once_with(
            test.IsHttpRequest(), project=project.id)
        calls = [mock.call(test.IsHttpRequest()),
                 mock.call(test.IsHttpRequest(), group="1"), ]

        self.mock_user_list.assert_has_calls(calls)

    @test.create_mocks({api.keystone: ("tenant_get",
                                       "domain_get",
                                       "role_list",),
                        quotas: ('enabled_quotas',)})
    def test_detail_view_users_tab_exception(self):
        project = self.tenants.first()
        domain = self.domains.first()

        # Prepare mocks
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = domain
        self.mock_enabled_quotas.return_value = ('instances',)
        self.mock_role_list.side_effect = self.exceptions.keystone

        # Get project details view on user tab
        url = reverse('horizon:identity:projects:detail', args=[project.id])
        detail_view = tabs.ProjectDetailTabs(self.request, group=project)
        users_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("users").get_id()
        )
        url += users_tab_link
        res = self.client.get(url)

        # Check the projects table is empty
        self.assertFalse(res.context["userstable_table"].data)
        # Check one error message is displayed
        self.assertMessageCount(res, error=1)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())
        self.mock_role_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ("tenant_get",
                                       "domain_get",
                                       "get_project_groups_roles",
                                       "role_list",
                                       "group_list"),
                        quotas: ('enabled_quotas',)})
    def test_detail_view_groups_tab(self):
        project = self.tenants.first()
        domain = self.domains.first()
        groups = self.groups.filter(domain_id=project.domain_id)
        role_assignments = self.role_assignments.filter(
            scope={'project': {'id': project.id}})
        # {group_id: [role_id1, role_id2]} as returned by the api
        project_groups_roles = self._project_group_roles(role_assignments)

        # Prepare mocks
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = domain
        self.mock_enabled_quotas.return_value = ('instances',)
        self.mock_get_project_groups_roles.return_value = project_groups_roles
        self.mock_group_list.return_value = groups
        self.mock_role_list.return_value = self.roles.list()

        # Get project details view on group tab
        url = reverse('horizon:identity:projects:detail', args=[project.id])
        detail_view = tabs.ProjectDetailTabs(self.request, group=project)
        groups_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("groups").get_id()
        )
        url += groups_tab_link

        res = self.client.get(url)

        # Check the template expected has been used
        self.assertTemplateUsed(res,
                                "horizon/common/_detail_table.html")

        # Check the table content
        groups_expected = {'1': ["_member_"], }
        groups_id_observed = [group.id for group in
                              res.context["groupstable_table"].data]

        # Check the group is displayed
        self.assertItemsEqual(groups_id_observed, groups_expected.keys())

        # Check the groups roles
        for group in res.context["groupstable_table"].data:
            self.assertEqual(groups_expected[group.id], group.roles)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())
        self.mock_role_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_get_project_groups_roles.assert_called_once_with(
            test.IsHttpRequest(), project=project.id)

    @test.create_mocks({api.keystone: ("tenant_get",
                                       "domain_get",
                                       "get_project_groups_roles"),
                        quotas: ('enabled_quotas',)})
    def test_detail_view_groups_tab_exception(self):
        project = self.tenants.first()
        domain = self.domains.first()

        # Prepare mocks
        self.mock_tenant_get.return_value = project
        self.mock_domain_get.return_value = domain
        self.mock_enabled_quotas.return_value = ('instances',)
        self.mock_get_project_groups_roles.side_effect = \
            self.exceptions.keystone

        # Get project details view on group tab
        url = reverse('horizon:identity:projects:detail', args=[project.id])
        detail_view = tabs.ProjectDetailTabs(self.request, group=project)
        groups_tab_link = "?%s=%s" % (
            detail_view.param_name,
            detail_view.get_tab("groups").get_id()
        )
        url += groups_tab_link
        res = self.client.get(url)

        # Check the projects table is empty
        self.assertFalse(res.context["groupstable_table"].data)
        # Check one error message is displayed
        self.assertMessageCount(res, error=1)

        self.mock_tenant_get.assert_called_once_with(test.IsHttpRequest(),
                                                     self.tenant.id)
        self.mock_domain_get.assert_called_once_with(test.IsHttpRequest(),
                                                     domain.id)
        self.mock_enabled_quotas.assert_called_once_with(test.IsHttpRequest())
        self.mock_get_project_groups_roles.assert_called_once_with(
            test.IsHttpRequest(), project=project.id)


@tag('selenium')
class SeleniumTests(test.SeleniumAdminTestCase, test.TestCase):
    @test.create_mocks({api.keystone: ('get_default_domain',
                                       'get_default_role',
                                       'user_list',
                                       'group_list',
                                       'role_list'),
                        api.base: ('is_service_enabled',),
                        api.cinder: ('is_volume_service_enabled',),
                        quotas: ('get_default_quota_data',)})
    def test_membership_list_loads_correctly(self):
        member_css_class = ".available_members"
        users = self.users.list()

        self.mock_is_service_enabled.return_value = False
        self.mock_is_volume_service_enabled.return_value = False
        self.mock_get_default_domain.return_value = self.domain
        self.mock_get_default_quota_data.return_value = self.quotas.first()
        self.mock_get_default_role.return_value = self.roles.first()
        self.mock_user_list.return_value = users
        self.mock_role_list.return_value = self.roles.list()
        self.mock_group_list.return_value = self.groups.list()

        self.selenium.get("%s%s" %
                          (self.live_server_url,
                           reverse('horizon:identity:projects:create')))

        members = self.selenium.find_element_by_css_selector(member_css_class)

        for user in users:
            self.assertIn(user.name, members.text)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_service_enabled, 2,
            mock.call(test.IsHttpRequest(), 'network'))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_volume_service_enabled, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_get_default_domain.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_get_default_quota_data.assert_called_once_with(
            test.IsHttpRequest())

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_default_role, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_user_list.assert_called_once_with(
            test.IsHttpRequest(), domain=self.domain.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_role_list, 2, mock.call(test.IsHttpRequest()))
        self.mock_group_list.assert_called_once_with(
            test.IsHttpRequest(), domain=self.domain.id)
