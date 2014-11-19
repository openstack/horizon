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

from ceilometerclient.v2 import meters
from ceilometerclient.v2 import resources
from ceilometerclient.v2 import samples
from ceilometerclient.v2 import statistics

from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import users

from openstack_dashboard.api import ceilometer
from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.ceilometer_users = utils.TestDataContainer()
    TEST.ceilometer_tenants = utils.TestDataContainer()
    TEST.resources = utils.TestDataContainer()
    TEST.api_resources = utils.TestDataContainer()
    TEST.samples = utils.TestDataContainer()
    TEST.meters = utils.TestDataContainer()
    TEST.statistics = utils.TestDataContainer()
    TEST.global_disk_usages = utils.TestDataContainer()
    TEST.global_network_usages = utils.TestDataContainer()
    TEST.global_network_traffic_usages = utils.TestDataContainer()
    TEST.global_object_store_usages = utils.TestDataContainer()
    TEST.statistics_array = utils.TestDataContainer()

    # users
    ceilometer_user_dict1 = {'id': "1",
                             'name': 'user',
                             'email': 'test@example.com',
                             'password': 'password',
                             'token': 'test_token',
                             'project_id': '1',
                             'enabled': True,
                             'domain_id': "1"}
    ceilometer_user_dict2 = {'id': "2",
                             'name': 'user2',
                             'email': 'test2@example.com',
                             'password': 'password',
                             'token': 'test_token',
                             'project_id': '2',
                             'enabled': True,
                             'domain_id': "2"}
    TEST.ceilometer_users.add(users.User(None,
                                         ceilometer_user_dict1))
    TEST.ceilometer_users.add(users.User(None,
                                         ceilometer_user_dict2))

    # Tenants.
    tenant_dict = {'id': "1",
                   'name': 'test_tenant',
                   'description': "a test tenant.",
                   'enabled': True,
                   'domain_id': '1'}
    tenant_dict_2 = {'id': "2",
                     'name': 'disabled_tenant',
                     'description': "a disabled test tenant.",
                     'enabled': False,
                     'domain_id': '2'}
    tenant_dict_3 = {'id': "3",
                     'name': u'\u4e91\u89c4\u5219',
                     'description': "an unicode-named tenant.",
                     'enabled': True,
                     'domain_id': '2'}
    ceilometer_tenant = tenants.Tenant(tenants.TenantManager,
                                       tenant_dict)
    ceilometer_disabled_tenant = tenants.Tenant(tenants.TenantManager,
                                                tenant_dict_2)
    ceilometer_tenant_unicode = tenants.Tenant(tenants.TenantManager,
                                               tenant_dict_3)

    TEST.ceilometer_tenants.add(ceilometer_tenant,
                                ceilometer_disabled_tenant,
                                ceilometer_tenant_unicode)

    # resources
    resource_dict_1 = dict(
        resource_id='fake_resource_id',
        project_id='fake_project_id',
        user_id="fake_user_id",
        timestamp='2012-07-02T10:42:00.000000',
        metadata={'tag': 'self.counter3', 'display_name': 'test-server'},
        links=[{'url': 'test_url', 'rel': 'storage.objects'}],
    )
    resource_dict_2 = dict(
        resource_id='fake_resource_id2',
        project_id='fake_project_id',
        user_id="fake_user_id",
        timestamp='2012-07-02T10:42:00.000000',
        metadata={'tag': 'self.counter3', 'display_name': 'test-server'},
        links=[{'url': 'test_url', 'rel': 'storage.objects'}],
    )
    resource_dict_3 = dict(
        resource_id='fake_resource_id3',
        project_id='fake_project_id',
        user_id="fake_user_id",
        timestamp='2012-07-02T10:42:00.000000',
        metadata={'tag': 'self.counter3', 'display_name': 'test-server'},
        links=[{'url': 'test_url', 'rel': 'instance'}],
    )
    resource_dict_4 = dict(
        resource_id='fake_resource_id3',
        project_id='fake_project_id',
        user_id="fake_user_id",
        timestamp='2012-07-02T10:42:00.000000',
        metadata={'tag': 'self.counter3', 'display_name': 'test-server'},
        links=[{'url': 'test_url', 'rel': 'memory'}],
    )

    resource_1 = resources.Resource(resources.ResourceManager(None),
                                    resource_dict_1)
    resource_2 = resources.Resource(resources.ResourceManager(None),
                                    resource_dict_2)
    resource_3 = resources.Resource(resources.ResourceManager(None),
                                    resource_dict_3)
    resource_4 = resources.Resource(resources.ResourceManager(None),
                                    resource_dict_4)

    TEST.resources.add(resource_1)
    TEST.resources.add(resource_2)
    TEST.resources.add(resource_3)

    # Having a separate set of fake objects for openstack_dashboard
    # api Resource class. This is required because of additional methods
    # defined in openstack_dashboard.api.ceilometer.Resource

    api_resource_1 = ceilometer.Resource(resource_1)
    api_resource_2 = ceilometer.Resource(resource_2)
    api_resource_3 = ceilometer.Resource(resource_3)
    api_resource_4 = ceilometer.Resource(resource_4)

    TEST.api_resources.add(api_resource_1)
    TEST.api_resources.add(api_resource_2)
    TEST.api_resources.add(api_resource_3)
    TEST.api_resources.add(api_resource_4)

    # samples
    sample_dict_1 = {'resource_id': 'fake_resource_id',
                     'project_id': 'fake_project_id',
                     'user_id': 'fake_user_id',
                     'counter_name': 'image',
                     'counter_type': 'gauge',
                     'counter_unit': 'image',
                     'counter_volume': 1,
                     'timestamp': '2012-12-21T11:00:55.000000',
                     'metadata': {'name1': 'value1', 'name2': 'value2'},
                     'message_id': 'fake_message_id'}
    sample_dict_2 = {'resource_id': 'fake_resource_id2',
                     'project_id': 'fake_project_id',
                     'user_id': 'fake_user_id',
                     'counter_name': 'image',
                     'counter_type': 'gauge',
                     'counter_unit': 'image',
                     'counter_volume': 1,
                     'timestamp': '2012-12-21T11:00:55.000000',
                     'metadata': {'name1': 'value1', 'name2': 'value2'},
                     'message_id': 'fake_message_id'}
    sample_1 = samples.Sample(samples.SampleManager(None), sample_dict_1)
    sample_2 = samples.Sample(samples.SampleManager(None), sample_dict_2)
    TEST.samples.add(sample_1)
    TEST.samples.add(sample_2)

    # meters
    meter_dict_1 = {'name': 'instance',
                    'type': 'gauge',
                    'unit': 'instance',
                    'resource_id': 'fake_resource_id',
                    'project_id': 'fake_project_id',
                    'user_id': 'fake_user_id'}
    meter_dict_2 = {'name': 'instance',
                    'type': 'gauge',
                    'unit': 'instance',
                    'resource_id': 'fake_resource_id',
                    'project_id': 'fake_project_id',
                    'user_id': 'fake_user_id'}
    meter_dict_3 = {'name': 'disk.read.bytes',
                    'type': 'gauge',
                    'unit': 'instance',
                    'resource_id': 'fake_resource_id',
                    'project_id': 'fake_project_id',
                    'user_id': 'fake_user_id'}
    meter_dict_4 = {'name': 'disk.write.bytes',
                    'type': 'gauge',
                    'unit': 'instance',
                    'resource_id': 'fake_resource_id',
                    'project_id': 'fake_project_id',
                    'user_id': 'fake_user_id'}
    meter_1 = meters.Meter(meters.MeterManager(None), meter_dict_1)
    meter_2 = meters.Meter(meters.MeterManager(None), meter_dict_2)
    meter_3 = meters.Meter(meters.MeterManager(None), meter_dict_3)
    meter_4 = meters.Meter(meters.MeterManager(None), meter_dict_4)
    TEST.meters.add(meter_1)
    TEST.meters.add(meter_2)
    TEST.meters.add(meter_3)
    TEST.meters.add(meter_4)

    # statistic
    statistic_dict_1 = {'min': 1,
                        'max': 9,
                        'avg': 4.55,
                        'sum': 45,
                        'count': 10,
                        'duration_start': '2012-12-21T11:00:55.000000',
                        'duration_end': '2012-12-21T11:00:55.000000',
                        'period': 7200,
                        'period_start': '2012-12-21T11:00:55.000000',
                        'period_end': '2012-12-21T11:00:55.000000'}
    statistic_1 = statistics.Statistics(statistics.StatisticsManager(None),
                                        statistic_dict_1)
    TEST.statistics.add(statistic_1)
