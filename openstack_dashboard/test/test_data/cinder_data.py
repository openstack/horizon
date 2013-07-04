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

from cinderclient.v1 import quotas
from openstack_dashboard.api.base import Quota
from openstack_dashboard.api.base import QuotaSet as QuotaSetWrapper
from openstack_dashboard.usage.quotas import QuotaUsage

from openstack_dashboard.test.test_data.utils import TestDataContainer


def data(TEST):
    TEST.cinder_quotas = TestDataContainer()
    TEST.cinder_quota_usages = TestDataContainer()

    # Quota Sets
    quota_data = dict(volumes='1',
                      snapshots='1',
                      gigabytes='1000')
    quota = quotas.QuotaSet(quotas.QuotaSetManager(None), quota_data)
    #TEST.quotas.cinder = QuotaSetWrapper(quota)
    TEST.cinder_quotas.add(QuotaSetWrapper(quota))

    # Quota Usages
    quota_usage_data = {'gigabytes': {'used': 0,
                                      'quota': 1000},
                        'instances': {'used': 0,
                                      'quota': 10},
                        'snapshots': {'used': 0,
                                      'quota': 10}}
    quota_usage = QuotaUsage()
    for k, v in quota_usage_data.items():
        quota_usage.add_quota(Quota(k, v['quota']))
        quota_usage.tally(k, v['used'])

    TEST.cinder_quota_usages.add(quota_usage)
