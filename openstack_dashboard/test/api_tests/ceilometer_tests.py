# Copyright 2012 Canonical Ltd.
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

from django import http

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class CeilometerApiTests(test.APITestCase):
    def test_sample_list(self):
        samples = self.samples.list()
        meter_name = "meter_name"
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.samples = self.mox.CreateMockAnything()
        ceilometerclient.samples.list(meter_name=meter_name,
                                      q=[],
                                      limit=None).AndReturn(samples)
        self.mox.ReplayAll()

        ret_list = api.ceilometer.sample_list(self.request,
                                              meter_name,
                                              query=[])
        for c in ret_list:
            self.assertIsInstance(c, api.ceilometer.Sample)

    def test_alarm_list(self):
        alarms = self.alarms.list()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.alarms = self.mox.CreateMockAnything()
        ceilometerclient.alarms.list(q=[]).AndReturn(alarms)
        self.mox.ReplayAll()

        ret_list = api.ceilometer.alarm_list(self.request, query=[])
        self.assertIsNotNone(ret_list)
        for c in ret_list:
            self.assertIsInstance(c, api.ceilometer.Alarm)

    def test_alarm_get(self):
        alarm = self.alarms.first()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.alarms = self.mox.CreateMockAnything()
        ceilometerclient.alarms.get(alarm.id).AndReturn(alarm)
        self.mox.ReplayAll()

        ret_alarm = api.ceilometer.alarm_get(self.request,
                                             alarm_id='fake_alarm_id')
        self.assertEqual(alarm.alarm_id, ret_alarm.alarm_id)

    def test_alarm_create(self):
        alarm = self.alarms.first()
        new_alarm = {'alarm': alarm}
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.alarms = self.mox.CreateMockAnything()
        ceilometerclient.alarms.create(**new_alarm).AndReturn(alarm)
        self.mox.ReplayAll()
        test_alarm = api.ceilometer.alarm_create(self.request,
                                                 **new_alarm)
        self.assertEqual(alarm.alarm_id, test_alarm.alarm_id)

    def test_alarm_update(self):
        """test update parameters"""
        alarm1 = self.alarms.first()
        alarm2 = self.alarms.list()[1]
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.alarms = self.mox.CreateMockAnything()
        # Return the mock object that has "New" as description
        ceilometerclient.alarms.update(alarm1.id,
                                       description='New').AndReturn(alarm2)
        self.mox.ReplayAll()
        test_alarm = api.ceilometer.alarm_update(self.request,
                                                 alarm1.id,
                                                 description='New')
        self.assertEqual(alarm2.description, test_alarm.description)

    def test_meter_list(self):
        meters = self.meters.list()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list([]).AndReturn(meters)
        self.mox.ReplayAll()

        ret_list = api.ceilometer.meter_list(self.request, [])
        for m in ret_list:
            self.assertIsInstance(m, api.ceilometer.Meter)

    def test_resource_list(self):
        resources = self.resources.list()
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=[]).AndReturn(resources)
        self.mox.ReplayAll()

        ret_list = api.ceilometer.resource_list(self.request, query=[])
        for r in ret_list:
            self.assertIsInstance(r, api.ceilometer.Resource)

    def test_statistic_list(self):
        statistics = self.statistics.list()
        meter_name = "meter_name"
        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.statistics = self.mox.CreateMockAnything()
        ceilometerclient.statistics.list(meter_name=meter_name,
                                         period=None, q=[]).\
            AndReturn(statistics)
        self.mox.ReplayAll()

        ret_list = api.ceilometer.statistic_list(self.request,
                                                 meter_name,
                                                 period=None,
                                                 query=[])
        for s in ret_list:
            self.assertIsInstance(s, api.ceilometer.Statistic)

    @test.create_stubs({api.nova: ('flavor_list',),
                        })
    def test_meters_list_all(self):
        meters = self.meters.list()

        request = self.mox.CreateMock(http.HttpRequest)
        api.nova.flavor_list(request, None).AndReturn([])

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list(None).AndReturn(meters)

        self.mox.ReplayAll()

        meters_object = api.ceilometer.Meters(self.request)

        ret_list = meters_object.list_all()

        for m in ret_list:
            self.assertIsInstance(m, api.ceilometer.Meter)

        self.assertEqual(3, len(ret_list))

        names = ["disk.read.bytes", "disk.write.bytes", "instance"]
        for ret in ret_list:
            self.assertIn(ret.name, names)
            names.remove(ret.name)

    @test.create_stubs({api.nova: ('flavor_list',),
                        })
    def test_meters_list_all_only(self):
        meters = self.meters.list()

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list(None).AndReturn(meters)

        request = self.mox.CreateMock(http.HttpRequest)
        api.nova.flavor_list(request, None).AndReturn([])
        self.mox.ReplayAll()

        meters_object = api.ceilometer.Meters(self.request)
        ret_list = meters_object.list_all(only_meters=["disk.read.bytes"])

        self.assertEqual(1, len(ret_list))
        self.assertEqual("disk.read.bytes", ret_list[0].name)

        ret_list = meters_object.list_all(only_meters=["disk.read.bytes",
                                                       "instance"])

        self.assertEqual(2, len(ret_list))
        self.assertEqual("disk.read.bytes", ret_list[0].name)
        self.assertEqual("instance", ret_list[1].name)

    @test.create_stubs({api.nova: ('flavor_list',),
                        })
    def test_meters_list_all_except(self):
        meters = self.meters.list()

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.meters = self.mox.CreateMockAnything()
        ceilometerclient.meters.list(None).AndReturn(meters)

        request = self.mox.CreateMock(http.HttpRequest)
        api.nova.flavor_list(request, None).AndReturn([])
        self.mox.ReplayAll()

        meters_object = api.ceilometer.Meters(self.request)
        ret_list = meters_object.list_all(except_meters=["disk.write.bytes",
                                                         "instance"])

        self.assertEqual(1, len(ret_list))
        self.assertEqual("disk.read.bytes", ret_list[0].name)

        ret_list = meters_object.list_all(except_meters=["disk.write.bytes"])

        self.assertEqual(len(ret_list), 2)
        names = ["disk.read.bytes", "instance"]

        for ret in ret_list:
            self.assertIn(ret.name, names)
            names.remove(ret.name)

    # TODO(lsmola) Test resource aggregates.

    @test.create_stubs({api.ceilometer.CeilometerUsage: ("get_user",
                                                         "get_tenant")})
    def test_global_data_get(self):
        class TempUsage(api.base.APIResourceWrapper):
            _attrs = ["id", "tenant", "user", "resource", "get_meter"]

            meters = ["fake_meter_1",
                      "fake_meter_2"]

            default_query = ["Fake query"]
            stats_attr = "max"

        resources = self.resources.list()
        statistics = self.statistics.list()
        user = self.ceilometer_users.list()[0]
        tenant = self.ceilometer_tenants.list()[0]

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        # I am returning only 1 resource
        ceilometerclient.resources.list(q=IsA(list)).AndReturn(resources[:1])

        ceilometerclient.statistics = self.mox.CreateMockAnything()
        # check that list is called twice for one resource and 2 meters
        ceilometerclient.statistics.list(meter_name=IsA(str),
                                         period=None, q=IsA(list)).\
            AndReturn(statistics)
        ceilometerclient.statistics.list(meter_name=IsA(str),
                                         period=None, q=IsA(list)).\
            AndReturn(statistics)

        api.ceilometer.CeilometerUsage\
            .get_user(IsA(str)).AndReturn(user)
        api.ceilometer.CeilometerUsage\
            .get_tenant(IsA(str)).AndReturn(tenant)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        ceilometer_usage = api.ceilometer.CeilometerUsage(http.HttpRequest)
        data = ceilometer_usage.global_data_get(
            used_cls=TempUsage, query=["fake_query"], with_statistics=True)

        first = data[0]
        self.assertEqual('fake_project_id__fake_user_id__'
                         'fake_resource_id',
                         first.id)
        self.assertEqual('user', first.user.name)
        self.assertEqual('test_tenant', first.tenant.name)
        self.assertEqual('fake_resource_id', first.resource)
        self.assertEqual(9, first.get_meter('fake_meter_1'),)
        self.assertEqual(9, first.get_meter('fake_meter_2'),)
        self.assertEqual(2, len(first.meters))
        # check that only one resource is returned
        self.assertEqual(1, len(data))

    @test.create_stubs({api.ceilometer.CeilometerUsage: ("get_user",
                                                         "get_tenant")})
    def test_global_data_get_without_statistic_data(self):
        class TempUsage(api.base.APIResourceWrapper):
            _attrs = ["id", "tenant", "user", "resource", "fake_meter_1",
                      "fake_meter_2"]

            meters = ["fake_meter_1",
                      "fake_meter_2"]

            default_query = ["Fake query"]
            stats_attr = "max"

        resources = self.resources.list()
        user = self.ceilometer_users.list()[0]
        tenant = self.ceilometer_tenants.list()[0]

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=IsA(list)).AndReturn(resources)

        api.ceilometer.CeilometerUsage\
            .get_user(IsA(str)).MultipleTimes().AndReturn(user)
        api.ceilometer.CeilometerUsage\
            .get_tenant(IsA(str)).MultipleTimes().AndReturn(tenant)

        self.mox.ReplayAll()

        # getting all resources and with statistics
        ceilometer_usage = api.ceilometer.CeilometerUsage(http.HttpRequest)
        data = ceilometer_usage.global_data_get(
            used_cls=TempUsage, query=["fake_query"], with_statistics=False)

        first = data[0]
        self.assertEqual('fake_project_id__fake_user_id__'
                         'fake_resource_id',
                         first.id)
        self.assertEqual('user', first.user.name)
        self.assertEqual('test_tenant', first.tenant.name)
        self.assertEqual('fake_resource_id', first.resource)

        self.assertRaises(AttributeError, getattr, first, 'fake_meter_1')
        self.assertRaises(AttributeError, getattr, first, 'fake_meter_2')

        self.assertEqual(len(resources), len(data))

    @test.create_stubs({api.ceilometer.CeilometerUsage: ("get_user",
                                                         "get_tenant")})
    def test_global_data_get_all_statistic_data(self):
        class TempUsage(api.base.APIResourceWrapper):
            _attrs = ["id", "tenant", "user", "resource", "get_meter", ]

            meters = ["fake_meter_1",
                      "fake_meter_2"]

            default_query = ["Fake query"]
            stats_attr = None  # have to return dictionary with all stats

        resources = self.resources.list()

        statistics = self.statistics.list()
        user = self.ceilometer_users.list()[0]
        tenant = self.ceilometer_tenants.list()[0]

        ceilometerclient = self.stub_ceilometerclient()
        ceilometerclient.resources = self.mox.CreateMockAnything()
        ceilometerclient.resources.list(q=IsA(list)).AndReturn(resources)

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
        ceilometer_usage = api.ceilometer.CeilometerUsage(http.HttpRequest)
        data = ceilometer_usage.global_data_get(
            used_cls=TempUsage, query=["fake_query"], with_statistics=True)

        first = data[0]
        self.assertEqual('fake_project_id__fake_user_id__'
                         'fake_resource_id',
                         first.id)
        self.assertEqual('user', first.user.name)
        self.assertEqual('test_tenant', first.tenant.name)
        self.assertEqual('fake_resource_id', first.resource)

        statistic_obj = api.ceilometer.Statistic(statistics[0])
        # check that it returns whole statistic object
        self.assertEqual(vars(first.get_meter('fake_meter_1')[0]),
                         vars(statistic_obj))
        self.assertEqual(vars(first.get_meter('fake_meter_2')[0]),
                         vars(statistic_obj))

        self.assertEqual(len(resources), len(data))
