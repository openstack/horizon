# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django import http
from django.core.urlresolvers import reverse

from mox import IsA

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas
from .workflows import CreateProject, UpdateProject

INDEX_URL = reverse('horizon:admin:projects:index')


class TenantsViewTests(test.BaseAdminViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(api.keystone, 'tenant_list')
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True) \
                    .AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants.list())


class CreateProjectWorkflowTests(test.BaseAdminViewTests):
    def _get_project_info(self, project):
        project_info = {"tenant_name": project.name,
                        "description": project.description,
                        "enabled": project.enabled}
        return project_info

    def _get_workflow_fields(self, project):
        project_info = {"name": project.name,
                        "description": project.description,
                        "enabled": project.enabled}
        return project_info

    def _get_quota_info(self, quota):
        quota_data = {}
        for field in quotas.QUOTA_FIELDS:
            quota_data[field] = int(quota.get(field).limit)
        return quota_data

    def _get_workflow_data(self, project, quota):
        project_info = self._get_workflow_fields(project)
        quota_data = self._get_quota_info(quota)
        project_info.update(quota_data)
        return project_info

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'user_list',
                                       'role_list'),
                        quotas: ('get_default_quota_data',)})
    def test_add_project_get(self):
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        # init
        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/projects/create.html')

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name, CreateProject.name)

        step = workflow.get_step("createprojectinfoaction")
        self.assertEqual(step.action.initial['ram'], quota.get('ram').limit)
        self.assertEqual(step.action.initial['injected_files'],
                         quota.get('injected_files').limit)
        self.assertQuerysetEqual(workflow.steps,
                            ['<CreateProjectInfo: createprojectinfoaction>',
                             '<UpdateProjectMembers: update_members>',
                             '<UpdateProjectQuota: update_quotas>'])

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'add_tenant_user_role',
                                       'tenant_create',
                                       'user_list',
                                       'role_list'),
                        quotas: ('get_default_quota_data',),
                        api.cinder: ('tenant_quota_update',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_post(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # init
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
                    .AndReturn(project)

        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}
        for role in roles:
            if "role_" + role.id in workflow_data:
                ulist = workflow_data["role_" + role.id]
                for user_id in ulist:
                    api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                                      tenant_id=self.tenant.id,
                                                      user_id=user_id,
                                                      role_id=role.id)

        nova_updated_quota = dict([(key, quota_data[key]) for key in
                                   quotas.NOVA_QUOTA_FIELDS])
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **nova_updated_quota)
        cinder_updated_quota = dict([(key, quota_data[key]) for key in
                                   quotas.CINDER_QUOTA_FIELDS])
        api.cinder.tenant_quota_update(IsA(http.HttpRequest),
                                       project.id,
                                       **cinder_updated_quota)

        self.mox.ReplayAll()

        workflow_data.update(self._get_workflow_data(project, quota))

        url = reverse('horizon:admin:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('user_list',
                                       'role_list',
                                       'get_default_role'),
                        quotas: ('get_default_quota_data',)})
    def test_add_project_quota_defaults_error(self):
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # init
        quotas.get_default_quota_data(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/projects/create.html')
        self.assertContains(res, "Unable to retrieve default quota values")

    @test.create_stubs({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'get_default_role'),
                        quotas: ('get_default_quota_data',)})
    def test_add_project_tenant_create_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # init
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        project_details = self._get_project_info(project)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(project, quota)

        url = reverse('horizon:admin:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'get_default_role',
                                       'add_tenant_user_role'),
                        quotas: ('get_default_quota_data',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_quota_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # init
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
            .AndReturn(project)

        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}
        for role in roles:
            if "role_" + role.id in workflow_data:
                ulist = workflow_data["role_" + role.id]
                for user_id in ulist:
                    api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                                      tenant_id=self.tenant.id,
                                                      user_id=user_id,
                                                      role_id=role.id)

        nova_updated_quota = dict([(key, quota_data[key]) for key in
                                   quotas.NOVA_QUOTA_FIELDS])
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **nova_updated_quota) \
           .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        workflow_data.update(self._get_workflow_data(project, quota))

        url = reverse('horizon:admin:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'get_default_role',
                                       'add_tenant_user_role'),
                        quotas: ('get_default_quota_data',),
                        api.cinder: ('tenant_quota_update',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_user_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # init
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
                    .AndReturn(project)

        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}
        for role in roles:
            if "role_" + role.id in workflow_data:
                ulist = workflow_data["role_" + role.id]
                for user_id in ulist:
                    api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                                      tenant_id=self.tenant.id,
                                                      user_id=user_id,
                                                      role_id=role.id) \
                       .AndRaise(self.exceptions.keystone)
                    break
            break

        nova_updated_quota = dict([(key, quota_data[key]) for key in
                                   quotas.NOVA_QUOTA_FIELDS])
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **nova_updated_quota)

        cinder_updated_quota = dict([(key, quota_data[key]) for key in
                                    quotas.CINDER_QUOTA_FIELDS])
        api.cinder.tenant_quota_update(IsA(http.HttpRequest),
                                       project.id,
                                       **cinder_updated_quota)

        self.mox.ReplayAll()

        workflow_data.update(self._get_workflow_data(project, quota))

        url = reverse('horizon:admin:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('user_list',
                                       'role_list',
                                       'get_default_role'),
                        quotas: ('get_default_quota_data',)})
    def test_add_project_missing_field_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # init
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(project, quota)
        workflow_data["name"] = ""

        url = reverse('horizon:admin:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertContains(res, "field is required")


class UpdateProjectWorkflowTests(test.BaseAdminViewTests):
    def _get_quota_info(self, quota):
        quota_data = {}
        for field in quotas.QUOTA_FIELDS:
            quota_data[field] = int(quota.get(field).limit)
        return quota_data

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'roles_for_user',
                                       'tenant_get',
                                       'user_list',
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',)})
    def test_update_project_get(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        api.keystone.tenant_get(IsA(http.HttpRequest),
                                self.tenant.id, admin=True) \
            .AndReturn(project)
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        for user in users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/projects/update.html')

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name, UpdateProject.name)

        step = workflow.get_step("update_info")
        self.assertEqual(step.action.initial['ram'], quota.get('ram').limit)
        self.assertEqual(step.action.initial['injected_files'],
                         quota.get('injected_files').limit)
        self.assertEqual(step.action.initial['name'], project.name)
        self.assertEqual(step.action.initial['description'],
                         project.description)
        self.assertQuerysetEqual(workflow.steps,
                            ['<UpdateProjectInfo: update_info>',
                             '<UpdateProjectMembers: update_members>',
                             '<UpdateProjectQuota: update_quotas>'])

    @test.create_stubs({api.keystone: ('tenant_get',
                                       'tenant_update',
                                       'get_default_role',
                                       'roles_for_user',
                                       'remove_tenant_user_role',
                                       'add_tenant_user_role',
                                       'user_list',
                                       'role_list'),
                        api.nova: ('tenant_quota_update',),
                        api.cinder: ('tenant_quota_update',),
                        quotas: ('get_tenant_quota_data',)})
    def test_update_project_save(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest),
                                self.tenant.id, admin=True) \
            .AndReturn(project)
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}
        for user in users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)

        workflow_data["role_1"] = ['3']  # admin role
        workflow_data["role_2"] = ['2']  # member role

        # update some fields
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = 444
        quota.volumes = 444

        updated_project = {"tenant_name": project._info["name"],
                           "tenant_id": project.id,
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndReturn(project)

        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)
        api.keystone.user_list(IsA(http.HttpRequest),
                               tenant_id=self.tenant.id).AndReturn(users)

        # admin user - try to remove all roles on current project, warning
        api.keystone.roles_for_user(IsA(http.HttpRequest), '1',
                                    self.tenant.id) \
                           .AndReturn(roles)

        # member user 1 - has role 1, will remove it
        api.keystone.roles_for_user(IsA(http.HttpRequest), '2',
                                    self.tenant.id) \
                           .AndReturn((roles[0],))
        # remove role 1
        api.keystone.remove_tenant_user_role(IsA(http.HttpRequest),
                                             tenant_id=self.tenant.id,
                                             user_id='2',
                                             role_id='1')
        # add role 2
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          tenant_id=self.tenant.id,
                                          user_id='2',
                                          role_id='2')

        # member user 3 - has role 2
        api.keystone.roles_for_user(IsA(http.HttpRequest), '3',
                                    self.tenant.id) \
                           .AndReturn((roles[1],))
        # remove role 2
        api.keystone.remove_tenant_user_role(IsA(http.HttpRequest),
                                             tenant_id=self.tenant.id,
                                             user_id='3',
                                             role_id='2')
        # add role 1
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          tenant_id=self.tenant.id,
                                          user_id='3',
                                          role_id='1')

        nova_updated_quota = dict([(key, updated_quota[key]) for key in
                                   quotas.NOVA_QUOTA_FIELDS])
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **nova_updated_quota)

        cinder_updated_quota = dict([(key, updated_quota[key]) for key in
                                   quotas.CINDER_QUOTA_FIELDS])
        api.cinder.tenant_quota_update(IsA(http.HttpRequest),
                                       project.id,
                                       **cinder_updated_quota)
        self.mox.ReplayAll()

        # submit form data
        project_data = {"name": project._info["name"],
                         "id": project.id,
                         "description": project._info["description"],
                         "enabled": project.enabled}
        workflow_data.update(project_data)
        workflow_data.update(updated_quota)
        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_get',)})
    def test_update_project_get_error(self):

        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_get',
                                       'tenant_update',
                                       'get_default_role',
                                       'roles_for_user',
                                       'remove_tenant_user',
                                       'add_tenant_user_role',
                                       'user_list',
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',),
                        api.nova: ('tenant_quota_update',)})
    def test_update_project_tenant_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}
        for user in users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)
            role_ids = [role.id for role in roles]
            if role_ids:
                workflow_data.setdefault("role_" + role_ids[0], []) \
                             .append(user.id)

        # update some fields
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = 444
        quota.volumes = 444

        updated_project = {"tenant_name": project._info["name"],
                           "tenant_id": project.id,
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        # submit form data
        project_data = {"name": project._info["name"],
                         "id": project.id,
                         "description": project._info["description"],
                         "enabled": project.enabled}
        workflow_data.update(project_data)
        workflow_data.update(updated_quota)
        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_get',
                                       'tenant_update',
                                       'get_default_role',
                                       'roles_for_user',
                                       'remove_tenant_user_role',
                                       'add_tenant_user_role',
                                       'user_list',
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',),
                        api.nova: ('tenant_quota_update',)})
    def test_update_project_quota_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}

        for user in users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)

        workflow_data["role_1"] = ['1', '3']  # admin role
        workflow_data["role_2"] = ['1', '2', '3']  # member role

        # update some fields
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota[0].limit = 444
        quota[1].limit = -1

        updated_project = {"tenant_name": project._info["name"],
                           "tenant_id": project.id,
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndReturn(project)

        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)
        api.keystone.user_list(IsA(http.HttpRequest),
                               tenant_id=self.tenant.id).AndReturn(users)

        # admin user - try to remove all roles on current project, warning
        api.keystone.roles_for_user(IsA(http.HttpRequest), '1',
                                    self.tenant.id) \
                           .AndReturn(roles)

        # member user 1 - has role 1, will remove it
        api.keystone.roles_for_user(IsA(http.HttpRequest), '2',
                                    self.tenant.id) \
                           .AndReturn((roles[1],))

        # member user 3 - has role 2
        api.keystone.roles_for_user(IsA(http.HttpRequest), '3',
                                    self.tenant.id) \
                           .AndReturn((roles[0],))
        # add role 2
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          tenant_id=self.tenant.id,
                                          user_id='3',
                                          role_id='2')

        nova_updated_quota = dict([(key, updated_quota[key]) for key in
                                   quotas.NOVA_QUOTA_FIELDS])
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **nova_updated_quota) \
                            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        # submit form data
        project_data = {"name": project._info["name"],
                         "id": project.id,
                         "description": project._info["description"],
                         "enabled": project.enabled}
        workflow_data.update(project_data)
        workflow_data.update(updated_quota)
        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_get',
                                       'tenant_update',
                                       'get_default_role',
                                       'roles_for_user',
                                       'remove_tenant_user_role',
                                       'add_tenant_user_role',
                                       'user_list',
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',)})
    def test_update_project_member_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        users = self.users.list()
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest)).AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        workflow_data = {}
        for user in users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)
        workflow_data["role_1"] = ['1', '3']  # admin role
        workflow_data["role_2"] = ['1', '2', '3']  # member role

        # update some fields
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = 444
        quota.volumes = 444

        updated_project = {"tenant_name": project._info["name"],
                           "tenant_id": project.id,
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # contribute
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndReturn(project)

        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)
        api.keystone.user_list(IsA(http.HttpRequest),
                               tenant_id=self.tenant.id).AndReturn(users)

        # admin user - try to remove all roles on current project, warning
        api.keystone.roles_for_user(IsA(http.HttpRequest), '1',
                                    self.tenant.id) \
                           .AndReturn(roles)

        # member user 1 - has role 1, will remove it
        api.keystone.roles_for_user(IsA(http.HttpRequest), '2',
                                    self.tenant.id) \
                           .AndReturn((roles[1],))

        # member user 3 - has role 2
        api.keystone.roles_for_user(IsA(http.HttpRequest), '3',
                                    self.tenant.id) \
                           .AndReturn((roles[0],))
        # add role 2
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          tenant_id=self.tenant.id,
                                          user_id='3',
                                          role_id='2')\
                                 .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        # submit form data
        project_data = {"name": project._info["name"],
                         "id": project.id,
                         "description": project._info["description"],
                         "enabled": project.enabled}
        workflow_data.update(project_data)
        workflow_data.update(updated_quota)
        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('get_default_role', 'tenant_get'),
                        quotas: ('get_tenant_quota_data',)})
    def test_update_project_when_default_role_does_not_exist(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .AndReturn(None)  # Default role doesn't exist
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])

        try:
            # Avoid the log message in the test output when the workflow's
            # step action cannot be instantiated
            logging.disable(logging.ERROR)
            with self.assertRaises(exceptions.NotFound):
                res = self.client.get(url)
        finally:
            logging.disable(logging.NOTSET)
