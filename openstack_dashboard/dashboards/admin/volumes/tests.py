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
from mox3.mox import IsA

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.dashboards.project.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.snapshots import forms


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

    @test.create_stubs({api.nova: ('server_list', 'server_get'),
                        cinder: ('volume_list_paged',
                                 'volume_snapshot_list'),
                        keystone: ('tenant_list',)})
    def _test_index(self, instanceless_volumes=False):
        volumes = self.cinder_volumes.list()
        if instanceless_volumes:
            for volume in volumes:
                volume.attachments = []
        else:
            server = self.servers.first()

        cinder.volume_list_paged(IsA(http.HttpRequest), sort_dir="desc",
                                 marker=None, paginate=True,
                                 search_opts={'all_tenants': True})\
            .AndReturn([volumes, False, False])
        cinder.volume_snapshot_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).AndReturn([])
        if not instanceless_volumes:
            api.nova.server_get(IsA(http.HttpRequest),
                                server.id).AndReturn(server)
            api.nova.server_list(IsA(http.HttpRequest), search_opts={
                                 'all_tenants': True}, detailed=False) \
                .AndReturn([self.servers.list(), False])
        keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

    def test_index_without_attachments(self):
        self._test_index(instanceless_volumes=True)

    def test_index_with_attachments(self):
        self._test_index(instanceless_volumes=False)

    @test.create_stubs({api.nova: ('server_list', 'server_get'),
                        cinder: ('volume_list_paged',
                                 'volume_snapshot_list'),
                        keystone: ('tenant_list',)})
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev):
        vol_snaps = self.cinder_volume_snapshots.list()
        server = self.servers.first()
        cinder.volume_list_paged(IsA(http.HttpRequest), sort_dir=sort_dir,
                                 marker=marker, paginate=True,
                                 search_opts={'all_tenants': True}) \
            .AndReturn([volumes, has_more, has_prev])
        api.cinder.volume_snapshot_list(
            IsA(http.HttpRequest), search_opts=None).AndReturn(vol_snaps)
        api.nova.server_list(IsA(http.HttpRequest), search_opts={
                             'all_tenants': True}, detailed=False) \
            .AndReturn([self.servers.list(), False])
        api.nova.server_get(IsA(http.HttpRequest),
                            server.id).AndReturn(server)
        keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()

        res = self.client.get(urlunquote(url))

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertEqual(res.status_code, 200)

        self.mox.UnsetStubs()
        return res

    @override_settings(FILTER_DATA_FIRST={'admin.volumes': True})
    def test_volumes_tab_with_admin_filter_first(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, [])

    def ensure_attachments_exist(self, volumes):
        volumes = copy.copy(volumes)
        for volume in volumes:
            if not volume.attachments:
                volume.attachments.append({
                    "id": "1", "server_id": '1', "device": "/dev/hda"})
        return volumes

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_volumes = self.ensure_attachments_exist(self.cinder_volumes.list())

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
        url = INDEX_URL + "?%s=%s" % (next, marker)
        res = self._test_index_paginated(marker=marker, sort_dir="desc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # get last page
        expected_volumes = mox_volumes[-size:]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = INDEX_URL + "?%s=%s" % (next, marker)
        res = self._test_index_paginated(marker=marker, sort_dir="desc",
                                         volumes=expected_volumes, url=url,
                                         has_more=False, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_volumes = self.ensure_attachments_exist(self.cinder_volumes.list())

        # prev from some page
        expected_volumes = mox_volumes[size:2 * size]
        marker = mox_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = INDEX_URL + "?%s=%s" % (prev, marker)
        res = self._test_index_paginated(marker=marker, sort_dir="asc",
                                         volumes=expected_volumes, url=url,
                                         has_more=False, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # back to first page
        expected_volumes = mox_volumes[:size]
        marker = mox_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = INDEX_URL + "?%s=%s" % (prev, marker)
        res = self._test_index_paginated(marker=marker, sort_dir="asc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=False)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

    @test.create_stubs({cinder: ('volume_reset_state',
                                 'volume_get')})
    def test_update_volume_status(self):
        volume = self.volumes.first()
        formData = {'status': 'error'}

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        cinder.volume_reset_state(IsA(http.HttpRequest),
                                  volume.id,
                                  formData['status'])
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:update_status',
                    args=(volume.id,)),
            formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_manage',
                                 'volume_type_list',
                                 'availability_zone_list',
                                 'extension_supported')})
    def test_manage_volume(self):
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
        cinder.volume_type_list(
            IsA(http.HttpRequest)). \
            AndReturn(self.cinder_volume_types.list())
        cinder.availability_zone_list(
            IsA(http.HttpRequest)). \
            AndReturn(self.availability_zones.list())
        cinder.extension_supported(
            IsA(http.HttpRequest),
            'AvailabilityZones'). \
            AndReturn(True)
        cinder.volume_manage(
            IsA(http.HttpRequest),
            host=formData['host'],
            identifier=formData['identifier'],
            id_type=formData['id_type'],
            name=formData['name'],
            description=formData['description'],
            volume_type=formData['volume_type'],
            availability_zone=formData['availability_zone'],
            metadata={metadata['key']: metadata['value']},
            bootable=formData['bootable'])
        self.mox.ReplayAll()
        res = self.client.post(
            reverse('horizon:admin:volumes:manage'),
            formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_unmanage',
                                 'volume_get')})
    def test_unmanage_volume(self):
        # important - need to get the v2 cinder volume which has host data
        volume_list = [x for x in self.cinder_volumes.list()
                       if x.name == 'v2_volume']
        volume = volume_list[0]
        formData = {'volume_name': volume.name,
                    'host_name': 'host@backend-name#pool',
                    'volume_id': volume.id}

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        cinder.volume_unmanage(IsA(http.HttpRequest), volume.id). \
            AndReturn(volume)
        self.mox.ReplayAll()
        res = self.client.post(
            reverse('horizon:admin:volumes:unmanage',
                    args=(volume.id,)),
            formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('pool_list',
                                 'volume_get',)})
    def test_volume_migrate_get(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.pool_list(IsA(http.HttpRequest)) \
            .AndReturn(self.cinder_pools.list())

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                                'admin/volumes/migrate_volume.html')

    @test.create_stubs({cinder: ('volume_get',)})
    def test_volume_migrate_get_volume_get_exception(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('pool_list',
                                 'volume_get',)})
    def test_volume_migrate_list_pool_get_exception(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.pool_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()
        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('pool_list',
                                 'volume_get',
                                 'volume_migrate',)})
    def test_volume_migrate_post(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        host = self.cinder_pools.first().name

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.pool_list(IsA(http.HttpRequest)) \
            .AndReturn(self.cinder_pools.list())
        cinder.volume_migrate(IsA(http.HttpRequest),
                              volume.id,
                              host,
                              False) \
            .AndReturn(None)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.post(url, {'host': host, 'volume_id': volume.id})
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('pool_list',
                                 'volume_get',
                                 'volume_migrate',)})
    def test_volume_migrate_post_api_exception(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        host = self.cinder_pools.first().name

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.pool_list(IsA(http.HttpRequest)) \
            .AndReturn(self.cinder_pools.list())
        cinder.volume_migrate(IsA(http.HttpRequest),
                              volume.id,
                              host,
                              False) \
            .AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:migrate',
                      args=[volume.id])
        res = self.client.post(url, {'host': host, 'volume_id': volume.id})
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_get_volume_status_choices_without_current(self):
        current_status = 'available'
        status_choices = forms.populate_status_choices(current_status,
                                                       forms.STATUS_CHOICES)
        self.assertEqual(len(status_choices), len(forms.STATUS_CHOICES))
        self.assertNotIn(current_status,
                         [status[0] for status in status_choices])

    @test.create_stubs({cinder: ('volume_get',)})
    def test_update_volume_status_get(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:update_status',
                      args=[volume.id])
        res = self.client.get(url)
        status_option = "<option value=\"%s\"></option>" % volume.status
        self.assertNotContains(res, status_option)
