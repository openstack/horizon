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

from django.core.urlresolvers import reverse  # noqa
from django import http
from django.test.utils import override_settings  # noqa

from mox import IsA  # noqa

from horizon import exceptions
from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.admin.projects import workflows


INDEX_URL = reverse('horizon:admin:projects:index')
USER_ROLE_PREFIX = workflows.PROJECT_GROUP_MEMBER_SLUG + "_role_"
GROUP_ROLE_PREFIX = workflows.PROJECT_USER_MEMBER_SLUG + "_role_"


@test.create_stubs({api.keystone: ('tenant_list',)})
class TenantsViewTests(test.BaseAdminViewTests):
    def test_index(self):
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=True) \
            .AndReturn([self.tenants.list(), False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.tenants.list())

    @test.create_stubs({api.keystone: ('tenant_list', )})
    def test_index_with_domain_context(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        domain_tenants = [tenant for tenant in self.tenants.list()
                          if tenant.domain_id == domain.id]
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=domain.id) \
                    .AndReturn(domain_tenants)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/projects/index.html')
        self.assertItemsEqual(res.context['table'].data, domain_tenants)
        self.assertContains(res, "<em>test_domain:</em>")


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

    def _get_workflow_data(self, project, quota):
        project_info = self._get_workflow_fields(project)
        quota_data = self._get_quota_info(quota)
        project_info.update(quota_data)
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

    @test.create_stubs({api.keystone: ('get_default_domain',
                                       'get_default_role',
                                       'user_list',
                                       'group_list',
                                       'role_list'),
                        api.base: ('is_service_enabled',),
                        api.neutron: ('is_extension_supported',),
                        quotas: ('get_default_quota_data',)})
    def test_add_project_get(self):
        quota = self.quotas.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
            .MultipleTimes().AndReturn(True)
        api.keystone.get_default_domain(IsA(http.HttpRequest)) \
            .AndReturn(default_domain)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'security-group').AndReturn(True)
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)
        api.keystone.role_list(IsA(http.HttpRequest)).AndReturn(roles)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertContains(res, '<input type="hidden" name="subnet" '
                            'id="id_subnet" />', html=True)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.CreateProject.name)

        step = workflow.get_step("createprojectinfoaction")
        self.assertEqual(step.action.initial['ram'], quota.get('ram').limit)
        self.assertEqual(step.action.initial['injected_files'],
                         quota.get('injected_files').limit)
        self.assertQuerysetEqual(workflow.steps,
                            ['<CreateProjectInfo: createprojectinfoaction>',
                             '<UpdateProjectMembers: update_members>',
                             '<UpdateProjectGroups: update_group_members>',
                             '<UpdateProjectQuota: update_quotas>'])

    def test_add_project_get_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_get()

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'user_list',
                                       'group_list',
                                       'role_list',
                                       'domain_get'),
                        api.neutron: ('is_extension_supported',
                                      'tenant_quota_get'),
                        quotas: ('get_default_quota_data',)})
    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_add_project_get_with_neutron(self):
        quota = self.quotas.first()
        neutron_quotas = self.neutron_quotas.first()

        quotas.get_default_quota_data(IsA(http.HttpRequest)) \
            .AndReturn(quota)
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
            .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'security-group').AndReturn(True)
        api.neutron.tenant_quota_get(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(neutron_quotas)
        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.roles.first())
        api.keystone.user_list(IsA(http.HttpRequest), domain=None) \
            .AndReturn(self.users.list())
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .AndReturn(self.roles.list())
        api.keystone.group_list(IsA(http.HttpRequest), domain=None) \
            .AndReturn(self.groups.list())
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .AndReturn(self.roles.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:projects:create'))

        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertContains(res, '<input name="subnet" id="id_subnet" '
                            'value="10" type="text" />', html=True)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.CreateProject.name)

        step = workflow.get_step("createprojectinfoaction")
        self.assertEqual(step.action.initial['ram'], quota.get('ram').limit)
        self.assertEqual(step.action.initial['subnet'],
                         neutron_quotas.get('subnet').limit)

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'add_tenant_user_role',
                                       'tenant_create',
                                       'user_list',
                                       'group_list',
                                       'role_list',
                                       'domain_get'),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas'),
                        api.cinder: ('tenant_quota_update',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_post(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)

        # handle
        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
                    .AndReturn(project)

        workflow_data = {}
        for role in roles:
            if USER_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[USER_ROLE_PREFIX + role.id]
                for user_id in ulist:
                    api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                                      project=self.tenant.id,
                                                      user=user_id,
                                                      role=role.id)
        for role in roles:
            if GROUP_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[GROUP_ROLE_PREFIX + role.id]
                for group_id in ulist:
                    api.keystone.add_group_role(IsA(http.HttpRequest),
                                                role=role.id,
                                                group=group_id,
                                                project=self.tenant.id)

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

    def test_add_project_post_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_post()

    @test.create_stubs({api.neutron: ('is_extension_supported',
                                      'tenant_quota_update')})
    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_add_project_post_with_neutron(self):
        quota_data = self.neutron_quotas.first()
        neutron_updated_quota = dict([(key, quota_data.get(key).limit)
                                      for key in quotas.NEUTRON_QUOTA_FIELDS])

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'security-group').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
            .MultipleTimes().AndReturn(True)
        api.neutron.tenant_quota_update(IsA(http.HttpRequest),
                                        self.tenant.id,
                                        **neutron_updated_quota)
        self.test_add_project_post()

    @test.create_stubs({api.keystone: ('user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role'),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas')})
    def test_add_project_quota_defaults_error(self):
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        api.keystone.get_default_domain(IsA(http.HttpRequest)) \
            .AndReturn(default_domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertContains(res, "Unable to retrieve default quota values")

    def test_add_project_quota_defaults_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_quota_defaults_error()

    @test.create_stubs({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role'),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas')})
    def test_add_project_tenant_create_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        api.keystone.get_default_domain(IsA(http.HttpRequest)) \
            .AndReturn(default_domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)

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

    def test_add_project_tenant_create_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_tenant_create_error()

    @test.create_stubs({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role',
                                       'add_tenant_user_role'),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas'),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_quota_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        api.keystone.get_default_domain(IsA(http.HttpRequest)) \
            .AndReturn(default_domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)

        # handle
        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
            .AndReturn(project)

        workflow_data = {}
        for role in roles:
            if USER_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[USER_ROLE_PREFIX + role.id]
                for user_id in ulist:
                    api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                                      project=self.tenant.id,
                                                      user=user_id,
                                                      role=role.id)
        for role in roles:
            if GROUP_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[GROUP_ROLE_PREFIX + role.id]
                for group_id in ulist:
                    api.keystone.add_group_role(IsA(http.HttpRequest),
                                                role=role.id,
                                                group=group_id,
                                                project=self.tenant.id)

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

    def test_add_project_quota_update_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_quota_update_error()

    @test.create_stubs({api.keystone: ('tenant_create',
                                       'user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role',
                                       'add_tenant_user_role'),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas'),
                        api.cinder: ('tenant_quota_update',),
                        api.nova: ('tenant_quota_update',)})
    def test_add_project_user_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        api.keystone.get_default_domain(IsA(http.HttpRequest)) \
            .AndReturn(default_domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)

        # handle
        project_details = self._get_project_info(project)
        quota_data = self._get_quota_info(quota)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
            .AndReturn(project)

        workflow_data = {}
        for role in roles:
            if USER_ROLE_PREFIX + role.id in workflow_data:
                ulist = workflow_data[USER_ROLE_PREFIX + role.id]
                for user_id in ulist:
                    api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                                      project=self.tenant.id,
                                                      user=user_id,
                                                      role=role.id) \
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

    def test_add_project_user_update_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_user_update_error()

    @test.create_stubs({api.keystone: ('user_list',
                                       'role_list',
                                       'group_list',
                                       'get_default_domain',
                                       'get_default_role'),
                        quotas: ('get_default_quota_data',
                                 'get_disabled_quotas')})
    def test_add_project_missing_field_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        default_domain = self._get_default_domain()
        domain_id = default_domain.id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # init
        api.keystone.get_default_domain(IsA(http.HttpRequest)) \
            .AndReturn(default_domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_default_quota_data(IsA(http.HttpRequest)).AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(project, quota)
        workflow_data["name"] = ""

        url = reverse('horizon:admin:projects:create')
        res = self.client.post(url, workflow_data)

        self.assertContains(res, "field is required")

    def test_add_project_missing_field_error_domain(self):
        domain = self.domains.get(id="1")
        self.setSessionValues(domain_context=domain.id,
                              domain_context_name=domain.name)
        self.test_add_project_missing_field_error()


class UpdateProjectWorkflowTests(test.BaseAdminViewTests):
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

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'roles_for_user',
                                       'tenant_get',
                                       'domain_get',
                                       'user_list',
                                       'roles_for_group',
                                       'group_list',
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas')})
    def test_update_project_get(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()
        proj_users = self._get_proj_users(project.id)

        api.keystone.tenant_get(IsA(http.HttpRequest),
                                self.tenant.id, admin=True) \
            .AndReturn(project)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(self.domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)
        api.keystone.user_list(IsA(http.HttpRequest),
                               project=self.tenant.id).AndReturn(proj_users)
        for user in proj_users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)

        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         project=self.tenant.id) \
                .AndReturn(roles)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:projects:update',
                      args=[self.tenant.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.UpdateProject.name)

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
                             '<UpdateProjectGroups: update_group_members>',
                             '<UpdateProjectQuota: update_quotas>'])

    @test.create_stubs({api.keystone: ('tenant_get',
                                       'domain_get',
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
                                       'role_list'),
                        api.nova: ('tenant_quota_update',),
                        api.cinder: ('tenant_quota_update',),
                        quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas')})
    def test_update_project_save(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        proj_users = self._get_proj_users(project.id)
        groups = self._get_all_groups(domain_id)
        proj_groups = self._get_proj_groups(project.id)
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest),
                                self.tenant.id, admin=True) \
            .AndReturn(project)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(self.domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)
        api.keystone.user_list(IsA(http.HttpRequest),
                               project=self.tenant.id).AndReturn(proj_users)
        workflow_data = {}
        for user in proj_users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)
        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         project=self.tenant.id) \
                .AndReturn(roles)

        workflow_data[USER_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[USER_ROLE_PREFIX + "2"] = ['2']  # member role
        # Group assignment form  data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['2']  # member role

        # update some fields
        project._info["domain_id"] = domain_id
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = 444
        quota.volumes = 444

        updated_project = {"name": project._info["name"],
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest),
                                   project.id,
                                   **updated_project) \
            .AndReturn(project)

        api.keystone.user_list(IsA(http.HttpRequest),
                               project=self.tenant.id).AndReturn(proj_users)

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
                                             project=self.tenant.id,
                                             user='2',
                                             role='1')
        # add role 2
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          project=self.tenant.id,
                                          user='2',
                                          role='2')

        # member user 3 - has role 2
        api.keystone.roles_for_user(IsA(http.HttpRequest), '3',
                                    self.tenant.id) \
                           .AndReturn((roles[1],))
        # remove role 2
        api.keystone.remove_tenant_user_role(IsA(http.HttpRequest),
                                             project=self.tenant.id,
                                             user='3',
                                             role='2')
        # add role 1
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          project=self.tenant.id,
                                          user='3',
                                          role='1')

        # Group assignments
        api.keystone.group_list(IsA(http.HttpRequest),
                                domain=domain_id,
                                project=self.tenant.id).AndReturn(proj_groups)

        # admin group - try to remove all roles on current project
        api.keystone.roles_for_group(IsA(http.HttpRequest),
                                     group='1',
                                     project=self.tenant.id) \
                           .AndReturn(roles)
        for role in roles:
            api.keystone.remove_group_role(IsA(http.HttpRequest),
                                           role=role.id,
                                           group='1',
                                           project=self.tenant.id)

        # member group 1 - has role 1, will remove it
        api.keystone.roles_for_group(IsA(http.HttpRequest),
                                     group='2',
                                     project=self.tenant.id) \
                           .AndReturn((roles[0],))
        # remove role 1
        api.keystone.remove_group_role(IsA(http.HttpRequest),
                                       role='1',
                                       group='2',
                                       project=self.tenant.id)
        # add role 2
        api.keystone.add_group_role(IsA(http.HttpRequest),
                                    role='2',
                                    group='2',
                                    project=self.tenant.id)

        # member group 3 - has role 2
        api.keystone.roles_for_group(IsA(http.HttpRequest),
                                     group='3',
                                     project=self.tenant.id) \
                           .AndReturn((roles[1],))
        # remove role 2
        api.keystone.remove_group_role(IsA(http.HttpRequest),
                                       role='2',
                                       group='3',
                                       project=self.tenant.id)
        # add role 1
        api.keystone.add_group_role(IsA(http.HttpRequest),
                                    role='1',
                                    group='3',
                                    project=self.tenant.id)

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
        project_data = {"domain_id": project._info["domain_id"],
                        "name": project._info["name"],
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

    @test.create_stubs({api.neutron: ('is_extension_supported',
                                      'tenant_quota_get',
                                      'tenant_quota_update')})
    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_update_project_save_with_neutron(self):
        quota_data = self.neutron_quotas.first()
        neutron_updated_quota = dict([(key, quota_data.get(key).limit)
                                      for key in quotas.NEUTRON_QUOTA_FIELDS])

        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
            .MultipleTimes().AndReturn(True)
        api.neutron.tenant_quota_get(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota_data)
        api.neutron.tenant_quota_update(IsA(http.HttpRequest),
                                        self.tenant.id,
                                        **neutron_updated_quota)
        self.test_update_project_save()

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
                                       'domain_get',
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
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas'),
                        api.nova: ('tenant_quota_update',)})
    def test_update_project_tenant_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()
        proj_users = self._get_proj_users(project.id)

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(self.domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)
        api.keystone.user_list(IsA(http.HttpRequest),
                               project=self.tenant.id).AndReturn(proj_users)

        workflow_data = {}
        for user in proj_users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)
            role_ids = [role.id for role in roles]
            if role_ids:
                workflow_data.setdefault(USER_ROLE_PREFIX + role_ids[0], []) \
                             .append(user.id)

        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         project=self.tenant.id) \
                .AndReturn(roles)
            role_ids = [role.id for role in roles]
            if role_ids:
                workflow_data.setdefault(GROUP_ROLE_PREFIX + role_ids[0], []) \
                             .append(group.id)

        # update some fields
        project._info["domain_id"] = domain_id
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = 444
        quota.volumes = 444

        updated_project = {"name": project._info["name"],
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest),
                                   project.id,
                                   **updated_project) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        # submit form data
        project_data = {"domain_id": project._info["domain_id"],
                        "name": project._info["name"],
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
                                       'domain_get',
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
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas'),
                        api.nova: ('tenant_quota_update',)})
    def test_update_project_quota_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        proj_users = self._get_proj_users(project.id)
        groups = self._get_all_groups(domain_id)
        proj_groups = self._get_proj_groups(project.id)
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(self.domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)
        api.keystone.user_list(IsA(http.HttpRequest),
                       project=self.tenant.id).AndReturn(proj_users)

        workflow_data = {}

        for user in proj_users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)

        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         project=self.tenant.id) \
                .AndReturn(roles)

        workflow_data[USER_ROLE_PREFIX + "1"] = ['1', '3']  # admin role
        workflow_data[USER_ROLE_PREFIX + "2"] = ['1', '2', '3']  # member role
        # Group role assignment data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['1', '3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['1', '2', '3']  # member role

        # update some fields
        project._info["domain_id"] = domain_id
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota[0].limit = 444
        quota[1].limit = -1

        updated_project = {"name": project._info["name"],
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest),
                                   project.id,
                                   **updated_project) \
            .AndReturn(project)

        api.keystone.user_list(IsA(http.HttpRequest),
                               project=self.tenant.id).AndReturn(proj_users)

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
                                          project=self.tenant.id,
                                          user='3',
                                          role='2')

        # Group assignment
        api.keystone.group_list(IsA(http.HttpRequest),
                                domain=domain_id,
                                project=self.tenant.id).AndReturn(proj_groups)

        # admin group 1- try to remove all roles on current project
        api.keystone.roles_for_group(IsA(http.HttpRequest),
                                     group='1',
                                     project=self.tenant.id) \
                           .AndReturn(roles)

        # member group 1 - has no change
        api.keystone.roles_for_group(IsA(http.HttpRequest),
                                     group='2',
                                     project=self.tenant.id) \
                           .AndReturn((roles[1],))

        # member group 3 - has role 1
        api.keystone.roles_for_group(IsA(http.HttpRequest),
                                     group='3',
                                     project=self.tenant.id) \
                           .AndReturn((roles[0],))

        # add role 2
        api.keystone.add_group_role(IsA(http.HttpRequest),
                                    role='2',
                                    group='3',
                                    project=self.tenant.id)

        nova_updated_quota = dict([(key, updated_quota[key]) for key in
                                   quotas.NOVA_QUOTA_FIELDS])
        api.nova.tenant_quota_update(IsA(http.HttpRequest),
                                     project.id,
                                     **nova_updated_quota) \
                            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        # submit form data
        project_data = {"domain_id": project._info["domain_id"],
                        "name": project._info["name"],
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
                                       'domain_get',
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
                                       'role_list'),
                        quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas')})
    def test_update_project_member_update_error(self):
        project = self.tenants.first()
        quota = self.quotas.first()
        default_role = self.roles.first()
        domain_id = project.domain_id
        users = self._get_all_users(domain_id)
        proj_users = self._get_proj_users(project.id)
        groups = self._get_all_groups(domain_id)
        roles = self.roles.list()

        # get/init
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(self.domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
        quotas.get_tenant_quota_data(IsA(http.HttpRequest),
                                     tenant_id=self.tenant.id) \
            .AndReturn(quota)

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.user_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(users)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain_id) \
            .AndReturn(groups)
        api.keystone.user_list(IsA(http.HttpRequest),
                       project=self.tenant.id).AndReturn(proj_users)

        workflow_data = {}
        for user in proj_users:
            api.keystone.roles_for_user(IsA(http.HttpRequest),
                                        user.id,
                                        self.tenant.id).AndReturn(roles)
        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         project=self.tenant.id) \
                .AndReturn(roles)

        workflow_data[USER_ROLE_PREFIX + "1"] = ['1', '3']  # admin role
        workflow_data[USER_ROLE_PREFIX + "2"] = ['1', '2', '3']  # member role

        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['1', '3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['1', '2', '3']  # member role
        # update some fields
        project._info["domain_id"] = domain_id
        project._info["name"] = "updated name"
        project._info["description"] = "updated description"
        quota.metadata_items = 444
        quota.volumes = 444

        updated_project = {"name": project._info["name"],
                           "description": project._info["description"],
                           "enabled": project.enabled}
        updated_quota = self._get_quota_info(quota)

        # handle
        api.keystone.tenant_update(IsA(http.HttpRequest),
                                   project.id,
                                   **updated_project) \
            .AndReturn(project)

        api.keystone.user_list(IsA(http.HttpRequest),
                               project=self.tenant.id).AndReturn(proj_users)

        # admin user - try to remove all roles on current project, warning
        api.keystone.roles_for_user(IsA(http.HttpRequest), '1',
                                    self.tenant.id).AndReturn(roles)

        # member user 1 - has role 1, will remove it
        api.keystone.roles_for_user(IsA(http.HttpRequest), '2',
                                    self.tenant.id).AndReturn((roles[1],))

        # member user 3 - has role 2
        api.keystone.roles_for_user(IsA(http.HttpRequest), '3',
                                    self.tenant.id).AndReturn((roles[0],))
        # add role 2
        api.keystone.add_tenant_user_role(IsA(http.HttpRequest),
                                          project=self.tenant.id,
                                          user='3',
                                          role='2')\
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        # submit form data
        project_data = {"domain_id": project._info["domain_id"],
                        "name": project._info["name"],
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

    @test.create_stubs({api.keystone: ('get_default_role',
                                       'tenant_get',
                                       'domain_get'),
                        quotas: ('get_tenant_quota_data',
                                 'get_disabled_quotas')})
    def test_update_project_when_default_role_does_not_exist(self):
        project = self.tenants.first()
        domain_id = project.domain_id
        quota = self.quotas.first()

        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(None)  # Default role doesn't exist
        api.keystone.tenant_get(IsA(http.HttpRequest), self.tenant.id,
                                admin=True) \
            .AndReturn(project)
        api.keystone.domain_get(IsA(http.HttpRequest), domain_id) \
            .AndReturn(self.domain)
        quotas.get_disabled_quotas(IsA(http.HttpRequest)) \
            .AndReturn(self.disabled_quotas.first())
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
                self.client.get(url)
        finally:
            logging.disable(logging.NOTSET)
