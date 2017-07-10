# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from django.utils.http import urlunquote
from mox3.mox import IsA

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.project.snapshots \
    import tables as snapshot_tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:snapshots:index')


class VolumeSnapshotsViewTests(test.TestCase):
    @test.create_stubs({api.cinder: ('tenant_absolute_limits',
                                     'volume_snapshot_list_paged',
                                     'volume_list',),
                        api.base: ('is_service_enabled',)})
    def _test_snapshots_index_paginated(self, marker, sort_dir, snapshots, url,
                                        has_more, has_prev):
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volumev2') \
            .AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
            .AndReturn(True)
        api.cinder.volume_snapshot_list_paged(
            IsA(http.HttpRequest), marker=marker, sort_dir=sort_dir,
            paginate=True).AndReturn([snapshots, has_more, has_prev])
        api.cinder.volume_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_volumes.list())
        self.mox.ReplayAll()

        res = self.client.get(urlunquote(url))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

        self.mox.UnsetStubs()
        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated(self):
        mox_snapshots = self.cinder_volume_snapshots.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        next = snapshot_tables.VolumeSnapshotsTable._meta.pagination_param

        # get first page
        expected_snapshots = mox_snapshots[:size]
        res = self._test_snapshots_index_paginated(
            marker=None, sort_dir="desc", snapshots=expected_snapshots,
            url=base_url, has_more=True, has_prev=False)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # get second page
        expected_snapshots = mox_snapshots[size:2 * size]
        marker = expected_snapshots[0].id

        url = base_url + "?%s=%s" % (next, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="desc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # get last page
        expected_snapshots = mox_snapshots[-size:]
        marker = expected_snapshots[0].id
        url = base_url + "?%s=%s" % (next, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="desc", snapshots=expected_snapshots,
            url=url, has_more=False, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated_prev_page(self):
        mox_snapshots = self.cinder_volume_snapshots.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        prev = snapshot_tables.VolumeSnapshotsTable._meta.prev_pagination_param

        # prev from some page
        expected_snapshots = mox_snapshots[size:2 * size]
        marker = expected_snapshots[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # back to first page
        expected_snapshots = mox_snapshots[:size]
        marker = expected_snapshots[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=False)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

    @test.create_stubs({cinder: ('volume_get',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_snapshot_get(self):
        volume = self.cinder_volumes.first()
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        snapshot_used = len(self.cinder_volume_snapshots.list())
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'totalGigabytesUsed': 20,
                       'totalSnapshotsUsed': snapshot_used,
                       'maxTotalSnapshots': 6}
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
            AndReturn(usage_limit)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/volumes/create_snapshot.html')

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_snapshot_create',)})
    def test_create_snapshot_post(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.name,
                                      snapshot.description,
                                      force=False) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_snapshot_create',)})
    def test_force_create_snapshot(self):
        volume = self.cinder_volumes.get(name='my_volume')
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.name,
                                      snapshot.description,
                                      force=True) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.cinder: ('volume_snapshot_list_paged',
                                     'volume_list',
                                     'volume_snapshot_delete',
                                     'tenant_absolute_limits')})
    def test_delete_volume_snapshot(self):
        vol_snapshots = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_snapshot_list_paged(
            IsA(http.HttpRequest), paginate=True, marker=None,
            sort_dir='desc').AndReturn([vol_snapshots, False, False])
        api.cinder.volume_list(IsA(http.HttpRequest)). \
            AndReturn(volumes)

        api.cinder.volume_snapshot_delete(IsA(http.HttpRequest), snapshot.id)
        self.mox.ReplayAll()

        formData = {'action': 'volume_snapshots__delete__%s' % snapshot.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.cinder: ('volume_snapshot_get', 'volume_get')})
    def test_volume_snapshot_detail_get(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndReturn(volume)
        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)
        api.cinder.volume_get(IsA(http.HttpRequest), snapshot.volume_id). \
            AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['snapshot'].id, snapshot.id)

    @test.create_stubs({api.cinder: ('volume_snapshot_get',)})
    def test_volume_snapshot_detail_get_with_exception(self):
        # Test to verify redirect if get volume snapshot fails
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id).\
            AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.cinder: ('volume_snapshot_get', 'volume_get')})
    def test_volume_snapshot_detail_with_volume_get_exception(self):
        # Test to verify redirect if get volume fails
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndRaise(self.exceptions.cinder)
        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:project:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('volume_snapshot_update',
                                 'volume_snapshot_get')})
    def test_update_snapshot(self):
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id) \
            .AndReturn(snapshot)
        cinder.volume_snapshot_update(IsA(http.HttpRequest),
                                      snapshot.id,
                                      snapshot.name,
                                      snapshot.description) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'UpdateSnapshotForm',
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse(('horizon:project:snapshots:update'),
                      args=[snapshot.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)
