# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

from django.core.urlresolvers import reverse  # noqa
from django import http  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse("horizon:admin:metering:index")


class MeteringViewTests(test.APITestCase, test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_disk_usage(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 marker='tenant_marker',
                                 paginate=True) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name=IsA(str),
                                         period=None, q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        res = self.client.get(reverse('horizon:admin:metering:index'))
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        table_stats = res.context['table'].data

        first = table_stats[0]
        self.assertEqual(first.id, 'test_tenant')
        self.assertEqual(first.disk_write_requests, 4.55)
        self.assertEqual(first.disk_read_bytes, 4.55)
        self.assertEqual(first.disk_write_bytes, 4.55)
        self.assertEqual(first.disk_read_bytes, 4.55)

        second = table_stats[1]
        self.assertEqual(second.id, 'disabled_tenant')
        self.assertEqual(second.disk_write_requests, 4.55)
        self.assertEqual(second.disk_read_bytes, 4.55)
        self.assertEqual(second.disk_write_bytes, 4.55)
        self.assertEqual(second.disk_read_bytes, 4.55)

        # check there is as many rows as tenants
        self.assertEqual(len(table_stats),
                         len(self.tenants.list()))
        self.assertIsInstance(first, api.ceilometer.ResourceAggregate)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_global_network_traffic_usage(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 marker='tenant_marker',
                                 paginate=True) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name=IsA(str),
                                         period=None, q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        res = self.client.get(reverse('horizon:admin:metering:index') +
            "?tab=ceilometer_overview__global_network_traffic_usage")
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        table_stats = res.context['table'].data

        first = table_stats[0]
        self.assertEqual(first.id, 'test_tenant')
        self.assertEqual(first.network_incoming_bytes, 4.55)
        self.assertEqual(first.network_incoming_packets, 4.55)
        self.assertEqual(first.network_outgoing_bytes, 4.55)
        self.assertEqual(first.network_outgoing_packets, 4.55)

        second = table_stats[1]
        self.assertEqual(second.id, 'disabled_tenant')
        self.assertEqual(second.network_incoming_bytes, 4.55)
        self.assertEqual(second.network_incoming_packets, 4.55)
        self.assertEqual(second.network_outgoing_bytes, 4.55)
        self.assertEqual(second.network_outgoing_packets, 4.55)

        # check there is as many rows as tenants
        self.assertEqual(len(table_stats),
                         len(self.tenants.list()))
        self.assertIsInstance(first, api.ceilometer.ResourceAggregate)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_global_network_usage(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 marker='tenant_marker',
                                 paginate=True) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name=IsA(str),
                                         period=None, q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        res = self.client.get(reverse('horizon:admin:metering:index') +
            "?tab=ceilometer_overview__global_network_usage")
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        table_stats = res.context['table'].data

        first = table_stats[0]
        self.assertEqual(first.id, 'test_tenant')
        self.assertEqual(first.network, 4.55)
        self.assertEqual(first.network_create, 4.55)
        self.assertEqual(first.subnet, 4.55)
        self.assertEqual(first.subnet_create, 4.55)
        self.assertEqual(first.port, 4.55)
        self.assertEqual(first.port_create, 4.55)
        self.assertEqual(first.router, 4.55)
        self.assertEqual(first.router_create, 4.55)
        self.assertEqual(first.ip_floating, 4.55)
        self.assertEqual(first.ip_floating_create, 4.55)

        second = table_stats[1]
        self.assertEqual(second.id, 'disabled_tenant')
        self.assertEqual(second.network, 4.55)
        self.assertEqual(second.network_create, 4.55)
        self.assertEqual(second.subnet, 4.55)
        self.assertEqual(second.subnet_create, 4.55)
        self.assertEqual(second.port, 4.55)
        self.assertEqual(second.port_create, 4.55)
        self.assertEqual(second.router, 4.55)
        self.assertEqual(second.router_create, 4.55)
        self.assertEqual(second.ip_floating, 4.55)
        self.assertEqual(second.ip_floating_create, 4.55)

        # check there is as many rows as tenants
        self.assertEqual(len(table_stats),
                         len(self.tenants.list()))
        self.assertIsInstance(first, api.ceilometer.ResourceAggregate)

    @test.create_stubs({api.ceilometer.CeilometerUsage: ("get_user",
                                                         "get_tenant")})
    def test_global_object_store_usage(self):
        resources = self.resources.list()
        statistics = self.statistics.list()
        user = self.ceilometer_users.list()[0]
        tenant = self.ceilometer_tenants.list()[0]

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=None).AndReturn(resources)

        ceilometerclient.statistics = self.mox.CreateMockAnything()
        ceilometerclient.statistics.list(meter_name=IsA(str),
                                         period=None, q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        api.ceilometer.CeilometerUsage\
                .get_user(IsA(str)).MultipleTimes().AndReturn(user)
        api.ceilometer.CeilometerUsage\
                .get_tenant(IsA(str)).MultipleTimes().AndReturn(tenant)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        res = self.client.get(reverse('horizon:admin:metering:index') +
            "?tab=ceilometer_overview__global_object_store_usage")
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        table_stats = res.context['table'].data

        first = table_stats[0]
        self.assertEqual(first.id, 'fake_project_id__fake_user_id__'
                                   'fake_resource_id')
        self.assertEqual(first.user.name, 'user')
        self.assertEqual(first.tenant.name, 'test_tenant')
        self.assertEqual(first.resource, 'fake_resource_id')

        self.assertEqual(first.storage_objects, 4.55)
        self.assertEqual(first.storage_objects_size, 4.55)
        self.assertEqual(first.storage_objects_incoming_bytes, 4.55)
        self.assertEqual(first.storage_objects_outgoing_bytes, 4.55)

        self.assertEqual(len(table_stats), len(resources))
        self.assertIsInstance(first, api.ceilometer.GlobalObjectStoreUsage)

    def test_stats_page(self):
        resources = self.resources.list()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        # I am returning only 1 resource
        ceilometerclient.resources.list(q=IsA(list)).AndReturn(resources[:1])

        self.mox.ReplayAll()

        # getting all resources and with statistics
        res = self.client.get(reverse('horizon:admin:metering:index') +
            "?tab=ceilometer_overview__stats")
        self.assertTemplateUsed(res, 'admin/metering/index.html')
        self.assertTemplateUsed(res, 'admin/metering/stats.html')

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_for_line_chart(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 marker='tenant_marker',
                                 paginate=True) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name="memory",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get all statistics of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=memory&group_by=project&stats_attr=avg&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        self.assertEqual(res._container,
                        ['{"series": [{"data": [{"y": 4, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "test_tenant", "unit": ""}, '
                                     '{"data": [{"y": 4, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "disabled_tenant", '
                                      '"unit": ""}, '
                                     '{"data": [{"y": 4, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "\\u4e91\\u89c4\\u5219", '
                                      '"unit": ""}], '
                          '"settings": {}}'])

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_stats_for_line_chart_attr_max(self):
        statistics = self.statistics.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 marker='tenant_marker',
                                 paginate=True) \
            .AndReturn([self.tenants.list(), False])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name="memory",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # get all statistics of project aggregates
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=memory&group_by=project&stats_attr=max&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        self.assertEqual(res._container,
                        ['{"series": [{"data": [{"y": 9, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "test_tenant", "unit": ""}, '
                                     '{"data": [{"y": 9, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "disabled_tenant", '
                                      '"unit": ""}, '
                                     '{"data": [{"y": 9, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "\\u4e91\\u89c4\\u5219", '
                                      '"unit": ""}], '
                          '"settings": {}}'])

    def test_stats_for_line_chart_no_group_by(self):
        resources = self.resources.list()
        statistics = self.statistics.list()

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=IsA(list)).AndReturn(resources)

        ceilometerclient.statistics = self.mox.CreateMockAnything()
        ceilometerclient.statistics.list(meter_name="storage.objects",
                                         period=IsA(int), q=IsA(list)).\
            MultipleTimes().\
            AndReturn(statistics)

        self.mox.ReplayAll()

        # getting all resources and with statistics, I have only
        # 'storage.objects' defined in test data
        res = self.client.get(reverse('horizon:admin:metering:samples') +
            "?meter=storage.objects&stats_attr=avg&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        self.assertEqual(res._container,
                        ['{"series": [{"data": [{"y": 4, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "fake_resource_id", '
                                      '"unit": ""}, '
                                     '{"data": [{"y": 4, '
                                      '"x": "2012-12-21T11:00:55"}], '
                                      '"name": "fake_resource_id2", '
                                      '"unit": ""}], '
                          '"settings": {}}'])
