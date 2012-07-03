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

from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from horizon import api
from horizon import test

from .workflows import CreateProject, UpdateProject
from .views import QUOTA_FIELDS

INDEX_URL = reverse('horizon:syspanel:projects:index')


class TenantsViewTests(test.BaseAdminViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(api.keystone, 'tenant_list')
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True) \
                    .AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'syspanel/projects/index.html')
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
        for field in QUOTA_FIELDS:
            quota_data[field] = int(getattr(quota, field, None))
        return quota_data

    def _get_workflow_data(self, project, quota):
        project_info = self._get_workflow_fields(project)
        quota_data = self._get_quota_info(quota)
        project_info.update(quota_data)
        return project_info

    @test.create_stubs({api: ('tenant_quota_defaults',)})
    def test_add_project_get(self):
        quota = self.quotas.first()
        api.tenant_quota_defaults(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(quota)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/projects/create.html')

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name, CreateProject.name)

        step = workflow.get_step("createprojectinfoaction")
        self.assertEqual(step.action.initial['ram'], quota.ram)
        self.assertEqual(step.action.initial['injected_files'],
                         quota.injected_files)
        self.assertQuerysetEqual(workflow.steps,
                            ['<CreateProjectInfo: createprojectinfoaction>',
                             '<UpdateProjectQuota: update_quotas>'])

    @test.create_stubs({api.keystone: ('tenant_create',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_post(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
                    .AndReturn(project)
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **quota_data)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(project, quota)

        url = reverse('horizon:syspanel:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('tenant_quota_defaults',)})
    def test_add_project_quota_defaults_error(self):
        api.tenant_quota_defaults(IsA(http.HttpRequest), self.tenant.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/projects/create.html')
        self.assertContains(res, "Unable to retrieve default quota values")

    @test.create_stubs({api.keystone: ('tenant_create',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_tenant_create_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        project_details = self._get_project_info(project)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(project, quota)

        url = reverse('horizon:syspanel:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.keystone: ('tenant_create',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_quota_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
                    .AndReturn(project)
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **quota_data) \
                                    .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(project, quota)

        url = reverse('horizon:syspanel:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_add_project_missing_field_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        workflow_data = self._get_workflow_data(project, quota)
        workflow_data["name"] = ""

        url = reverse('horizon:syspanel:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertContains(res, "field is required")


class UpdateProjectWorkflowTests(test.BaseAdminViewTests):
    def _get_quota_info(self, quota):
        quota_data = {}
        for field in QUOTA_FIELDS:
            quota_data[field] = int(getattr(quota, field, None))
        return quota_data

    @test.create_stubs({api: ('tenant_get',
                              'tenant_quota_get',)})
    def test_update_project_get(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        api.tenant_get(IsA(http.HttpRequest), self.tenant.id, admin=True) \
            .AndReturn(project)
        api.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(quota)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/projects/update.html')

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name, UpdateProject.name)

        step = workflow.get_step("update_info")
        self.assertEqual(step.action.initial['ram'], quota.ram)
        self.assertEqual(step.action.initial['injected_files'],
                         quota.injected_files)
        self.assertEqual(step.action.initial['name'], project.name)
        self.assertEqual(step.action.initial['description'],
                         project.description)
        self.assertQuerysetEqual(workflow.steps,
                            ['<UpdateProjectInfo: update_info>',
                             '<UpdateProjectQuota: update_quotas>'])

    @test.create_stubs({api: ('tenant_get',
                              'tenant_quota_get',
                              'tenant_update',
                              'tenant_quota_update',)})
    def test_update_project_post(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        api.tenant_get(IsA(http.HttpRequest), project.id, admin=True) \
            .AndReturn(project)
        api.tenant_quota_get(IsA(http.HttpRequest), project.id) \
            .AndReturn(quota)

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

        api.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndReturn(project)
        api.tenant_quota_update(IsA(http.HttpRequest),
                                project.id,
                                **updated_quota)

        self.mox.ReplayAll()

        # submit form data
        workflow_data = {"name": project._info["name"],
                         "id": project.id,
                         "description": project._info["description"],
                         "enabled": project.enabled}
        workflow_data.update(updated_quota)
        url = reverse('horizon:syspanel:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('tenant_get',
                              'tenant_quota_get',)})
    def test_update_project_get_error(self):
        project = self.tenants.first()

        api.tenant_get(IsA(http.HttpRequest), self.tenant.id, admin=True) \
            .AndReturn(project)
        api.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('tenant_get',
                              'tenant_quota_get',
                              'tenant_update',)})
    def test_update_project_tenant_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        api.tenant_get(IsA(http.HttpRequest), project.id, admin=True) \
            .AndReturn(project)
        api.tenant_quota_get(IsA(http.HttpRequest), project.id) \
            .AndReturn(quota)

        # update some fields
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = '444'
        quota.volumes = '444'

        updated_project = {"tenant_name": project._info["name"],
                           "tenant_id": project.id,
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        api.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        # submit form data
        workflow_data = {"name": project._info["name"],
                         "id": project.id,
                         "description": project._info["description"],
                         "enabled": project.enabled}
        workflow_data.update(updated_quota)
        url = reverse('horizon:syspanel:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('tenant_get',
                              'tenant_quota_get',
                              'tenant_update',
                              'tenant_quota_update',)})
    def test_update_project_quota_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()

        # first set of calls for 'get' because the url takes an arg
        api.tenant_get(IsA(http.HttpRequest), project.id, admin=True) \
            .AndReturn(project)
        api.tenant_quota_get(IsA(http.HttpRequest), project.id) \
            .AndReturn(quota)

        # update some fields
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = '444'
        quota.volumes = '444'

        updated_project = {"tenant_name": project._info["name"],
                           "tenant_id": project.id,
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        api.tenant_update(IsA(http.HttpRequest), **updated_project) \
            .AndReturn(project)
        api.tenant_quota_update(IsA(http.HttpRequest),
                                project.id,
                                **updated_quota) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        # submit form data
        workflow_data = {"name": updated_project["tenant_name"],
                         "id": project.id,
                         "description": updated_project["description"],
                         "enabled": project.enabled}
        workflow_data.update(updated_quota)
        url = reverse('horizon:syspanel:projects:update',
                      args=[self.tenant.id])
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
