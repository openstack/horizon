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
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import urlunquote
import mock

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.snapshots \
    import tables as snapshot_tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:snapshots:index')


class VolumeSnapshotsViewTests(test.TestCase):
    @test.create_mocks({api.cinder: ('volume_snapshot_list_paged',
                                     'volume_list',
                                     'group_snapshot_list'),
                        api.base: ('is_service_enabled',)})
    def _test_snapshots_index_paginated(self, marker, sort_dir, snapshots, url,
                                        has_more, has_prev, with_groups=False):
        self.mock_is_service_enabled.return_value = True
        self.mock_volume_snapshot_list_paged.return_value = [snapshots,
                                                             has_more,
                                                             has_prev]
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_group_snapshot_list.return_value = \
            self.cinder_volume_snapshots_with_groups.list()

        res = self.client.get(urlunquote(url))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_service_enabled, 2,
            mock.call(test.IsHttpRequest(), 'volumev3'))
        self.mock_volume_snapshot_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=marker, sort_dir=sort_dir,
            paginate=True)
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest())

        if with_groups:
            self.mock_group_snapshot_list.assert_called_once_with(
                test.IsHttpRequest())

        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated(self):
        mock_snapshots = self.cinder_volume_snapshots.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        next = snapshot_tables.VolumeSnapshotsTable._meta.pagination_param

        # get first page
        expected_snapshots = mock_snapshots[:size]
        res = self._test_snapshots_index_paginated(
            marker=None, sort_dir="desc", snapshots=expected_snapshots,
            url=base_url, has_more=True, has_prev=False)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # get second page
        expected_snapshots = mock_snapshots[size:2 * size]
        marker = expected_snapshots[0].id

        url = base_url + "?%s=%s" % (next, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="desc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # get last page
        expected_snapshots = mock_snapshots[-size:]
        marker = expected_snapshots[0].id
        url = base_url + "?%s=%s" % (next, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="desc", snapshots=expected_snapshots,
            url=url, has_more=False, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_with_group(self):
        mock_snapshots = self.cinder_volume_snapshots_with_groups.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL

        # get first page
        expected_snapshots = mock_snapshots[:size]
        res = self._test_snapshots_index_paginated(
            marker=None, sort_dir="desc", snapshots=expected_snapshots,
            url=base_url, has_more=False, has_prev=False, with_groups=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, mock_snapshots)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated_prev_page(self):
        mock_snapshots = self.cinder_volume_snapshots.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        prev = snapshot_tables.VolumeSnapshotsTable._meta.prev_pagination_param

        # prev from some page
        expected_snapshots = mock_snapshots[size:2 * size]
        marker = expected_snapshots[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # back to first page
        expected_snapshots = mock_snapshots[:size]
        marker = expected_snapshots[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=False)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

    @test.create_mocks({api.cinder: ('volume_get',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_snapshot_get(self):
        volume = self.cinder_volumes.first()
        self.mock_volume_get.return_value = volume
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()

        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/volumes/create_snapshot.html')
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_tenant_quota_usages.assert_called_once_with(
            test.IsHttpRequest(),
            targets=('snapshots', 'gigabytes'))

    @test.create_mocks({api.cinder: ('volume_get',
                                     'volume_snapshot_create')})
    def test_create_snapshot_post(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_create.return_value = snapshot

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_snapshot_create.assert_called_once_with(
            test.IsHttpRequest(),
            volume.id,
            snapshot.name,
            snapshot.description,
            force=False)

    @test.create_mocks({api.cinder: ('volume_get',
                                     'volume_snapshot_create')})
    def test_force_create_snapshot(self):
        volume = self.cinder_volumes.get(name='my_volume')
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_create.return_value = snapshot

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_snapshot_create.assert_called_once_with(
            test.IsHttpRequest(),
            volume.id,
            snapshot.name,
            snapshot.description,
            force=True)

    @test.create_mocks({api.cinder: ('volume_snapshot_list_paged',
                                     'volume_list',
                                     'volume_snapshot_delete')})
    def test_delete_volume_snapshot(self):
        vol_snapshots = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_snapshot_list_paged.return_value = [vol_snapshots,
                                                             False, False]
        self.mock_volume_list.return_value = volumes
        self.mock_volume_snapshot_delete.return_value = None

        formData = {'action': 'volume_snapshots__delete__%s' % snapshot.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

        self.mock_volume_snapshot_list_paged.assert_called_once_with(
            test.IsHttpRequest(), paginate=True, marker=None, sort_dir='desc')
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), snapshot.id)

    @test.create_mocks({api.cinder: ('volume_get',
                                     'volume_snapshot_get')})
    def test_volume_snapshot_detail_get(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_get.return_value = snapshot

        url = reverse('horizon:project:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['snapshot'].id, snapshot.id)

        self.mock_volume_get.assert_has_calls([
            mock.call(test.IsHttpRequest(), volume.id),
            mock.call(test.IsHttpRequest(), snapshot.volume_id),
        ])
        self.assertEqual(2, self.mock_volume_get.call_count)
        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), snapshot.id)

    @test.create_mocks({api.cinder: ('volume_snapshot_get',)})
    def test_volume_snapshot_detail_get_with_exception(self):
        # Test to verify redirect if get volume snapshot fails
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_snapshot_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), snapshot.id)

    @test.create_mocks({api.cinder: ('volume_get',
                                     'volume_snapshot_get')})
    def test_volume_snapshot_detail_with_volume_get_exception(self):
        # Test to verify redirect if get volume fails
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_get.side_effect = self.exceptions.cinder
        self.mock_volume_snapshot_get.return_value = snapshot

        url = reverse('horizon:project:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), snapshot.id)

    @test.create_mocks({api.cinder: ('volume_snapshot_update',
                                     'volume_snapshot_get')})
    def test_update_snapshot(self):
        snapshot = self.cinder_volume_snapshots.first()

        self.mock_volume_snapshot_get.return_value = snapshot
        self.mock_volume_snapshot_update.return_value = snapshot

        formData = {'method': 'UpdateSnapshotForm',
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse(('horizon:project:snapshots:update'),
                      args=[snapshot.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), snapshot.id)
        self.mock_volume_snapshot_update.assert_called_once_with(
            test.IsHttpRequest(),
            snapshot.id,
            snapshot.name,
            snapshot.description)
