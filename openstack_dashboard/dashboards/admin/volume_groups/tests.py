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


INDEX_URL = reverse('horizon:admin:volume_groups:index')
INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class AdminVolumeGroupTests(test.BaseAdminViewTests):
    @test.create_mocks({
        api.keystone: ['tenant_list'],
        api.cinder: ['group_list_with_vol_type_names',
                     'group_snapshot_list']})
    def test_index(self):
        group = self.cinder_groups.list()
        vg_snapshot = self.cinder_group_snapshots.list()
        tenants = self.tenants.list()
        self.mock_group_list_with_vol_type_names.return_value = group
        self.mock_group_snapshot_list.return_value = vg_snapshot
        self.mock_tenant_list.return_value = [tenants, False]

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertIn('volume_groups_table', res.context)
        volume_groups_table = res.context['volume_groups_table']
        volume_groups = volume_groups_table.data
        self.assertEqual(len(volume_groups), 1)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_group_list_with_vol_type_names.assert_called_once_with(
            test.IsHttpRequest(), {'all_tenants': 1})
        self.mock_group_snapshot_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.cinder: ['group_get', 'group_delete']})
    def test_delete_group(self):
        group = self.cinder_groups.first()

        self.mock_group_get.return_value = group
        self.mock_group_delete.return_value = None

        url = reverse('horizon:admin:volume_groups:delete',
                      args=[group.id])
        res = self.client.post(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id,
                                                       delete_volumes=False)

    @test.create_mocks({api.cinder: ['group_get', 'group_delete']})
    def test_delete_group_delete_volumes_flag(self):
        group = self.cinder_groups.first()
        formData = {'delete_volumes': True}

        self.mock_group_get.return_value = group
        self.mock_group_delete.return_value = None

        url = reverse('horizon:admin:volume_groups:delete',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id,
                                                       delete_volumes=True)

    @test.create_mocks({api.cinder: ['group_get', 'group_delete']})
    def test_delete_group_exception(self):
        group = self.cinder_groups.first()
        formData = {'delete_volumes': False}

        self.mock_group_get.return_value = group
        self.mock_group_delete.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volume_groups:delete',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id,
                                                       delete_volumes=False)

    def test_update_group_add_vol(self):
        self._test_update_group_add_remove_vol(add=True)

    def test_update_group_remove_vol(self):
        self._test_update_group_add_remove_vol(add=False)

    @test.create_mocks({api.cinder: ['volume_list',
                                     'volume_type_list',
                                     'group_get',
                                     'group_update']})
    def _test_update_group_add_remove_vol(self, add=True):
        group = self.cinder_groups.first()
        volume_types = self.cinder_volume_types.list()
        volumes = (self.cinder_volumes.list() +
                   self.cinder_group_volumes.list())

        group_voltype_names = [t.name for t in volume_types
                               if t.id in group.volume_types]
        compat_volumes = [v for v in volumes
                          if v.volume_type in group_voltype_names]
        compat_volume_ids = [v.id for v in compat_volumes]
        assigned_volume_ids = [v.id for v in compat_volumes
                               if getattr(v, 'group_id', None)]
        add_volume_ids = [v.id for v in compat_volumes
                          if v.id not in assigned_volume_ids]

        new_volums = compat_volume_ids if add else []
        formData = {
            'default_add_volumes_to_group_role': 'member',
            'add_volumes_to_group_role_member': new_volums,
        }

        self.mock_volume_list.return_value = volumes
        self.mock_volume_type_list.return_value = volume_types
        self.mock_group_get.return_value = group
        self.mock_group_update.return_value = group

        url = reverse('horizon:admin:volume_groups:manage',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_volume_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        if add:
            self.mock_group_update.assert_called_once_with(
                test.IsHttpRequest(), group.id,
                add_volumes=add_volume_ids,
                remove_volumes=[])
        else:
            self.mock_group_update.assert_called_once_with(
                test.IsHttpRequest(), group.id,
                add_volumes=[],
                remove_volumes=assigned_volume_ids)

    @test.create_mocks({api.cinder: ['group_get_with_vol_type_names',
                                     'volume_list',
                                     'group_snapshot_list']})
    def test_detail_view(self):
        group = self.cinder_groups.first()
        volumes = self.cinder_volumes.list()
        vg_snapshot = self.cinder_group_snapshots.list()

        self.mock_group_get_with_vol_type_names.return_value = group
        self.mock_volume_list.return_value = volumes
        self.mock_group_snapshot_list.return_value = vg_snapshot

        url = reverse('horizon:admin:volume_groups:detail',
                      args=[group.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(group.has_snapshots)

        self.mock_group_get_with_vol_type_names.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        search_opts = {'group_id': group.id}
        self.mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=search_opts)
        self.mock_group_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=search_opts)

    @test.create_mocks({api.cinder: ['group_get']})
    def test_detail_view_with_exception(self):
        group = self.cinder_groups.first()

        self.mock_group_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volume_groups:detail',
                      args=[group.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
