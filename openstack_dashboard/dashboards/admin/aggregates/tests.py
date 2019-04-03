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

import mock

from django.urls import reverse
from django.utils import html

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.aggregates import constants
from openstack_dashboard.dashboards.admin.aggregates import workflows
from openstack_dashboard.test import helpers as test


class BaseAggregateWorkflowTests(test.BaseAdminViewTests):

    def _get_create_workflow_data(self, aggregate, hosts=None):
        aggregate_info = {"name": aggregate.name,
                          "availability_zone": aggregate.availability_zone}

        if hosts:
            host_field_name = 'add_host_to_aggregate_role_member'
            aggregate_info[host_field_name] = hosts

        return aggregate_info


class CreateAggregateWorkflowTests(BaseAggregateWorkflowTests):

    @test.create_mocks({api.nova: ['service_list']})
    def test_workflow_get(self):

        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.get(url)
        workflow = res.context['workflow']

        self.assertTemplateUsed(res, constants.AGGREGATES_CREATE_VIEW_TEMPLATE)
        self.assertEqual(workflow.name, workflows.CreateAggregateWorkflow.name)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<SetAggregateInfoStep: set_aggregate_info>',
             '<AddHostsToAggregateStep: add_host_to_aggregate>'])
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(),
            binary='nova-compute')

    @test.create_mocks({
        api.nova: ['service_list',
                   'aggregate_details_list',
                   'aggregate_create']})
    def _test_generic_create_aggregate(self, workflow_data, aggregate,
                                       existing_aggregates=(),
                                       error_count=0,
                                       expected_error_message=None):
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services
        self.mock_aggregate_details_list.return_value = existing_aggregates

        if not expected_error_message:
            self.mock_aggregate_create.return_value = aggregate

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.post(url, workflow_data)

        if not expected_error_message:
            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(
                res, reverse(constants.AGGREGATES_INDEX_URL))
            self.mock_aggregate_create.assert_called_once_with(
                test.IsHttpRequest(),
                name=workflow_data['name'],
                availability_zone=workflow_data['availability_zone'])
        else:
            self.assertFormErrors(res, error_count, expected_error_message)
            self.mock_aggregate_create.assert_not_called()
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(),
            binary='nova-compute')
        self.mock_aggregate_details_list.assert_called_once_with(
            test.IsHttpRequest())

    def test_create_aggregate(self):
        aggregate = self.aggregates.first()
        workflow_data = self._get_create_workflow_data(aggregate)
        self._test_generic_create_aggregate(workflow_data, aggregate)

    def test_create_aggregate_fails_missing_fields(self):
        aggregate = self.aggregates.first()
        workflow_data = self._get_create_workflow_data(aggregate)
        workflow_data['name'] = ''
        workflow_data['availability_zone'] = ''
        self._test_generic_create_aggregate(workflow_data, aggregate, (), 1,
                                            u'This field is required')

    def test_create_aggregate_fails_missing_fields_existing_aggregates(self):
        aggregate = self.aggregates.first()
        existing_aggregates = self.aggregates.list()
        workflow_data = self._get_create_workflow_data(aggregate)
        workflow_data['name'] = ''
        workflow_data['availability_zone'] = ''

        self._test_generic_create_aggregate(workflow_data, aggregate,
                                            existing_aggregates, 1,
                                            u'This field is required')

    def test_create_aggregate_fails_duplicated_name(self):
        aggregate = self.aggregates.first()
        existing_aggregates = self.aggregates.list()
        workflow_data = self._get_create_workflow_data(aggregate)
        expected_error_message = html \
            .escape(u'The name "%s" is already used by another host aggregate.'
                    % aggregate.name)

        self._test_generic_create_aggregate(workflow_data, aggregate,
                                            existing_aggregates, 1,
                                            expected_error_message)

    @test.create_mocks(
        {api.nova: ['service_list',
                    'aggregate_details_list',
                    'aggregate_create',
                    'add_host_to_aggregate']})
    def test_create_aggregate_with_hosts(self):
        aggregate = self.aggregates.first()

        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        compute_hosts = [s.host for s in compute_services]

        self.mock_service_list.return_value = compute_services
        self.mock_aggregate_details_list.return_value = []

        workflow_data = self._get_create_workflow_data(aggregate,
                                                       compute_hosts)
        self.mock_aggregate_create.return_value = aggregate
        self.mock_add_host_to_aggregate.return_value = None

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(),
            binary='nova-compute')
        self.mock_aggregate_details_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_aggregate_create.assert_called_once_with(
            test.IsHttpRequest(),
            name=workflow_data['name'],
            availability_zone=workflow_data['availability_zone'])
        self.assertEqual(self.mock_add_host_to_aggregate.call_count,
                         len(compute_hosts))

        expected_calls = [mock.call(test.IsHttpRequest(), aggregate.id, h)
                          for h in compute_hosts]
        self.mock_add_host_to_aggregate.assert_has_calls(
            expected_calls)

    @test.create_mocks({api.nova: ['service_list']})
    def test_service_list_nova_compute(self):
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.get(url)
        workflow = res.context['workflow']
        step = workflow.get_step("add_host_to_aggregate")
        field_name = step.get_member_field_name('member')
        self.assertEqual(len(step.action.fields[field_name].choices),
                         len(compute_services))
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')


