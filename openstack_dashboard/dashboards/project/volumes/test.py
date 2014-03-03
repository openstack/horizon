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

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:volumes:index')


class VolumeAndSnapshotsTests(test.TestCase):
    @test.create_stubs({api.cinder: ('volume_list',
                                     'volume_snapshot_list',),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        vol_snaps = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()

        api.cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn(volumes)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn([self.servers.list(), False])
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(vol_snaps)
        api.cinder.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).MultipleTimes(). \
            AndReturn(self.quota_usages.first())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'project/volumes/index.html')
