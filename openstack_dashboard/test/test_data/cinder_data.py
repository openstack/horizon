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
from openstack_dashboard.api import base
from openstack_dashboard.usage import quotas as usage_quotas

from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.cinder_quotas = utils.TestDataContainer()
    TEST.cinder_quota_usages = utils.TestDataContainer()

    # Quota Sets
    quota_data = dict(volumes='1',
                      snapshots='1',
                      gigabytes='1000')
    quota = quotas.QuotaSet(quotas.QuotaSetManager(None), quota_data)
    #TEST.quotas.cinder = QuotaSetWrapper(quota)
    TEST.cinder_quotas.add(base.QuotaSet(quota))

    # Quota Usages
    quota_usage_data = {'gigabytes': {'used': 0,
                                      'quota': 1000},
                        'instances': {'used': 0,
                                      'quota': 10},
                        'snapshots': {'used': 0,
                                      'quota': 10}}
    quota_usage = usage_quotas.QuotaUsage()
    for k, v in quota_usage_data.items():
        quota_usage.add_quota(base.Quota(k, v['quota']))
        quota_usage.tally(k, v['used'])

    TEST.cinder_quota_usages.add(quota_usage)
