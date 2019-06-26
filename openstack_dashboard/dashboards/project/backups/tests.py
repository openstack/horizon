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

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.http import urlunquote

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.backups \
    import tables as backup_tables
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:backups:index')


class VolumeBackupsViewTests(test.TestCase):

    @test.create_mocks({api.cinder: ('volume_list', 'volume_snapshot_list',
                                     'volume_backup_list_paged')})
    def _test_backups_index_paginated(self, marker, sort_dir, backups, url,
                                      has_more, has_prev):
        self.mock_volume_backup_list_paged.return_value = [backups,
                                                           has_more, has_prev]
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_volume_snapshot_list.return_value \
            = self.cinder_volume_snapshots.list()

        res = self.client.get(urlunquote(url))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.mock_volume_backup_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=marker, sort_dir=sort_dir,
            paginate=True)
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest())
        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_backups_index_paginated(self):
        backups = self.cinder_volume_backups.list()
        expected_snapshosts = self.cinder_volume_snapshots.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        next = backup_tables.BackupsTable._meta.pagination_param

        # get first page
        expected_backups = backups[:size]
        res = self._test_backups_index_paginated(
            marker=None, sort_dir="desc", backups=expected_backups,
            url=base_url, has_more=True, has_prev=False)
        result = res.context['volume_backups_table'].data
        self.assertItemsEqual(result, expected_backups)

        # get second page
        expected_backups = backups[size:2 * size]
        marker = expected_backups[0].id

        url = base_url + "?%s=%s" % (next, marker)
        res = self._test_backups_index_paginated(
            marker=marker, sort_dir="desc", backups=expected_backups, url=url,
            has_more=True, has_prev=True)
        result = res.context['volume_backups_table'].data
        self.assertItemsEqual(result, expected_backups)
        self.assertEqual(result[0].snapshot.id, expected_snapshosts[1].id)
        # get last page
        expected_backups = backups[-size:]
        marker = expected_backups[0].id
        url = base_url + "?%s=%s" % (next, marker)
        res = self._test_backups_index_paginated(
            marker=marker, sort_dir="desc", backups=expected_backups, url=url,
            has_more=False, has_prev=True)
        result = res.context['volume_backups_table'].data
        self.assertItemsEqual(result, expected_backups)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_backups_index_paginated_prev_page(self):
        backups = self.cinder_volume_backups.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        prev = backup_tables.BackupsTable._meta.prev_pagination_param

        # prev from some page
        expected_backups = backups[size:2 * size]
        marker = expected_backups[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_backups_index_paginated(
            marker=marker, sort_dir="asc", backups=expected_backups, url=url,
            has_more=True, has_prev=True)
        result = res.context['volume_backups_table'].data
        self.assertItemsEqual(result, expected_backups)

        # back to first page
        expected_backups = backups[:size]
        marker = expected_backups[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_backups_index_paginated(
            marker=marker, sort_dir="asc", backups=expected_backups, url=url,
            has_more=True, has_prev=False)
        result = res.context['volume_backups_table'].data
        self.assertItemsEqual(result, expected_backups)

    @test.create_mocks({api.cinder: ('volume_backup_create',
                                     'volume_snapshot_list',
                                     'volume_get')})
    def test_create_backup_available(self):
        volume = self.cinder_volumes.first()
        backup = self.cinder_volume_backups.first()

        self.mock_volume_get.return_value = volume
        self.mock_volume_backup_create.return_value = backup

        formData = {'method': 'CreateBackupForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'container_name': backup.container_name,
                    'name': backup.name,
                    'description': backup.description}
        url = reverse('horizon:project:volumes:create_backup',
                      args=[volume.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(),
            search_opts={'volume_id': volume.id})
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_backup_create.assert_called_once_with(
            test.IsHttpRequest(),
            volume.id,
            backup.container_name,
            backup.name,
            backup.description,
            force=False,
            snapshot_id=None)

    @test.create_mocks(
        {api.cinder: ('volume_backup_create', 'volume_snapshot_get',
                      'volume_get')})
    def test_create_backup_from_snapshot_table(self):
        backup = self.cinder_volume_backups.list()[1]
        volume = self.cinder_volumes.list()[4]
        snapshot = self.cinder_volume_snapshots.list()[1]
        self.mock_volume_backup_create.return_value = backup
        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_get.return_value = snapshot
        formData = {'method': 'CreateBackupForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'container_name': backup.container_name,
                    'name': backup.name,
                    'snapshot_id': backup.snapshot_id,
                    'description': backup.description}
        url = reverse('horizon:project:volumes:create_snapshot_backup',
                      args=[backup.volume_id, backup.snapshot_id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     backup.volume_id)
        self.mock_volume_backup_create.assert_called_once_with(
            test.IsHttpRequest(),
            backup.volume_id,
            backup.container_name,
            backup.name,
            backup.description,
            force=False,
            snapshot_id=backup.snapshot_id)

    @test.create_mocks(
        {api.cinder: ('volume_backup_create',
                      'volume_snapshot_list',
                      'volume_get')})
    def test_create_backup_from_snapshot_volume_table(self):
        volume = self.cinder_volumes.list()[4]
        backup = self.cinder_volume_backups.list()[1]
        snapshots = self.cinder_volume_snapshots.list()[1:3]
        self.mock_volume_backup_create.return_value = backup
        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_list.return_value = snapshots
        formData = {'method': 'CreateBackupForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'container_name': backup.container_name,
                    'name': backup.name,
                    'snapshot_id': snapshots[0].id,
                    'description': backup.description}
        url = reverse('horizon:project:volumes:create_backup',
                      args=[backup.volume_id])

        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(),
            search_opts={'volume_id': volume.id})
        self.assertMessageCount(error=0, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     backup.volume_id)
        self.mock_volume_backup_create.assert_called_once_with(
            test.IsHttpRequest(),
            backup.volume_id,
            backup.container_name,
            backup.name,
            backup.description,
            force=False,
            snapshot_id=backup.snapshot_id)

    @test.create_mocks(
        {api.cinder: ('volume_backup_create', 'volume_snapshot_list',
                      'volume_get')})
    def test_create_backup_in_use(self):
        # The third volume in the cinder test volume data is in-use
        volume = self.cinder_volumes.list()[2]

        backup = self.cinder_volume_backups.first()
        snapshots = []
        self.mock_volume_get.return_value = volume
        self.mock_volume_backup_create.return_value = backup
        self.mock_volume_snapshot_list.return_value = snapshots
        formData = {'method': 'CreateBackupForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'container_name': backup.container_name,
                    'name': backup.name,
                    'description': backup.description}
        url = reverse('horizon:project:volumes:create_backup',
                      args=[volume.id])

        res = self.client.post(url, formData)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(),
            search_opts={'volume_id': volume.id})
        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=0)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_backup_create.assert_called_once_with(
            test.IsHttpRequest(),
            volume.id,
            backup.container_name,
            backup.name,
            backup.description,
            force=True,
            snapshot_id=None)

    @test.create_mocks({api.cinder: ('volume_list',
                                     'volume_snapshot_list',
                                     'volume_backup_list_paged',
                                     'volume_backup_delete')})
    def test_delete_volume_backup(self):
        vol_backups = self.cinder_volume_backups.list()
        volumes = self.cinder_volumes.list()
        backup = self.cinder_volume_backups.first()
        snapshots = self.cinder_volume_snapshots.list()

        self.mock_volume_backup_list_paged.return_value = [vol_backups,
                                                           False, False]
        self.mock_volume_list.return_value = volumes
        self.mock_volume_backup_delete.return_value = None
        self.mock_volume_snapshot_list.return_value = snapshots
        formData = {'action':
                    'volume_backups__delete__%s' % backup.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_volume_backup_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None, sort_dir='desc',
            paginate=True)
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_backup_delete.assert_called_once_with(
            test.IsHttpRequest(), backup.id)

    @test.create_mocks({api.cinder: ('volume_backup_get',
                                     'volume_get')})
    def test_volume_backup_detail_get(self):
        backup = self.cinder_volume_backups.first()
        volume = self.cinder_volumes.get(id=backup.volume_id)

        self.mock_volume_backup_get.return_value = backup
        self.mock_volume_get.return_value = volume

        url = reverse('horizon:project:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['backup'].id, backup.id)
        self.mock_volume_backup_get.assert_called_once_with(
            test.IsHttpRequest(), backup.id)
        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), backup.volume_id)

    @test.create_mocks({api.cinder: ('volume_backup_get',
                                     'volume_snapshot_get',
                                     'volume_get')})
    def test_volume_backup_detail_get_with_snapshot(self):
        backup = self.cinder_volume_backups.list()[1]
        volume = self.cinder_volumes.get(id=backup.volume_id)

        self.mock_volume_backup_get.return_value = backup
        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_get.return_value \
            = self.cinder_volume_snapshots.list()[1]
        url = reverse('horizon:project:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['backup'].id, backup.id)
        self.assertEqual(res.context['snapshot'].id, backup.snapshot_id)
        self.mock_volume_backup_get.assert_called_once_with(
            test.IsHttpRequest(), backup.id)
        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), backup.volume_id)
        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), backup.snapshot_id)

    @test.create_mocks({api.cinder: ('volume_backup_get',)})
    def test_volume_backup_detail_get_with_exception(self):
        # Test to verify redirect if get volume backup fails
        backup = self.cinder_volume_backups.first()

        self.mock_volume_backup_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_volume_backup_get.assert_called_once_with(
            test.IsHttpRequest(), backup.id)

    @test.create_mocks({api.cinder: ('volume_backup_get',
                                     'volume_get')})
    def test_volume_backup_detail_with_missing_volume(self):
        # Test to check page still loads even if volume is deleted
        backup = self.cinder_volume_backups.first()

        self.mock_volume_backup_get.return_value = backup
        self.mock_volume_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['backup'].id, backup.id)
        self.mock_volume_backup_get.assert_called_once_with(
            test.IsHttpRequest(), backup.id)
        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), backup.volume_id)

    @test.create_mocks({api.cinder: ('volume_list',
                                     'volume_backup_restore')})
    def test_restore_backup(self):
        mock_backup = self.cinder_volume_backups.first()
        volumes = self.cinder_volumes.list()
        expected_volumes = [vol for vol in volumes
                            if vol.status == 'available']

        self.mock_volume_list.return_value = expected_volumes
        self.mock_volume_backup_restore.return_value = mock_backup

        formData = {'method': 'RestoreBackupForm',
                    'backup_id': mock_backup.id,
                    'backup_name': mock_backup.name,
                    'volume_id': mock_backup.volume_id}
        url = reverse('horizon:project:backups:restore',
                      args=[mock_backup.id])
        url += '?%s' % urlencode({'backup_name': mock_backup.name,
                                  'volume_id': mock_backup.volume_id})
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(info=1)
        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:project:volumes:index'))
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      {'status': 'available'})
        self.mock_volume_backup_restore.assert_called_once_with(
            test.IsHttpRequest(), mock_backup.id, mock_backup.volume_id)