class AggregatesViewTests(test.BaseAdminViewTests):

    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.nova: ['extension_supported']})
    def test_panel_not_available(self):
        self.mock_tenant_list.return_value = self.tenants.list()
        self.mock_extension_supported.return_value = False

        self.patchers['aggregates'].stop()
        res = self.client.get(reverse('horizon:admin:overview:index'))
        self.assertNotIn(b'Host Aggregates', res.content)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.assertEqual(self.mock_extension_supported.call_count, 3)
        expected_calls = [mock.call(a, test.IsHttpRequest())
                          for a in ['SimpleTenantUsage',
                                    'SimpleTenantUsage',
                                    'Aggregates']]
        self.mock_extension_supported.assert_has_calls(
            expected_calls)

    @test.create_mocks({
        api.nova: ['aggregate_details_list',
                   'availability_zone_list']})
    def test_index(self):
        self.mock_aggregate_details_list.return_value = self.aggregates.list()
        self.mock_availability_zone_list.return_value = \
            self.availability_zones.list()

        res = self.client.get(reverse(constants.AGGREGATES_INDEX_URL))
        self.assertTemplateUsed(res, constants.AGGREGATES_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['host_aggregates_table'].data,
                              self.aggregates.list())
        self.assertItemsEqual(res.context['availability_zones_table'].data,
                              self.availability_zones.list())
        self.mock_aggregate_details_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest(), detailed=True)

    @test.create_mocks({api.nova: ['aggregate_update', 'aggregate_get']})
    def _test_generic_update_aggregate(self, form_data, aggregate,
                                       error_count=0,
                                       expected_error_message=None):
        self.mock_aggregate_get.return_value = aggregate
        if not expected_error_message:
            az = form_data['availability_zone']
            aggregate_data = {'name': form_data['name'],
                              'availability_zone': az}
            self.mock_aggregate_update.return_value = None

        res = self.client.post(reverse(constants.AGGREGATES_UPDATE_URL,
                               args=[aggregate.id]),
                               form_data)

        self.mock_aggregate_get.assert_called_once_with(
            test.IsHttpRequest(),
            str(aggregate.id))
        if not expected_error_message:
            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(
                res, reverse(constants.AGGREGATES_INDEX_URL))
            self.mock_aggregate_update.assert_called_once_with(
                test.IsHttpRequest(),
                str(aggregate.id),
                aggregate_data)
        else:
            self.assertFormErrors(res, error_count, expected_error_message)

    def test_update_aggregate(self):
        aggregate = self.aggregates.first()
        form_data = {'id': aggregate.id,
                     'name': 'my_new_name',
                     'availability_zone': 'my_new_zone'}

        self._test_generic_update_aggregate(form_data, aggregate)

    def test_update_aggregate_fails_missing_name_field(self):
        aggregate = self.aggregates.first()
        form_data = {'id': aggregate.id,
                     'name': '',
                     'availability_zone': aggregate.availability_zone}

        self._test_generic_update_aggregate(form_data, aggregate, 1,
                                            u'This field is required')

    def test_update_aggregate_fails_missing_az_field(self):
        aggregate = self.aggregates.first()
        form_data = {'id': aggregate.id,
                     'name': aggregate.name,
                     'availability_zone': ''}

        self._test_generic_update_aggregate(
            form_data, aggregate, 1,
            u'The new availability zone can&#39;t be empty')


