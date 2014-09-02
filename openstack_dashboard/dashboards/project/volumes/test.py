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

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.volumes.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:volumes:index')
VOLUME_SNAPSHOTS_TAB_URL = reverse('horizon:project:volumes:snapshots_tab')
VOLUME_BACKUPS_TAB_URL = reverse('horizon:project:volumes:backups_tab')


class VolumeAndSnapshotsTests(test.TestCase):
    @test.create_stubs({api.cinder: ('tenant_absolute_limits',
                                     'volume_list',
                                     'volume_list_paged',
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
        api.cinder.volume_list_paged(IsA(http.HttpRequest), marker=None,
                                     sort_dir='desc', search_opts=None,
                                     paginate=True).\
            AndReturn([volumes, False, False])
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

    @test.create_stubs({api.cinder: ('tenant_absolute_limits',
                                     'volume_list_paged',
                                     'volume_backup_supported',
                                     ),
                        api.nova: ('server_list',)})
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev):
        backup_supported = True

        api.cinder.volume_backup_supported(IsA(http.HttpRequest)).\
            MultipleTimes().AndReturn(backup_supported)
        api.cinder.volume_list_paged(IsA(http.HttpRequest), marker=marker,
                                     sort_dir=sort_dir, search_opts=None,
                                     paginate=True).\
            AndReturn([volumes, has_more, has_prev])
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn([self.servers.list(), False])
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)).MultipleTimes().\
            AndReturn(self.cinder_limits['absolute'])
        self.mox.ReplayAll()

        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'project/volumes/index.html')

        self.mox.UnsetStubs()
        return res

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated(self):
        mox_volumes = self.cinder_volumes.list()
        size = settings.API_RESULT_PAGE_SIZE

        # get first page
        expected_volumes = mox_volumes[:size]
        url = INDEX_URL
        res = self._test_index_paginated(marker=None, sort_dir="desc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=False)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # get second page
        expected_volumes = mox_volumes[size:2 * size]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = "?".join([INDEX_URL, "=".join([next, marker])])
        res = self._test_index_paginated(marker=marker, sort_dir="desc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # get last page
        expected_volumes = mox_volumes[-size:]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = "?".join([INDEX_URL, "=".join([next, marker])])
        res = self._test_index_paginated(marker=marker, sort_dir="desc",
                                         volumes=expected_volumes, url=url,
                                         has_more=False, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated_prev_page(self):
        mox_volumes = self.cinder_volumes.list()
        size = settings.API_RESULT_PAGE_SIZE

        # prev from some page
        expected_volumes = mox_volumes[size:2 * size]
        marker = expected_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = "?".join([INDEX_URL, "=".join([prev, marker])])
        res = self._test_index_paginated(marker=marker, sort_dir="asc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # back to first page
        expected_volumes = mox_volumes[:size]
        marker = expected_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = "?".join([INDEX_URL, "=".join([prev, marker])])
        res = self._test_index_paginated(marker=marker, sort_dir="asc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=False)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)
