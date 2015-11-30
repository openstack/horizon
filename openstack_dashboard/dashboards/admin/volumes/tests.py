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

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.dashboards.project.volumes.snapshots \
    import tables as snapshot_tables
from openstack_dashboard.dashboards.project.volumes.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:admin:volumes:index')


class VolumeTests(test.BaseAdminViewTests):

    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list_paged',
                                 'volume_snapshot_list'),
                        keystone: ('tenant_list',)})
    def test_index(self):
        cinder.volume_list_paged(IsA(http.HttpRequest), sort_dir="desc",
                                 marker=None, paginate=True,
                                 search_opts={'all_tenants': True})\
            .AndReturn([self.cinder_volumes.list(), False, False])
        cinder.volume_snapshot_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).AndReturn([])
        api.nova.server_list(IsA(http.HttpRequest), search_opts={
                             'all_tenants': True}) \
            .AndReturn([self.servers.list(), False])
        keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'admin/volumes/index.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list_paged',),
                        keystone: ('tenant_list',)})
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev):
        cinder.volume_list_paged(IsA(http.HttpRequest), sort_dir=sort_dir,
                                 marker=marker, paginate=True,
                                 search_opts={'all_tenants': True}) \
            .AndReturn([volumes, has_more, has_prev])
        api.nova.server_list(IsA(http.HttpRequest), search_opts={
                             'all_tenants': True}) \
            .AndReturn([self.servers.list(), False])
        keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()

        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/volumes/index.html')
        self.assertEqual(res.status_code, 200)

        self.mox.UnsetStubs()
        return res

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_volumes = self.cinder_volumes.list()

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
    def test_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_volumes = self.cinder_volumes.list()

        # prev from some page
        expected_volumes = mox_volumes[size:2 * size]
        marker = mox_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = "?".join([INDEX_URL, "=".join([prev, marker])])
        res = self._test_index_paginated(marker=marker, sort_dir="asc",
                                         volumes=expected_volumes, url=url,
                                         has_more=False, has_prev=True)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

        # back to first page
        expected_volumes = mox_volumes[:size]
        marker = mox_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = "?".join([INDEX_URL, "=".join([prev, marker])])
        res = self._test_index_paginated(marker=marker, sort_dir="asc",
                                         volumes=expected_volumes, url=url,
                                         has_more=True, has_prev=False)
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, expected_volumes)

    @test.create_stubs({cinder: ('volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'extension_supported',
                                 'volume_encryption_type_list')})
    def test_volume_types_tab(self):
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])
        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_qos_specs.list())
        cinder.volume_encryption_type_list(IsA(http.HttpRequest))\
            .AndReturn(encryption_list)
        cinder.extension_supported(IsA(http.HttpRequest),
                                   'VolumeTypeEncryption').MultipleTimes()\
            .AndReturn(True)

        self.mox.ReplayAll()
        res = self.client.get(reverse(
            'horizon:admin:volumes:volume_types_tab'))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(
            res, 'admin/volumes/volume_types/volume_types_tables.html')
        volume_types = res.context['volume_types_table'].data
        self.assertItemsEqual(volume_types, self.volume_types.list())
        qos_specs = res.context['qos_specs_table'].data
        self.assertItemsEqual(qos_specs, self.cinder_qos_specs.list())

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_snapshot_list_paged',),
                        keystone: ('tenant_list',)})
    def test_snapshots_tab(self):
        cinder.volume_snapshot_list_paged(
            IsA(http.HttpRequest), paginate=True, marker=None, sort_dir='desc',
            search_opts={'all_tenants': True},).AndReturn(
            [self.cinder_volume_snapshots.list(), False, False])
        cinder.volume_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).\
            AndReturn(self.cinder_volumes.list())
        keystone.tenant_list(IsA(http.HttpRequest)). \
            AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:admin:volumes:snapshots_tab'))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, self.cinder_volume_snapshots.list())

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_snapshot_list_paged',),
                        keystone: ('tenant_list',)})
    def _test_snapshots_index_paginated(self, marker, sort_dir, snapshots, url,
                                        has_more, has_prev):
        cinder.volume_snapshot_list_paged(
            IsA(http.HttpRequest), paginate=True, marker=marker,
            sort_dir=sort_dir, search_opts={'all_tenants': True}) \
            .AndReturn([snapshots, has_more, has_prev])
        cinder.volume_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).\
            AndReturn(self.cinder_volumes.list())
        keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()

        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/volumes/index.html')
        self.assertEqual(res.status_code, 200)

        self.mox.UnsetStubs()
        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_snapshots = self.cinder_volume_snapshots.list()
        base_url = reverse('horizon:admin:volumes:snapshots_tab')
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
        url = "&".join([base_url, "=".join([next, marker])])
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="desc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # get last page
        expected_snapshots = mox_snapshots[-size:]
        marker = expected_snapshots[0].id
        url = "&".join([base_url, "=".join([next, marker])])
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="desc", snapshots=expected_snapshots,
            url=url, has_more=False, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        max_snapshots = self.cinder_volume_snapshots.list()
        base_url = reverse('horizon:admin:volumes:snapshots_tab')
        prev = snapshot_tables.VolumeSnapshotsTable._meta.prev_pagination_param

        # prev from some page
        expected_snapshots = max_snapshots[size:2 * size]
        marker = max_snapshots[0].id
        url = "&".join([base_url, "=".join([prev, marker])])
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=False, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # back to first page
        expected_snapshots = max_snapshots[:size]
        marker = max_snapshots[0].id
        url = "&".join([base_url, "=".join([prev, marker])])
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=False)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)
