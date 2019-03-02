# Copyright 2019 NEC Corporation
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

from django.urls import reverse
import mock

from openstack_dashboard import api

from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:admin:vg_snapshots:index')
INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class AdminGroupSnapshotTests(test.BaseAdminViewTests):
    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.cinder: ['group_list',
                     'group_snapshot_list']})
    def test_index(self):
        vg_snapshots = self.cinder_group_snapshots.list()
        groups = self.cinder_groups.list()
        tenants = self.tenants.list()
        self.mock_group_snapshot_list.return_value = vg_snapshots
        self.mock_group_list.return_value = groups
        self.mock_tenant_list.return_value = [tenants, False]

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertIn('volume_vg_snapshots_table', res.context)
        volume_vg_snapshots_table = res.context['volume_vg_snapshots_table']
        volume_vg_snapshots = volume_vg_snapshots_table.data
        self.assertEqual(len(volume_vg_snapshots), 1)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_group_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), {'all_tenants': 1})
        self.mock_group_list.assert_called_once_with(
            test.IsHttpRequest(), {'all_tenants': 1})

    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.cinder: ['group_list',
                     'group_snapshot_delete',
                     'group_snapshot_list']})
    def test_delete_group_snapshot(self):
        vg_snapshots = self.cinder_group_snapshots.list()
        vg_snapshot = self.cinder_group_snapshots.first()
        tenants = self.tenants.list()
        self.mock_group_snapshot_list.return_value = vg_snapshots
        self.mock_group_snapshot_delete.return_value = None
        self.mock_group_list.return_value = self.cinder_groups.list()
        self.mock_tenant_list.return_value = [tenants, False]

        form_data = {'action': 'volume_vg_snapshots__delete_vg_snapshot__%s'
                     % vg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Scheduled deletion of Snapshot: %s" % vg_snapshot.name,
                      [m.message for m in res.context['messages']])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_group_snapshot_list, 2,
            mock.call(test.IsHttpRequest(), {'all_tenants': 1}))
        self.mock_group_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_group_list, 2,
            mock.call(test.IsHttpRequest(), {'all_tenants': 1}))

    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.cinder: ['group_list',
                     'group_snapshot_delete',
                     'group_snapshot_list']})
    def test_delete_group_snapshot_exception(self):
        vg_snapshots = self.cinder_group_snapshots.list()
        vg_snapshot = self.cinder_group_snapshots.first()
        tenants = self.tenants.list()
        self.mock_group_snapshot_list.return_value = vg_snapshots
        self.mock_group_snapshot_delete.side_effect = self.exceptions.cinder
        self.mock_group_list.return_value = self.cinder_groups.list()
        self.mock_tenant_list.return_value = [tenants, False]

        form_data = {'action': 'volume_vg_snapshots__delete_vg_snapshot__%s'
                     % vg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Unable to delete snapshot: %s" % vg_snapshot.name,
                      [m.message for m in res.context['messages']])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_group_snapshot_list, 2,
            mock.call(test.IsHttpRequest(), {'all_tenants': 1}))
        self.mock_group_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_group_list, 2,
            mock.call(test.IsHttpRequest(), {'all_tenants': 1}))

    @test.create_mocks({
        api.cinder: ['group_snapshot_get',
                     'group_get',
                     'volume_type_get',
                     'volume_list']})
    def test_detail_view(self):
        vg_snapshot = self.cinder_group_snapshots.first()
        group = self.cinder_groups.first()
        volume_type = self.cinder_volume_types.first()
        volumes = self.cinder_volumes.list()

        self.mock_group_snapshot_get.return_value = vg_snapshot
        self.mock_group_get.return_value = group
        self.mock_volume_type_get.return_value = volume_type
        self.mock_volume_list.return_value = volumes

        url = reverse(
            'horizon:admin:vg_snapshots:detail',
            args=[vg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)
        self.mock_group_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        search_opts = {'group_id': group.id}
        self.mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=search_opts)

    @test.create_mocks({api.cinder: ['group_snapshot_get']})
    def test_detail_view_with_exception(self):
        vg_snapshot = self.cinder_group_snapshots.first()

        self.mock_group_snapshot_get.side_effect = self.exceptions.cinder

        url = reverse(
            'horizon:admin:vg_snapshots:detail',
            args=[vg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
