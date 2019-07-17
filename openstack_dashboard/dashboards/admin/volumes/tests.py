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
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import urlunquote

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test


DETAIL_URL = ('horizon:admin:volumes:detail')
INDEX_URL = reverse('horizon:admin:volumes:index')


class VolumeTests(test.BaseAdminViewTests):
    def tearDown(self):
        for volume in self.cinder_volumes.list():
            # VolumeTableMixIn._set_volume_attributes mutates data
            # and cinder_volumes.list() doesn't deep copy
            for att in volume.attachments:
                if 'instance' in att:
                    del att['instance']
        super(VolumeTests, self).tearDown()

    @test.create_mocks({
        api.nova: ['server_list'],
        api.cinder: ['volume_snapshot_list', 'volume_list_paged'],
        api.keystone: ['tenant_list']})
    def _test_index(self, instanceless_volumes):
        volumes = self.cinder_volumes.list()
        if instanceless_volumes:
            for volume in volumes:
                volume.attachments = []

        self.mock_volume_list_paged.return_value = [volumes, False, False]
        self.mock_volume_snapshot_list.return_value = []

        if not instanceless_volumes:
            self.mock_server_list.return_value = [self.servers.list(), False]

        self.mock_tenant_list.return_value = [[self.tenants.list(), False]]

        res = self.client.get(INDEX_URL)
        if not instanceless_volumes:
            self.mock_server_list.assert_called_once_with(
                test.IsHttpRequest(), search_opts={'all_tenants': True})

        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), sort_dir="desc", marker=None, paginate=True,
            search_opts={'all_tenants': True})
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': True})
        self.mock_tenant_list.assert_called_once()
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

    def test_index_without_attachments(self):
        self._test_index(True)

    def test_index_with_attachments(self):
        self._test_index(False)

    @test.create_mocks({
        api.nova: ['server_list'],
        api.cinder: ['volume_snapshot_list', 'volume_list_paged'],
        api.keystone: ['tenant_list']})
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev):
        vol_snaps = self.cinder_volume_snapshots.list()

        self.mock_volume_list_paged.return_value = \
            [volumes, has_more, has_prev]
        self.mock_volume_snapshot_list.return_value = vol_snaps
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        res = self.client.get(urlunquote(url))

        self.mock_server_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': True})
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir=sort_dir,
            marker=marker, paginate=True,
            search_opts={
                'all_tenants': True})
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': True})
        self.mock_tenant_list.assert_called_once()

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertEqual(res.status_code, 200)

        return res

    @override_settings(FILTER_DATA_FIRST={'admin.volumes': True})
    def test_volumes_tab_with_admin_filter_first(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, [])

    def _ensure_attachments_exist(self, volumes):
        volumes = copy.copy(volumes)
        for volume in volumes:
            if not volume.attachments:
                volume.attachments.append({
                    "id": "1", "server_id": '1', "device": "/dev/hda"})
        return volumes

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated(self):
        size = settings.API_RESULT_PAGE_SIZE
        volumes = self._ensure_attachments_exist(
            self.cinder_volumes.list())

        # get first page
        expected_volumes = volumes[:size]
        url = INDEX_URL
        res = self._test_index_paginated(None, "desc", expected_volumes, url,
                                         True, False)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

        # get second page
        expected_volumes = volumes[size:2 * size]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = INDEX_URL + "?%s=%s" % (next, marker)
        res = self._test_index_paginated(marker, "desc", expected_volumes, url,
                                         True, True)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

        # get last page
        expected_volumes = volumes[-size:]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = INDEX_URL + "?%s=%s" % (next, marker)
        res = self._test_index_paginated(marker, "desc", expected_volumes, url,
                                         False, True)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        volumes = self._ensure_attachments_exist(
            self.cinder_volumes.list())

        # prev from some page
        expected_volumes = volumes[size:2 * size]
        marker = volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = INDEX_URL + "?%s=%s" % (prev, marker)
        res = self._test_index_paginated(marker, "asc", expected_volumes, url,
                                         False, True)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

        # back to first page
        expected_volumes = volumes[:size]
        marker = volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = INDEX_URL + "?%s=%s" % (prev, marker)
        res = self._test_index_paginated(marker, "asc", expected_volumes, url,
                                         True, False)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

    @test.create_mocks({api.cinder: ['volume_get', 'volume_reset_state']})
    def test_update_volume_status(self):
        volume = self.cinder_volumes.first()
        form_data = {'status': 'error'}

        self.mock_volume_reset_state.return_value = None
        self.mock_volume_get.return_value = volume

        res = self.client.post(
            reverse('horizon:admin:volumes:update_status',
                    args=(volume.id,)),
            form_data)

        self.mock_volume_reset_state.assert_called_once_with(
            test.IsHttpRequest(), volume.id, form_data['status'])
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.assertNoFormErrors(res)

    @test.create_mocks({
        api.cinder: ['extension_supported', 'availability_zone_list',
                     'volume_type_list', 'volume_manage']})
    def test_manage_volume(self):
        metadata = {'key': u'k1',
                    'value': u'v1'}
        form_data = {'host': 'host-1',
                     'identifier': 'vol-1',
                     'id_type': u'source-name',
                     'name': 'name-1',
                     'description': 'manage a volume',
                     'volume_type': 'vol_type_1',
                     'availability_zone': 'nova',
                     'metadata': metadata['key'] + '=' + metadata['value'],
                     'bootable': False}

        self.mock_extension_supported.return_value = None
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_availability_zone_list.return_value = \
            self.availability_zones.list()
        self.mock_extension_supported.return_value = True

        res = self.client.post(
            reverse('horizon:admin:volumes:manage'),
            form_data)

        self.mock_volume_manage.assert_called_once_with(
            test.IsHttpRequest(),
            host=form_data['host'],
            identifier=form_data['identifier'],
            id_type=form_data['id_type'],
            name=form_data['name'],
            description=form_data['description'],
            volume_type=form_data['volume_type'],
            availability_zone=form_data['availability_zone'],
            metadata={metadata['key']: metadata['value']},
            bootable=form_data['bootable'])
        self.mock_volume_type_list.assert_called_once()
        self.mock_availability_zone_list.assert_called_once()
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(),
            'AvailabilityZones')
        self.assertNoFormErrors(res)

    @test.create_mocks({api.cinder: ['volume_get', 'volume_unmanage']})
    def test_unmanage_volume(self):
        # important - need to get the v2 cinder volume which has host data
        volume_list = [x for x in self.cinder_volumes.list()
                       if x.name == 'v2_volume']
        volume = volume_list[0]
        form_data = {'volume_name': volume.name,
                     'host_name': 'host@backend-name#pool',
                     'volume_id': volume.id}

        self.mock_volume_get.return_value = volume
        self.mock_volume_unmanage.return_value = volume

        res = self.client.post(
            reverse('horizon:admin:volumes:unmanage',
                    args=(volume.id,)),
            form_data)

        self.mock_volume_unmanage.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.assertNoFormErrors(res)

    @test.create_mocks({api.cinder: ['volume_get', 'pool_list']})
    def test_volume_migrate_get(self):
        volume = self.cinder_volumes.get(name='v2_volume')

        self.mock_pool_list.return_value = self.cinder_pools.list()
        self.mock_volume_get.return_value = volume

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.mock_pool_list.assert_called_once()
        self.assertTemplateUsed(res,
                                'admin/volumes/migrate_volume.html')

    @test.create_mocks({api.cinder: ['volume_get']})
    def test_volume_migrate_get_volume_get_exception(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        self.mock_volume_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_mocks({api.cinder: ['volume_get', 'pool_list']})
    def test_volume_migrate_list_pool_get_exception(self):
        volume = self.cinder_volumes.get(name='v2_volume')

        self.mock_volume_get.return_value = volume
        self.mock_pool_list.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.mock_pool_list.assert_called_once()
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_mocks({
        api.cinder: ['volume_migrate', 'volume_get', 'pool_list']})
    def test_volume_migrate_post(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        host = self.cinder_pools.first().name

        self.mock_volume_get.return_value = volume
        self.mock_pool_list.return_value = self.cinder_pools.list()
        self.mock_volume_migrate.return_value = None

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.post(url, {'host': host, 'volume_id': volume.id})

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.mock_pool_list.assert_called_once()
        self.mock_volume_migrate.assert_called_once_with(
            test.IsHttpRequest(), volume.id, host, False)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_mocks({
        api.cinder: ['volume_migrate', 'volume_get', 'pool_list']})
    def test_volume_migrate_post_api_exception(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        host = self.cinder_pools.first().name

        self.mock_volume_get.return_value = volume
        self.mock_pool_list.return_value = self.cinder_pools.list()
        self.mock_volume_migrate.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.post(url, {'host': host, 'volume_id': volume.id})

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.mock_pool_list.assert_called_once()
        self.mock_volume_migrate.assert_called_once_with(
            test.IsHttpRequest(), volume.id, host, False)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_mocks({api.cinder: ['volume_get']})
    def test_update_volume_status_get(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        self.mock_volume_get.return_value = volume

        url = reverse('horizon:admin:volumes:update_status',
                      args=[volume.id])
        res = self.client.get(url)
        status_option = "<option value=\"%s\"></option>" % volume.status

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.assertNotContains(res, status_option)

    @test.create_mocks({
        api.nova: ['server_get'],
        api.cinder: ['tenant_absolute_limits', 'volume_get',
                     'volume_snapshot_list', 'message_list']})
    def test_detail_view_snapshot_tab(self):
        volume = self.cinder_volumes.first()
        server = self.servers.first()
        snapshots = self.cinder_volume_snapshots.list()
        this_volume_snapshots = [snapshot for snapshot in snapshots
                                 if snapshot.volume_id == volume.id]
        volume.attachments = [{"server_id": server.id}]
        volume_limits = self.cinder_limits['absolute']

        self.mock_server_get.return_value = server
        self.mock_tenant_absolute_limits.return_value = volume_limits
        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_list.return_value = this_volume_snapshots
        self.mock_message_list.return_value = []

        url = (reverse(DETAIL_URL, args=[volume.id]) + '?' +
               '='.join(['tab', 'volume_details__snapshots_tab']))
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['volume'].id, volume.id)
        self.assertEqual(len(res.context['table'].data),
                         len(this_volume_snapshots))
        self.assertNoMessages()

        self.mock_server_get.assert_called_once_with(test.IsHttpRequest(),
                                                     server.id)
        self.mock_tenant_absolute_limits.assert_called_once()
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(),
            search_opts={'volume_id': volume.id, 'all_tenants': True})
        self.mock_message_list.assert_called_once_with(
            test.IsHttpRequest(),
            {
                'resource_uuid': volume.id,
                'resource_type': 'volume'
            })
