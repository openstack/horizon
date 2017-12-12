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

from django import http
from django.urls import reverse
from django.utils import html
from mox3.mox import IsA

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

    @test.create_stubs({api.nova: ('service_list', ), })
    def test_workflow_get(self):

        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        self.mox.ReplayAll()

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.get(url)
        workflow = res.context['workflow']

        self.assertTemplateUsed(res, constants.AGGREGATES_CREATE_VIEW_TEMPLATE)
        self.assertEqual(workflow.name, workflows.CreateAggregateWorkflow.name)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<SetAggregateInfoStep: set_aggregate_info>',
             '<AddHostsToAggregateStep: add_host_to_aggregate>'])

    @test.create_stubs({api.nova: ('service_list', 'aggregate_details_list',
                                   'aggregate_create'), })
    def _test_generic_create_aggregate(self, workflow_data, aggregate,
                                       existing_aggregates=(),
                                       error_count=0,
                                       expected_error_message=None):
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        api.nova.aggregate_details_list(IsA(http.HttpRequest)) \
            .AndReturn(existing_aggregates)
        if not expected_error_message:
            api.nova.aggregate_create(
                IsA(http.HttpRequest),
                name=workflow_data['name'],
                availability_zone=workflow_data['availability_zone'],
            ).AndReturn(aggregate)

        self.mox.ReplayAll()

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.post(url, workflow_data)

        if not expected_error_message:
            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(
                res, reverse(constants.AGGREGATES_INDEX_URL))
        else:
            self.assertFormErrors(res, error_count, expected_error_message)

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

    @test.create_stubs({api.nova: ('service_list',
                                   'aggregate_details_list',
                                   'aggregate_create',
                                   'add_host_to_aggregate'), })
    def test_create_aggregate_with_hosts(self):
        aggregate = self.aggregates.first()

        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        compute_hosts = [s.host for s in compute_services]
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        api.nova.aggregate_details_list(IsA(http.HttpRequest)).AndReturn([])

        workflow_data = self._get_create_workflow_data(aggregate,
                                                       compute_hosts)
        api.nova.aggregate_create(
            IsA(http.HttpRequest),
            name=workflow_data['name'],
            availability_zone=workflow_data['availability_zone'],
        ).AndReturn(aggregate)

        for host in compute_hosts:
            api.nova.add_host_to_aggregate(
                IsA(http.HttpRequest),
                aggregate.id, host).InAnyOrder()

        self.mox.ReplayAll()

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.post(url, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))

    @test.create_stubs({api.nova: ('service_list',
                                   'aggregate_details_list', ), })
    def test_service_list_nova_compute(self):
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        self.mox.ReplayAll()

        url = reverse(constants.AGGREGATES_CREATE_URL)
        res = self.client.get(url)
        workflow = res.context['workflow']
        step = workflow.get_step("add_host_to_aggregate")
        field_name = step.get_member_field_name('member')
        self.assertEqual(len(step.action.fields[field_name].choices),
                         len(compute_services))


class AggregatesViewTests(test.BaseAdminViewTests):

    @mock.patch('openstack_dashboard.api.nova.extension_supported',
                mock.Mock(return_value=False))
    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_panel_not_available(self):
        api.keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn(self.tenants.list())
        self.mox.ReplayAll()

        self.patchers['aggregates'].stop()
        res = self.client.get(reverse('horizon:admin:overview:index'))
        self.assertNotIn(b'Host Aggregates', res.content)

    @test.create_stubs({api.nova: ('aggregate_details_list',
                                   'availability_zone_list',)})
    def test_index(self):
        api.nova.aggregate_details_list(IsA(http.HttpRequest)) \
                .AndReturn(self.aggregates.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest), detailed=True) \
                .AndReturn(self.availability_zones.list())
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.AGGREGATES_INDEX_URL))
        self.assertTemplateUsed(res, constants.AGGREGATES_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['host_aggregates_table'].data,
                              self.aggregates.list())
        self.assertItemsEqual(res.context['availability_zones_table'].data,
                              self.availability_zones.list())

    @test.create_stubs({api.nova: ('aggregate_update', 'aggregate_get',), })
    def _test_generic_update_aggregate(self, form_data, aggregate,
                                       error_count=0,
                                       expected_error_message=None):
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id))\
                .AndReturn(aggregate)
        if not expected_error_message:
            az = form_data['availability_zone']
            aggregate_data = {'name': form_data['name'],
                              'availability_zone': az}
            api.nova.aggregate_update(IsA(http.HttpRequest), str(aggregate.id),
                                      aggregate_data)
        self.mox.ReplayAll()

        res = self.client.post(reverse(constants.AGGREGATES_UPDATE_URL,
                               args=[aggregate.id]),
                               form_data)

        if not expected_error_message:
            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(
                res, reverse(constants.AGGREGATES_INDEX_URL))
        else:
            self.assertFormErrors(res, error_count, expected_error_message)

    def test_update_aggregate(self):
        aggregate = self.aggregates.first()
        form_data = {'id': aggregate.id,
                     'name': 'my_new_name',
                     'availability_zone': 'my_new_zone'}

        self._test_generic_update_aggregate(form_data, aggregate)

    def test_update_aggregate_fails_missing_fields(self):
        aggregate = self.aggregates.first()
        form_data = {'id': aggregate.id}

        self._test_generic_update_aggregate(form_data, aggregate, 1,
                                            u'This field is required')