class ManageHostsTests(test.BaseAdminViewTests):

    @test.create_mocks({api.nova: ['aggregate_get', 'service_list']})
    def test_manage_hosts(self):
        aggregate = self.aggregates.first()

        self.mock_aggregate_get.return_value = aggregate
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services

        res = self.client.get(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                      args=[aggregate.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                constants.AGGREGATES_MANAGE_HOSTS_TEMPLATE)
        self.mock_aggregate_get.assert_called_once_with(
            test.IsHttpRequest(),
            str(aggregate.id))
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(),
            binary='nova-compute')

    @test.create_mocks({
        api.nova: ['aggregate_get',
                   'add_host_to_aggregate',
                   'remove_host_from_aggregate',
                   'service_list']})
    def test_manage_hosts_update_add_remove_not_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['host1', 'host2']
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host = compute_services[0].host
        form_data = {'manageaggregatehostsaction_role_member': [host]}

        self.mock_remove_host_from_aggregate.return_value = None
        self.mock_aggregate_get.return_value = aggregate
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services
        self.mock_add_host_to_aggregate.return_value = None

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))
        self.assertEqual(self.mock_aggregate_get.call_count, 2)
        self.mock_aggregate_get.assert_has_calls(
            [mock.call(test.IsHttpRequest(), str(aggregate.id))] * 2)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_add_host_to_aggregate.assert_called_once_with(
            test.IsHttpRequest(), str(aggregate.id), host)
        self.assertEqual(self.mock_remove_host_from_aggregate.call_count, 2)
        expected_calls = [mock.call(test.IsHttpRequest(), str(aggregate.id), h)
                          for h in ('host1', 'host2')]
        self.mock_remove_host_from_aggregate.assert_has_calls(
            expected_calls,
            any_order=True)

    @test.create_mocks({
        api.nova: ['aggregate_get',
                   'add_host_to_aggregate',
                   'remove_host_from_aggregate',
                   'service_list']})
    def test_manage_hosts_update_add_not_empty_aggregate_should_fail(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['devstack001']
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host1 = compute_services[0].host
        host3 = compute_services[2].host
        form_data = {'manageaggregatehostsaction_role_member': [host1, host3]}

        self.mock_aggregate_get.return_value = aggregate
        self.mock_service_list.return_value = compute_services
        self.mock_add_host_to_aggregate.side_effect = self.exceptions.nova

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertMessageCount(error=2)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_aggregate_get,
            2,
            mock.call(test.IsHttpRequest(), str(aggregate.id)))
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_add_host_to_aggregate.assert_called_once_with(
            test.IsHttpRequest(), str(aggregate.id), host3)

    @test.create_mocks({
        api.nova: ['aggregate_get',
                   'add_host_to_aggregate',
                   'remove_host_from_aggregate',
                   'service_list']})
    def test_manage_hosts_update_clean_not_empty_aggregate_should_fail(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['host2']
        form_data = {'manageaggregatehostsaction_role_member':
                     []}

        self.mock_remove_host_from_aggregate.side_effect = self.exceptions.nova
        self.mock_aggregate_get.return_value = aggregate
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=2)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))
        self.mock_remove_host_from_aggregate.assert_called_once_with(
            test.IsHttpRequest(),
            str(aggregate.id),
            'host2')
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_aggregate_get,
            2,
            mock.call(test.IsHttpRequest(), str(aggregate.id)))
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(),
            binary='nova-compute')

    @test.create_mocks({
        api.nova: ['aggregate_get',
                   'add_host_to_aggregate',
                   'remove_host_from_aggregate',
                   'service_list']})
    def _test_manage_hosts_update(self,
                                  host,
                                  aggregate,
                                  form_data,
                                  add_aggregate=False,
                                  clean_aggregates=False):
        if clean_aggregates:
            self.mock_remove_host_from_aggregate.return_value = None
        self.mock_aggregate_get.return_value = aggregate
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services
        if add_aggregate:
            self.mock_add_host_to_aggregate.return_value = None

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))
        if clean_aggregates:
            self.assertEqual(self.mock_remove_host_from_aggregate.call_count,
                             3)
            expected_calls = [mock.call(test.IsHttpRequest(),
                                        str(aggregate.id), h)
                              for h in ('host1', 'host2', 'host3')]
            self.mock_remove_host_from_aggregate.assert_has_calls(
                expected_calls,
                any_order=True)
        else:
            self.mock_remove_host_from_aggregate.assert_not_called()

        if add_aggregate:
            self.mock_add_host_to_aggregate.assert_called_once_with(
                test.IsHttpRequest(),
                str(aggregate.id),
                host)
        else:
            self.mock_add_host_to_aggregate.assert_not_called()

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_aggregate_get,
            2,
            mock.call(test.IsHttpRequest(), str(aggregate.id)))
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(),
            binary='nova-compute')

    def test_manage_hosts_update_nothing_not_empty_aggregate(self):
        aggregate = self.aggregates.first()
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host = compute_services[0].host
        aggregate.hosts = [host]
        form_data = {'manageaggregatehostsaction_role_member': [host]}
        self._test_manage_hosts_update(host,
                                       aggregate,
                                       form_data,
                                       add_aggregate=False)

    def test_manage_hosts_update_nothing_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = []
        form_data = {'manageaggregatehostsaction_role_member':
                     []}
        self._test_manage_hosts_update(None,
                                       aggregate,
                                       form_data,
                                       add_aggregate=False)

    def test_manage_hosts_update_add_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = []
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host = compute_services[0].host
        form_data = {'manageaggregatehostsaction_role_member': [host]}
        self._test_manage_hosts_update(host,
                                       aggregate,
                                       form_data,
                                       add_aggregate=True)

    def test_manage_hosts_update_add_not_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['devstack001']
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host1 = compute_services[0].host
        host3 = compute_services[2].host
        form_data = {'manageaggregatehostsaction_role_member': [host1, host3]}
        self._test_manage_hosts_update(host3,
                                       aggregate,
                                       form_data,
                                       add_aggregate=True)

    def test_manage_hosts_update_clean_not_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['host1', 'host2', 'host3']
        form_data = {'manageaggregatehostsaction_role_member':
                     []}
        self._test_manage_hosts_update(None,
                                       aggregate,
                                       form_data,
                                       add_aggregate=False,
                                       clean_aggregates=True)
