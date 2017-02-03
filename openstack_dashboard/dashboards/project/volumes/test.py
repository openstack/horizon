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

import copy

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings
from django.utils.http import urlunquote

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.volumes.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:volumes:index')


class VolumeAndSnapshotsAndBackupsTests(test.TestCase):
    @test.create_stubs({api.cinder: ('tenant_absolute_limits',
                                     'volume_list',
                                     'volume_list_paged',
                                     'volume_snapshot_list',
                                     'volume_backup_supported',
                                     'volume_backup_list_paged',
                                     ),
                        api.nova: ('server_list',)})
    def test_index(self, instanceless_volumes=False):
        vol_snaps = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()
        if instanceless_volumes:
            for volume in volumes:
                volume.attachments = []

        api.cinder.volume_backup_supported(IsA(http.HttpRequest)).\
            MultipleTimes().AndReturn(False)
        api.cinder.volume_list_paged(
            IsA(http.HttpRequest), marker=None, search_opts=None,
            sort_dir='desc', paginate=True).\
            AndReturn([volumes, False, False])
        if not instanceless_volumes:
            api.nova.server_list(IsA(http.HttpRequest), search_opts=None,
                                 detailed=False).\
                AndReturn([self.servers.list(), False])
            api.cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                AndReturn(vol_snaps)

        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)).\
            MultipleTimes().AndReturn(self.cinder_limits['absolute'])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'project/volumes/index.html')

    def test_index_no_volume_attachments(self):
        self.test_index(instanceless_volumes=True)

    @test.create_stubs({api.cinder: ('tenant_absolute_limits',
                                     'volume_list_paged',
                                     'volume_backup_supported',
                                     'volume_snapshot_list'),
                        api.nova: ('server_list',)})
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev):
        backup_supported = True
        vol_snaps = self.cinder_volume_snapshots.list()

        api.cinder.volume_backup_supported(IsA(http.HttpRequest)).\
            MultipleTimes().AndReturn(backup_supported)
        api.cinder.volume_list_paged(IsA(http.HttpRequest), marker=marker,
                                     sort_dir=sort_dir, search_opts=None,
                                     paginate=True).\
            AndReturn([volumes, has_more, has_prev])
        api.cinder.volume_snapshot_list(
            IsA(http.HttpRequest), search_opts=None).AndReturn(vol_snaps)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None,
                             detailed=False).\
            AndReturn([self.servers.list(), False])
        api.cinder.tenant_absolute_limits(IsA(http.HttpRequest)).MultipleTimes().\
            AndReturn(self.cinder_limits['absolute'])
        self.mox.ReplayAll()

        res = self.client.get(urlunquote(url))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'project/volumes/index.html')

        self.mox.UnsetStubs()
        return res

    def ensure_attachments_exist(self, volumes):
        volumes = copy.copy(volumes)
        for volume in volumes:
            if not volume.attachments:
                volume.attachments.append({
                    "id": "1", "server_id": '1', "device": "/dev/hda"})
        return volumes

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated(self):
        mox_volumes = self.ensure_attachments_exist(self.cinder_volumes.list())
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
        mox_volumes = self.ensure_attachments_exist(self.cinder_volumes.list())
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
