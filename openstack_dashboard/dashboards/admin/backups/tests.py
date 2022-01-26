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

from urllib import parse

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import urlencode

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.backups \
    import tables as admin_tables
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:backups:index')


class AdminVolumeBackupsViewTests(test.BaseAdminViewTests):

    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.cinder: ['volume_list', 'volume_snapshot_list',
                     'volume_backup_list_paged_with_page_menu']})
    def _test_backups_index_paginated(self, page_number, backups,
                                      url, page_size, total_of_entries,
                                      number_of_pages, has_prev, has_more):
        self.mock_volume_backup_list_paged_with_page_menu.return_value = [
            backups, page_size, total_of_entries, number_of_pages]
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_volume_snapshot_list.return_value \
            = self.cinder_volume_snapshots.list()
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        res = self.client.get(parse.unquote(url))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertEqual(has_more,
                         res.context_data['view'].has_more_data(None))
        self.assertEqual(has_prev,
                         res.context_data['view'].has_prev_data(None))
        self.assertEqual(
            page_number, res.context_data['view'].current_page(None))
        self.assertEqual(
            number_of_pages, res.context_data['view'].number_of_pages(None))
        self.mock_volume_backup_list_paged_with_page_menu.\
            assert_called_once_with(test.IsHttpRequest(),
                                    page_number=page_number,
                                    all_tenants=True)
        self.mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': 1})
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(),
            search_opts={'all_tenants': 1})
        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_backups_index_paginated(self):
        backups = self.cinder_volume_backups.list()
        expected_snapshosts = self.cinder_volume_snapshots.list()
        size = settings.API_RESULT_PAGE_SIZE
        base_url = INDEX_URL
        number_of_pages = len(backups)
        pag = admin_tables.AdminBackupsTable._meta.pagination_param
        page_number = 1

        # get first page
        expected_backups = backups[:size]
        res = self._test_backups_index_paginated(
            page_number=page_number, backups=expected_backups, url=base_url,
            has_more=True, has_prev=False, page_size=size,
            number_of_pages=number_of_pages, total_of_entries=number_of_pages)
        result = res.context['volume_backups_table'].data
        self.assertCountEqual(result, expected_backups)

        # get second page
        expected_backups = backups[size:2 * size]
        page_number = 2
        url = base_url + "?%s=%s" % (pag, page_number)
        res = self._test_backups_index_paginated(
            page_number=page_number, backups=expected_backups, url=url,
            has_more=True, has_prev=True, page_size=size,
            number_of_pages=number_of_pages, total_of_entries=number_of_pages)
        result = res.context['volume_backups_table'].data
        self.assertCountEqual(result, expected_backups)
        self.assertEqual(result[0].snapshot.id, expected_snapshosts[1].id)
        # get last page
        expected_backups = backups[-size:]
        page_number = 3
        url = base_url + "?%s=%s" % (pag, page_number)
        res = self._test_backups_index_paginated(
            page_number=page_number, backups=expected_backups, url=url,
            has_more=False, has_prev=True, page_size=size,
            number_of_pages=number_of_pages, total_of_entries=number_of_pages)
        result = res.context['volume_backups_table'].data
        self.assertCountEqual(result, expected_backups)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_backups_index_paginated_prev_page(self):
        backups = self.cinder_volume_backups.list()
        size = settings.API_RESULT_PAGE_SIZE
        number_of_pages = len(backups)
        base_url = INDEX_URL
        pag = admin_tables.AdminBackupsTable._meta.pagination_param

        # prev from some page
        expected_backups = backups[size:2 * size]
        page_number = 2
        url = base_url + "?%s=%s" % (pag, page_number)
        res = self._test_backups_index_paginated(
            page_number=page_number, backups=expected_backups, url=url,
            has_more=True, has_prev=True, page_size=size,
            number_of_pages=number_of_pages, total_of_entries=number_of_pages)
        result = res.context['volume_backups_table'].data
        self.assertCountEqual(result, expected_backups)

        # back to first page
        expected_backups = backups[:size]
        page_number = 1
        url = base_url + "?%s=%s" % (pag, page_number)
        res = self._test_backups_index_paginated(
            page_number=page_number, backups=expected_backups, url=url,
            has_more=True, has_prev=False, page_size=size,
            number_of_pages=number_of_pages, total_of_entries=number_of_pages)
        result = res.context['volume_backups_table'].data
        self.assertCountEqual(result, expected_backups)

    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.cinder: ['volume_list',
                     'volume_snapshot_list',
                     'volume_backup_list_paged_with_page_menu',
                     'volume_backup_delete']})
    def test_delete_volume_backup(self):
        vol_backups = self.cinder_volume_backups.list()
        volumes = self.cinder_volumes.list()
        backup = self.cinder_volume_backups.first()
        snapshots = self.cinder_volume_snapshots.list()
        page_number = 1
        page_size = 1
        total_of_entries = 1
        number_of_pages = 1

        self.mock_volume_backup_list_paged_with_page_menu.return_value = [
            vol_backups, page_size, total_of_entries, number_of_pages]
        self.mock_volume_list.return_value = volumes
        self.mock_volume_backup_delete.return_value = None
        self.mock_volume_snapshot_list.return_value = snapshots
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        formData = {'action':
                    'volume_backups__delete__%s' % backup.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_volume_backup_list_paged_with_page_menu.\
            assert_called_once_with(test.IsHttpRequest(),
                                    page_number=page_number,
                                    all_tenants=True)
        self.mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': 1})
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': 1})
        self.mock_volume_backup_delete.assert_called_once_with(
            test.IsHttpRequest(), backup.id)

    @test.create_mocks({
        api.cinder: ['volume_backup_get',
                     'volume_get']})
    def test_volume_backup_detail_get(self):
        backup = self.cinder_volume_backups.first()
        volume = self.cinder_volumes.get(id=backup.volume_id)

        self.mock_volume_backup_get.return_value = backup
        self.mock_volume_get.return_value = volume

        url = reverse('horizon:admin:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['backup'].id, backup.id)
        self.mock_volume_backup_get.assert_called_once_with(
            test.IsHttpRequest(), backup.id)
        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), backup.volume_id)

    @test.create_mocks({
        api.cinder: ['volume_backup_get',
                     'volume_snapshot_get',
                     'volume_get']})
    def test_volume_backup_detail_get_with_snapshot(self):
        backup = self.cinder_volume_backups.list()[1]
        volume = self.cinder_volumes.get(id=backup.volume_id)

        self.mock_volume_backup_get.return_value = backup
        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_get.return_value \
            = self.cinder_volume_snapshots.list()[1]
        url = reverse('horizon:admin:backups:detail',
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

        url = reverse('horizon:admin:backups:detail',
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

        url = reverse('horizon:admin:backups:detail',
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
        url = reverse('horizon:admin:backups:restore',
                      args=[mock_backup.id])
        url += '?%s' % urlencode({'backup_name': mock_backup.name,
                                  'volume_id': mock_backup.volume_id})
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(info=1)
        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:admin:volumes:index'))
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      {'status': 'available'})
        self.mock_volume_backup_restore.assert_called_once_with(
            test.IsHttpRequest(), mock_backup.id, mock_backup.volume_id)

    @test.create_mocks({api.cinder: ('volume_backup_get',
                                     'volume_backup_reset_state')})
    def test_update_volume_backup_status(self):
        backup = self.cinder_volume_backups.first()
        form_data = {'status': 'error'}

        self.mock_volume_backup_reset_state.return_value = None
        self.mock_volume_backup_get.return_value = backup

        res = self.client.post(
            reverse('horizon:admin:backups:update_status',
                    args=(backup.id,)), form_data)

        self.mock_volume_backup_reset_state.assert_called_once_with(
            test.IsHttpRequest(), backup.id, form_data['status'])
        self.mock_volume_backup_get.assert_called_once_with(
            test.IsHttpRequest(), backup.id)
        self.assertNoFormErrors(res)
