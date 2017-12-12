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
import mock

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.dashboards.project.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.snapshots import forms


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

    @mock.patch.object(keystone, 'tenant_list')
    @mock.patch.object(cinder, 'volume_snapshot_list')
    @mock.patch.object(cinder, 'volume_list_paged')
    @mock.patch.object(api.nova, 'server_list')
    def _test_index(self, instanceless_volumes, mock_server_list,
                    mock_volume_list, mock_snapshot_list, mock_tenant_list):
        volumes = self.cinder_volumes.list()
        if instanceless_volumes:
            for volume in volumes:
                volume.attachments = []

        mock_volume_list.return_value = [volumes, False, False]
        mock_snapshot_list.return_value = []

        if not instanceless_volumes:
            mock_server_list.return_value = [self.servers.list(), False]

        mock_tenant_list.return_value = [[self.tenants.list(), False]]

        res = self.client.get(INDEX_URL)
        if not instanceless_volumes:
            mock_server_list.assert_called_once_with(
                test.IsHttpRequest(), search_opts={'all_tenants': True})

        mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), sort_dir="desc", marker=None, paginate=True,
            search_opts={'all_tenants': True})
        mock_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': True})
        mock_tenant_list.assert_called_once()
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

    def test_index_without_attachments(self):
        self._test_index(True)

    def test_index_with_attachments(self):
        self._test_index(False)

    @mock.patch.object(keystone, 'tenant_list')
    @mock.patch.object(cinder, 'volume_snapshot_list')
    @mock.patch.object(cinder, 'volume_list_paged')
    @mock.patch.object(api.nova, 'server_list')
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev, mock_server_list,
                              mock_volume_list, mock_snapshot_list,
                              mock_tenant_list):
        vol_snaps = self.cinder_volume_snapshots.list()

        mock_volume_list.return_value = [volumes, has_more, has_prev]
        mock_snapshot_list.return_value = vol_snaps
        mock_server_list.return_value = [self.servers.list(), False]
        mock_tenant_list.return_value = [self.tenants.list(), False]

        res = self.client.get(urlunquote(url))

        mock_server_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': True})
        mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                 sort_dir=sort_dir,
                                                 marker=marker, paginate=True,
                                                 search_opts={
                                                     'all_tenants': True})
        mock_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'all_tenants': True})
        mock_tenant_list.assert_called_once()

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
        mox_volumes = self._ensure_attachments_exist(
            self.cinder_volumes.list())

        # get first page
        expected_volumes = mox_volumes[:size]
        url = INDEX_URL
        res = self._test_index_paginated(None, "desc", expected_volumes, url,
                                         True, False)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # get second page
        expected_volumes = mox_volumes[size:2 * size]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = INDEX_URL + "?%s=%s" % (next, marker)
        res = self._test_index_paginated(marker, "desc", expected_volumes, url,
                                         True, True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # get last page
        expected_volumes = mox_volumes[-size:]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = INDEX_URL + "?%s=%s" % (next, marker)
        res = self._test_index_paginated(marker, "desc", expected_volumes, url,
                                         False, True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_volumes = self._ensure_attachments_exist(
            self.cinder_volumes.list())

        # prev from some page
        expected_volumes = mox_volumes[size:2 * size]
        marker = mox_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = INDEX_URL + "?%s=%s" % (prev, marker)
        res = self._test_index_paginated(marker, "asc", expected_volumes, url,
                                         False, True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # back to first page
        expected_volumes = mox_volumes[:size]
        marker = mox_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = INDEX_URL + "?%s=%s" % (prev, marker)
        res = self._test_index_paginated(marker, "asc", expected_volumes, url,
                                         True, False)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

    @mock.patch.object(cinder, 'volume_get')
    @mock.patch.object(cinder, 'volume_reset_state')
    def test_update_volume_status(self, mock_reset, mock_volume_get):
        volume = self.volumes.first()
        formData = {'status': 'error'}

        mock_volume_get.return_value = volume

        res = self.client.post(
            reverse('horizon:admin:volumes:update_status',
                    args=(volume.id,)),
            formData)

        mock_reset.assert_called_once_with(test.IsHttpRequest(),
                                           volume.id, formData['status'])
        mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                volume.id)
        self.assertNoFormErrors(res)

    @mock.patch.object(cinder, 'extension_supported')
    @mock.patch.object(cinder, 'availability_zone_list')
    @mock.patch.object(cinder, 'volume_type_list')
    @mock.patch.object(cinder, 'volume_manage')
    def test_manage_volume(self, mock_manage, mock_type_list, mock_az_list,
                           mock_extension):
        metadata = {'key': u'k1',
                    'value': u'v1'}
        formData = {'host': 'host-1',
                    'identifier': 'vol-1',
                    'id_type': u'source-name',
                    'name': 'name-1',
                    'description': 'manage a volume',
                    'volume_type': 'vol_type_1',
                    'availability_zone': 'nova',
                    'metadata': metadata['key'] + '=' + metadata['value'],
                    'bootable': False}

        mock_type_list.return_value = self.cinder_volume_types.list()
        mock_az_list.return_value = self.availability_zones.list()
        mock_extension.return_value = True

        res = self.client.post(
            reverse('horizon:admin:volumes:manage'),
            formData)

        mock_manage.assert_called_once_with(
            test.IsHttpRequest(),
            host=formData['host'],
            identifier=formData['identifier'],
            id_type=formData['id_type'],
            name=formData['name'],
            description=formData['description'],
            volume_type=formData['volume_type'],
            availability_zone=formData['availability_zone'],
            metadata={metadata['key']: metadata['value']},
            bootable=formData['bootable'])
        mock_type_list.assert_called_once()
        mock_az_list.assert_called_once()
        mock_extension.assert_called_once_with(test.IsHttpRequest(),
                                               'AvailabilityZones')
        self.assertNoFormErrors(res)

    @mock.patch.object(cinder, 'volume_get')
    @mock.patch.object(cinder, 'volume_unmanage')
    def test_unmanage_volume(self, mock_unmanage, mock_get):
        # important - need to get the v2 cinder volume which has host data
        volume_list = [x for x in self.cinder_volumes.list()
                       if x.name == 'v2_volume']
        volume = volume_list[0]
        formData = {'volume_name': volume.name,
                    'host_name': 'host@backend-name#pool',
                    'volume_id': volume.id}

        mock_get.return_value = volume
        mock_unmanage.return_value = volume

        res = self.client.post(
            reverse('horizon:admin:volumes:unmanage',
                    args=(volume.id,)),
            formData)

        mock_unmanage.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        self.assertNoFormErrors(res)

    @mock.patch.object(cinder, 'volume_get')
    @mock.patch.object(cinder, 'pool_list')
    def test_volume_migrate_get(self, mock_pool, mock_get):
        volume = self.cinder_volumes.get(name='v2_volume')

        mock_pool.return_value = self.cinder_pools.list()
        mock_get.return_value = volume

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_pool.assert_called_once()
        self.assertTemplateUsed(res,
                                'admin/volumes/migrate_volume.html')

    @mock.patch.object(cinder, 'volume_get')
    def test_volume_migrate_get_volume_get_exception(self, mock_get):
        volume = self.cinder_volumes.get(name='v2_volume')
        mock_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @mock.patch.object(cinder, 'volume_get')
    @mock.patch.object(cinder, 'pool_list')
    def test_volume_migrate_list_pool_get_exception(self, mock_pool, mock_get):
        volume = self.cinder_volumes.get(name='v2_volume')

        mock_get.return_value = volume
        mock_pool.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_pool.assert_called_once()
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @mock.patch.object(cinder, 'volume_migrate')
    @mock.patch.object(cinder, 'volume_get')
    @mock.patch.object(cinder, 'pool_list')
    def test_volume_migrate_post(self, mock_pool, mock_get, mock_migtate):
        volume = self.cinder_volumes.get(name='v2_volume')
        host = self.cinder_pools.first().name

        mock_get.return_value = volume
        mock_pool.return_value = self.cinder_pools.list()
        mock_migtate.return_value = None

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.post(url, {'host': host, 'volume_id': volume.id})

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_pool.assert_called_once()
        mock_migtate.assert_called_once_with(test.IsHttpRequest(),
                                             volume.id, host, False)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @mock.patch.object(cinder, 'volume_migrate')
    @mock.patch.object(cinder, 'volume_get')
    @mock.patch.object(cinder, 'pool_list')
    def test_volume_migrate_post_api_exception(self, mock_pool, mock_get,
                                               mock_migtate):
        volume = self.cinder_volumes.get(name='v2_volume')
        host = self.cinder_pools.first().name

        mock_get.return_value = volume
        mock_pool.return_value = self.cinder_pools.list()
        mock_migtate.side_effect = self.exceptions.cinder

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.post(url, {'host': host, 'volume_id': volume.id})

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_pool.assert_called_once()
        mock_migtate.assert_called_once_with(test.IsHttpRequest(), volume.id,
                                             host, False)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_get_volume_status_choices_without_current(self):
        current_status = 'available'
        status_choices = forms.populate_status_choices(current_status,
                                                       forms.STATUS_CHOICES)
        self.assertEqual(len(status_choices), len(forms.STATUS_CHOICES))
        self.assertNotIn(current_status,
                         [status[0] for status in status_choices])

    @mock.patch.object(cinder, 'volume_get')
    def test_update_volume_status_get(self, mock_get):
        volume = self.cinder_volumes.get(name='v2_volume')
        mock_get.return_value = volume

        url = reverse('horizon:admin:volumes:update_status',
                      args=[volume.id])
        res = self.client.get(url)
        status_option = "<option value=\"%s\"></option>" % volume.status

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        self.assertNotContains(res, status_option)

    def test_detail_view_snapshot_tab(self):
        volume = self.cinder_volumes.first()
        server = self.servers.first()
        snapshots = self.cinder_volume_snapshots.list()
        this_volume_snapshots = [snapshot for snapshot in snapshots
                                 if snapshot.volume_id == volume.id]
        volume.attachments = [{"server_id": server.id}]
        volume_limits = self.cinder_limits['absolute']
        with mock.patch.object(api.nova, 'server_get',
                               return_value=server) as mock_server_get, \
                mock.patch.object(
                    cinder, 'tenant_absolute_limits',
                    return_value=volume_limits) as mock_limits, \
                mock.patch.object(
                    cinder, 'volume_get',
                    return_value=volume) as mock_volume_get, \
                mock.patch.object(
                    cinder, 'volume_snapshot_list',
                    return_value=this_volume_snapshots) \
                as mock_snapshot_list, \
                mock.patch.object(
                    cinder, 'message_list',
                    return_value=[]) as mock_message_list:

            url = (reverse(DETAIL_URL, args=[volume.id]) + '?' +
                   '='.join(['tab', 'volume_details__snapshots_tab']))
            res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['volume'].id, volume.id)
        self.assertEqual(len(res.context['table'].data),
                         len(this_volume_snapshots))
        self.assertNoMessages()

        mock_server_get.assert_called_once_with(test.IsHttpRequest(),
                                                server.id)
        mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                volume.id)
        mock_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(),
            search_opts={'volume_id': volume.id, 'all_tenants': True})
        mock_limits.assert_called_once()
        mock_message_list.assert_called_once_with(
            test.IsHttpRequest(),
            {
                'resource_uuid': volume.id,
                'resource_type': 'volume'
            })
