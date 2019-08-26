# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import django
from django.conf import settings
from django.urls import reverse
import mock
from novaclient.v2 import flavors

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.flavors import constants
from openstack_dashboard.dashboards.admin.flavors import tables
from openstack_dashboard.dashboards.admin.flavors import workflows
from openstack_dashboard.test import helpers as test


class FlavorsViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.nova: ('flavor_list_paged',),
                        flavors.Flavor: ('get_keys',), })
    def test_index(self):
        self.mock_flavor_list_paged.return_value = (self.flavors.list(),
                                                    False, False)
        self.mock_get_keys.return_value = {}

        res = self.client.get(reverse(constants.FLAVORS_INDEX_URL))
        self.assertTemplateUsed(res, constants.FLAVORS_TEMPLATE_NAME)
        self.assertItemsEqual(res.context['table'].data, self.flavors.list())

        self.mock_flavor_list_paged.assert_called_once_with(
            test.IsHttpRequest(), None, marker=None, paginate=True,
            sort_dir='asc', sort_key='name', reversed_order=False)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_keys, 4, mock.call())

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_mocks({api.nova: ('flavor_list_paged',),
                        flavors.Flavor: ('get_keys',), })
    def test_index_pagination(self):
        flavors_list = self.flavors.list()[:4]
        self.mock_flavor_list_paged.side_effect = [
            (flavors_list, True, True),
            (flavors_list[:2], True, True),
            (flavors_list[2:4], True, True),
        ]
        self.mock_get_keys.return_value = {}

        # get all
        res = self.client.get(reverse(constants.FLAVORS_INDEX_URL))
        self.assertTemplateUsed(res, constants.FLAVORS_TEMPLATE_NAME)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[:5])

        # get first page with 2 items
        res = self.client.get(reverse(constants.FLAVORS_INDEX_URL))
        self.assertTemplateUsed(res, constants.FLAVORS_TEMPLATE_NAME)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[:2])

        # get second page (items 2-4)
        params = "=".join([tables.FlavorsTable._meta.pagination_param,
                           flavors_list[2].id])
        url = "?".join([reverse(constants.FLAVORS_INDEX_URL), params])
        res = self.client.get(url)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[2:4])

        self.mock_flavor_list_paged.assert_has_calls([
            mock.call(test.IsHttpRequest(), None,
                      marker=None, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
            mock.call(test.IsHttpRequest(), None,
                      marker=None, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
            mock.call(test.IsHttpRequest(), None,
                      marker=flavors_list[2].id, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
        ])
        self.assertEqual(3, self.mock_flavor_list_paged.call_count)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_keys, 8, mock.call())

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_mocks({api.nova: ('flavor_list_paged',),
                        flavors.Flavor: ('get_keys',), })
    def test_index_prev_pagination(self):
        flavors_list = self.flavors.list()[:3]
        self.mock_flavor_list_paged.side_effect = [
            (flavors_list, True, False),
            (flavors_list[:2], True, True),
            (flavors_list[2:], True, True),
            (flavors_list[:2], True, True),
        ]
        self.mock_get_keys.return_value = {}

        # get all
        res = self.client.get(reverse(constants.FLAVORS_INDEX_URL))
        self.assertTemplateUsed(res, constants.FLAVORS_TEMPLATE_NAME)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[:3])
        # get first page with 2 items
        res = self.client.get(reverse(constants.FLAVORS_INDEX_URL))
        self.assertEqual(len(res.context['table'].data),
                         settings.API_RESULT_PAGE_SIZE)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[:2])
        params = "=".join([tables.FlavorsTable._meta.pagination_param,
                           flavors_list[2].id])
        url = "?".join([reverse(constants.FLAVORS_INDEX_URL), params])
        res = self.client.get(url)
        # get second page (item 3)
        self.assertEqual(len(res.context['table'].data), 1)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[2:3])

        params = "=".join([tables.FlavorsTable._meta.prev_pagination_param,
                           flavors_list[2].id])
        url = "?".join([reverse(constants.FLAVORS_INDEX_URL), params])
        res = self.client.get(url)
        # prev back to get first page with 2 items
        self.assertEqual(len(res.context['table'].data),
                         settings.API_RESULT_PAGE_SIZE)
        self.assertItemsEqual(res.context['table'].data,
                              self.flavors.list()[:2])

        self.mock_flavor_list_paged.assert_has_calls([
            mock.call(test.IsHttpRequest(), None,
                      marker=None, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
            mock.call(test.IsHttpRequest(), None,
                      marker=None, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
            mock.call(test.IsHttpRequest(), None,
                      marker=flavors_list[2].id, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
            mock.call(test.IsHttpRequest(), None,
                      marker=flavors_list[2].id, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=True),
        ])
        self.assertEqual(4, self.mock_flavor_list_paged.call_count)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_keys, 8, mock.call())

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=1)
    @test.create_mocks({api.nova: ('flavor_list_paged',),
                        flavors.Flavor: ('get_keys',), })
    def test_index_form_action_with_pagination(self):
        page_size = settings.API_RESULT_PAGE_SIZE
        flavors_list = self.flavors.list()[:2]
        self.mock_flavor_list_paged.side_effect = [
            (flavors_list[:page_size], False, False),
            (flavors_list[page_size:], False, False),
        ]
        self.mock_get_keys.return_value = {}

        res = self.client.get(reverse(constants.FLAVORS_INDEX_URL))
        self.assertTemplateUsed(res, constants.FLAVORS_TEMPLATE_NAME)
        self.assertEqual(len(res.context['table'].data), page_size)

        params = "=".join([tables.FlavorsTable._meta.pagination_param,
                           flavors_list[page_size - 1].id])
        next_page_url = "?".join([reverse(constants.FLAVORS_INDEX_URL),
                                  params])
        form_action = 'action="%s"' % next_page_url

        res = self.client.get(next_page_url)
        self.assertEqual(len(res.context['table'].data), 1)
        self.assertContains(res, form_action, count=1)

        self.mock_flavor_list_paged.assert_has_calls([
            mock.call(test.IsHttpRequest(), None,
                      marker=None, paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
            mock.call(test.IsHttpRequest(), None,
                      marker=flavors_list[page_size - 1].id,
                      paginate=True,
                      sort_dir='asc', sort_key='name',
                      reversed_order=False),
        ])
        self.assertEqual(2, self.mock_flavor_list_paged.call_count)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_get_keys, 2, mock.call())


class BaseFlavorWorkflowTests(test.BaseAdminViewTests):

    def _flavor_create_params(self, flavor, id=None):
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        flavor_info = {"name": flavor.name,
                       "vcpu": flavor.vcpus,
                       "memory": flavor.ram,
                       "disk": flavor.disk,
                       "swap": flavor.swap,
                       "rxtx_factor": flavor.rxtx_factor,
                       "ephemeral": eph,
                       "is_public": flavor.is_public}
        if id:
            flavor_info["flavorid"] = id
        return flavor_info

    def _get_workflow_data(self, flavor, id=None, access=None):
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        flavor_info = {"name": flavor.name,
                       "vcpus": flavor.vcpus,
                       "memory_mb": flavor.ram,
                       "disk_gb": flavor.disk,
                       "swap_mb": flavor.swap,
                       "rxtx_factor": flavor.rxtx_factor,
                       "eph_gb": eph}
        self._get_access_field(flavor_info, access)
        if id:
            flavor_info['flavor_id'] = id
        return flavor_info

    def _get_access_field(self, flavor_info=None, access=None):
        flavor_info = flavor_info or {}
        if access is not None:
            access_field_name = 'flavor_access_role_member'
            flavor_info[access_field_name] = [p.id for p in access]
        return flavor_info


class CreateFlavorWorkflowTests(BaseFlavorWorkflowTests):
    @test.create_mocks({api.keystone: ('tenant_list',), })
    def test_workflow_get(self):
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.get(url)
        self.assertTemplateUsed(res, constants.FLAVORS_CREATE_VIEW_TEMPLATE)
        workflow = res.context['workflow']
        expected_name = workflows.CreateFlavor.name
        self.assertEqual(res.context['workflow'].name, expected_name)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<CreateFlavorInfo: createflavorinfoaction>',
             '<CreateFlavorAccess: flavor_access>'])
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',
                                   'flavor_create',)})
    def test_create_flavor_without_projects_post(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = []
        self.mock_flavor_create.return_value = flavor

        workflow_data = self._get_workflow_data(flavor)

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, reverse(constants.FLAVORS_INDEX_URL))

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)
        params = self._flavor_create_params(flavor, id='auto')
        self.mock_flavor_create.assert_called_once_with(test.IsHttpRequest(),
                                                        **params)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',
                                   'flavor_create',
                                   'add_tenant_to_flavor',)})
    def test_create_flavor_with_projects_post(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = []
        self.mock_flavor_create.return_value = flavor
        self.mock_add_tenant_to_flavor.return_value = None

        workflow_data = self._get_workflow_data(flavor, access=projects)

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, reverse(constants.FLAVORS_INDEX_URL))

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)
        params = self._flavor_create_params(flavor, id='auto')
        params['is_public'] = False
        self.mock_flavor_create.assert_called_once_with(test.IsHttpRequest(),
                                                        **params)
        self.mock_add_tenant_to_flavor.assert_has_calls(
            [mock.call(test.IsHttpRequest(), flavor.id, project.id)
             for project in projects]
        )
        self.assertEqual(len(projects),
                         self.mock_add_tenant_to_flavor.call_count)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',)})
    def test_create_existing_flavor_name_error(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = self.flavors.list()

        workflow_data = self._get_workflow_data(flavor)

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertFormErrors(res)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',)})
    def test_create_existing_flavor_id_error(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = self.flavors.list()

        workflow_data = self._get_workflow_data(flavor)
        # Name is okay.
        workflow_data['name'] = 'newflavorname'
        # Flavor id already exists.
        workflow_data['flavor_id'] = flavor.id

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertFormErrors(res)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',
                                   'flavor_create',
                                   'add_tenant_to_flavor',)})
    def test_create_flavor_project_update_error(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        # init
        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = []
        self.mock_flavor_create.return_value = flavor
        retvals_add_tenant = [None for project in projects]
        retvals_add_tenant[0] = self.exceptions.nova
        self.mock_add_tenant_to_flavor.side_effect = retvals_add_tenant

        workflow_data = self._get_workflow_data(flavor, access=projects)

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1, warning=0)
        self.assertRedirectsNoFollow(res, reverse(constants.FLAVORS_INDEX_URL))

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)
        params = self._flavor_create_params(flavor, id='auto')
        params['is_public'] = False
        self.mock_flavor_create.assert_called_once_with(test.IsHttpRequest(),
                                                        **params)
        self.mock_add_tenant_to_flavor.assert_has_calls(
            [mock.call(test.IsHttpRequest(), flavor.id, project.id)
             for project in projects]
        )
        self.assertEqual(len(projects),
                         self.mock_add_tenant_to_flavor.call_count)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',)})
    def test_create_flavor_missing_field_error(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = []

        workflow_data = self._get_workflow_data(flavor)
        workflow_data["name"] = ""

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertFormErrors(res)
        self.assertContains(res, "field is required")

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_list',)})
    def test_create_flavor_missing_swap_and_ephemeral_fields(self):
        flavor = self.flavors.first()
        projects = self.tenants.list()

        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_list.return_value = self.flavors.list()

        workflow_data = self._get_workflow_data(flavor)
        # Swap field empty
        del workflow_data['swap_mb']
        # Ephemeral field empty
        del workflow_data['eph_gb']

        url = reverse(constants.FLAVORS_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertFormErrors(res)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest(),
                                                      None)


class UpdateFlavorWorkflowTests(BaseFlavorWorkflowTests):

    @test.create_mocks({api.nova: ('flavor_get',
                                   'flavor_access_list',),
                        api.keystone: ('tenant_list',)})
    def test_update_flavor_get(self):
        flavor = self.flavors.list()[2]
        flavor_access = self.flavor_access.list()
        projects = self.tenants.list()

        self.mock_flavor_get.return_value = flavor
        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_access_list.return_value = flavor_access

        url = reverse(constants.FLAVORS_UPDATE_URL, args=[flavor.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, constants.FLAVORS_UPDATE_VIEW_TEMPLATE)

        workflow = res.context['workflow']
        expected_name = workflows.UpdateFlavor.name
        self.assertEqual(res.context['workflow'].name, expected_name)

        self.assertQuerysetEqual(
            workflow.steps,
            ['<UpdateFlavorAccess: flavor_access>'])

        step = workflow.get_step("flavor_access")
        field_name = step.get_member_field_name('member')
        self.assertEqual(step.action.fields[field_name].initial,
                         [fa.tenant_id for fa in flavor_access])

        self.mock_flavor_get.assert_called_once_with(test.IsHttpRequest(),
                                                     flavor.id)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_access_list.assert_called_once_with(
            test.IsHttpRequest(), flavor.id)

    @test.create_mocks({api.nova: ('flavor_get',), })
    def test_update_flavor_get_flavor_error(self):
        flavor = self.flavors.first()

        self.mock_flavor_get.side_effect = self.exceptions.nova

        url = reverse(constants.FLAVORS_UPDATE_URL, args=[flavor.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, reverse(constants.FLAVORS_INDEX_URL))
        self.mock_flavor_get.assert_called_once_with(test.IsHttpRequest(),
                                                     flavor.id)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_get',
                                   'flavor_access_list',
                                   'remove_tenant_from_flavor',
                                   'add_tenant_to_flavor')})
    def test_update_flavor_access(self):
        # The third element is private (is_public False)
        flavor = self.flavors.list()[2]
        projects = self.tenants.list()
        flavor_accesses = self.flavor_access.list()

        self.mock_flavor_get.return_value = flavor
        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_access_list.return_value = flavor_accesses
        self.mock_add_tenant_to_flavor.return_value = None
        self.mock_remove_tenant_from_flavor.return_value = None

        # run get test
        url = reverse(constants.FLAVORS_UPDATE_URL, args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, constants.FLAVORS_UPDATE_VIEW_TEMPLATE)

        # run post test
        data = self._get_access_field(access=projects[1:3])
        resp = self.client.post(url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1, error=0, warning=0)
        self.assertRedirectsNoFollow(resp,
                                     reverse(constants.FLAVORS_INDEX_URL))

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_get, 2,
            mock.call(test.IsHttpRequest(), flavor.id))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_list, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_access_list, 2,
            mock.call(test.IsHttpRequest(), flavor.id))
        # NOTE: This test assumes self.tenants.list() and
        # self.flavor_access.list() contains project IDs in a same order.
        # Otherwise, mocking below will fail.
        self.mock_add_tenant_to_flavor.assert_called_once_with(
            test.IsHttpRequest(), flavor.id, projects[2].id)
        self.mock_remove_tenant_from_flavor.assert_called_once_with(
            test.IsHttpRequest(), flavor.id, projects[0].id)

    @test.create_mocks({api.keystone: ('tenant_list',),
                        api.nova: ('flavor_get',
                                   'flavor_access_list',
                                   'add_tenant_to_flavor')})
    def test_update_flavor_access_with_error(self):
        # The third element is private (is_public False)
        flavor = self.flavors.list()[2]
        projects = self.tenants.list()
        flavor_projects = [self.tenants.first()]

        self.mock_flavor_get.return_value = flavor
        self.mock_tenant_list.return_value = [projects, False]
        self.mock_flavor_access_list.return_value = []
        self.mock_add_tenant_to_flavor.side_effect = self.exceptions.nova

        # run get test
        url = reverse(constants.FLAVORS_UPDATE_URL, args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, constants.FLAVORS_UPDATE_VIEW_TEMPLATE)

        # run post test
        data = self._get_access_field(access=flavor_projects)
        resp = self.client.post(url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(error=1, warning=0)
        self.assertRedirectsNoFollow(resp,
                                     reverse(constants.FLAVORS_INDEX_URL))

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_get, 2,
            mock.call(test.IsHttpRequest(), flavor.id))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_list, 2,
            mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_access_list, 2,
            mock.call(test.IsHttpRequest(), flavor.id))

        self.mock_add_tenant_to_flavor.assert_called_once_with(
            test.IsHttpRequest(), flavor.id, flavor_projects[0].id)
