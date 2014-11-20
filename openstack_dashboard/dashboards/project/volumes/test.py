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


INDEX_URL = reverse('horizon:project:volumes:index')
VOLUME_SNAPSHOTS_TAB_URL = reverse('horizon:project:volumes:snapshots_tab')
VOLUME_BACKUPS_TAB_URL = reverse('horizon:project:volumes:backups_tab')


class VolumeAndSnapshotsTests(test.TestCase):
    @test.create_stubs({api.cinder: ('tenant_absolute_limits',
                                     'volume_list',
                                     'volume_snapshot_list',
                                     'volume_backup_supported',
                                     'volume_backup_list',
                                     ),
                        api.nova: ('server_list',)})
    def _test_index(self, backup_supported=True):
        vol_backups = self.cinder_volume_backups.list()
        vol_snaps = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()

        api.cinder.volume_backup_supported(IsA(http.HttpRequest)).\
            MultipleTimes().AndReturn(backup_supported)
        api.cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn(volumes)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn([self.servers.list(), False])
        api.cinder.volume_snapshot_list(
            IsA(http.HttpRequest), search_opts=None).AndReturn(vol_snaps)
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(vol_snaps)
        api.cinder.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)
        if backup_supported:
            api.cinder.volume_backup_list(IsA(http.HttpRequest)).\
                AndReturn(vol_backups)
            api.cinder.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)).\
            MultipleTimes().AndReturn(self.cinder_limits['absolute'])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'project/volumes/index.html')

        # Explicitly load the other tabs. If this doesn't work the test
        # will fail due to "Expected methods never called."
        res = self.client.get(VOLUME_SNAPSHOTS_TAB_URL)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'project/volumes/index.html')

        if backup_supported:
            res = self.client.get(VOLUME_BACKUPS_TAB_URL)
            self.assertTemplateUsed(res, 'project/volumes/index.html')

    def test_index_backup_supported(self):
        self._test_index(backup_supported=True)

    def test_index_backup_not_supported(self):
        self._test_index(backup_supported=False)