class ManageHostsTests(test.BaseAdminViewTests):

    @test.create_stubs({api.nova: ('aggregate_get', 'service_list')})
    def test_manage_hosts(self):
        aggregate = self.aggregates.first()

        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                      args=[aggregate.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                constants.AGGREGATES_MANAGE_HOSTS_TEMPLATE)

    @test.create_stubs({api.nova: ('aggregate_get', 'add_host_to_aggregate',
                                   'remove_host_from_aggregate',
                                   'service_list')})
    def test_manage_hosts_update_add_remove_not_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['host1', 'host2']
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host = compute_services[0].host
        form_data = {'manageaggregatehostsaction_role_member': [host]}

        api.nova.remove_host_from_aggregate(IsA(http.HttpRequest),
                                            str(aggregate.id),
                                            'host2').InAnyOrder()
        api.nova.remove_host_from_aggregate(IsA(http.HttpRequest),
                                            str(aggregate.id),
                                            'host1').InAnyOrder()
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        api.nova.add_host_to_aggregate(IsA(http.HttpRequest),
                                       str(aggregate.id), host)
        self.mox.ReplayAll()

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))

    @test.create_stubs({api.nova: ('aggregate_get', 'add_host_to_aggregate',
                                   'remove_host_from_aggregate',
                                   'service_list')})
    def test_manage_hosts_update_add_not_empty_aggregate_should_fail(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['devstack001']
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host1 = compute_services[0].host
        host3 = compute_services[2].host
        form_data = {'manageaggregatehostsaction_role_member': [host1, host3]}

        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .InAnyOrder().AndReturn(aggregate)
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .InAnyOrder().AndReturn(aggregate)
        api.nova.add_host_to_aggregate(IsA(http.HttpRequest),
                                       str(aggregate.id),
                                       host3) \
                .InAnyOrder().AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertMessageCount(error=2)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))

    @test.create_stubs({api.nova: ('aggregate_get', 'add_host_to_aggregate',
                                   'remove_host_from_aggregate',
                                   'service_list')})
    def test_manage_hosts_update_clean_not_empty_aggregate_should_fail(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['host2']
        form_data = {'manageaggregatehostsaction_role_member':
                     []}

        api.nova.remove_host_from_aggregate(IsA(http.HttpRequest),
                                            str(aggregate.id),
                                            'host2')\
                .AndRaise(self.exceptions.nova)
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        self.mox.ReplayAll()

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertMessageCount(error=2)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))

    @test.create_stubs({api.nova: ('aggregate_get', 'add_host_to_aggregate',
                                   'remove_host_from_aggregate',
                                   'service_list')})
    def _test_manage_hosts_update(self,
                                  host,
                                  aggregate,
                                  form_data,
                                  addAggregate=False,
                                  cleanAggregates=False):
        if cleanAggregates:
            api.nova.remove_host_from_aggregate(IsA(http.HttpRequest),
                                                str(aggregate.id),
                                                'host3').InAnyOrder()
            api.nova.remove_host_from_aggregate(IsA(http.HttpRequest),
                                                str(aggregate.id),
                                                'host2').InAnyOrder()
            api.nova.remove_host_from_aggregate(IsA(http.HttpRequest),
                                                str(aggregate.id),
                                                'host1').InAnyOrder()
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest), binary='nova-compute') \
            .AndReturn(compute_services)
        api.nova.aggregate_get(IsA(http.HttpRequest), str(aggregate.id)) \
                .AndReturn(aggregate)
        if addAggregate:
            api.nova.add_host_to_aggregate(IsA(http.HttpRequest),
                                           str(aggregate.id),
                                           host)
        self.mox.ReplayAll()

        res = self.client.post(reverse(constants.AGGREGATES_MANAGE_HOSTS_URL,
                                       args=[aggregate.id]),
                               form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.AGGREGATES_INDEX_URL))

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
                                       addAggregate=False)

    def test_manage_hosts_update_nothing_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = []
        form_data = {'manageaggregatehostsaction_role_member':
                     []}
        self._test_manage_hosts_update(None,
                                       aggregate,
                                       form_data,
                                       addAggregate=False)

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
                                       addAggregate=True)

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
                                       addAggregate=True)

    def test_manage_hosts_update_clean_not_empty_aggregate(self):
        aggregate = self.aggregates.first()
        aggregate.hosts = ['host1', 'host2', 'host3']
        form_data = {'manageaggregatehostsaction_role_member':
                     []}
        self._test_manage_hosts_update(None,
                                       aggregate,
                                       form_data,
                                       addAggregate=False,
                                       cleanAggregates=True)
