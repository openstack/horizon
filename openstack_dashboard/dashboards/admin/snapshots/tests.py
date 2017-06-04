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
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings
from django.utils.http import urlunquote
from mox3.mox import IsA

from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.snapshots import forms
from openstack_dashboard.dashboards.admin.snapshots import tables

INDEX_URL = 'horizon:admin:snapshots:index'


class VolumeSnapshotsViewTests(test.BaseAdminViewTests):
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
        url = reverse(INDEX_URL)
        res = self.client.get(urlunquote(url))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
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

        res = self.client.get(urlunquote(url))

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertEqual(res.status_code, 200)

        self.mox.UnsetStubs()
        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_snapshots_index_paginated(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_snapshots = self.cinder_volume_snapshots.list()
        base_url = reverse(INDEX_URL)
        next = tables.VolumeSnapshotsTable._meta.pagination_param

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
    def test_snapshots_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        max_snapshots = self.cinder_volume_snapshots.list()
        base_url = reverse('horizon:admin:snapshots:index')
        prev = tables.VolumeSnapshotsTable._meta.prev_pagination_param

        # prev from some page
        expected_snapshots = max_snapshots[size:2 * size]
        marker = max_snapshots[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=False, has_prev=True)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

        # back to first page
        expected_snapshots = max_snapshots[:size]
        marker = max_snapshots[0].id
        url = base_url + "?%s=%s" % (prev, marker)
        res = self._test_snapshots_index_paginated(
            marker=marker, sort_dir="asc", snapshots=expected_snapshots,
            url=url, has_more=True, has_prev=False)
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, expected_snapshots)

    @test.create_stubs({cinder: ('volume_snapshot_reset_state',
                                 'volume_snapshot_get')})
    def test_update_snapshot_status(self):
        snapshot = self.cinder_volume_snapshots.first()
        state = 'error'

        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id) \
            .AndReturn(snapshot)
        cinder.volume_snapshot_reset_state(IsA(http.HttpRequest),
                                           snapshot.id,
                                           state)
        self.mox.ReplayAll()

        formData = {'status': state}
        url = reverse('horizon:admin:snapshots:update_status',
                      args=(snapshot.id,))
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_snapshot_get',
                                 'volume_get')})
    def test_get_volume_snapshot_details(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndReturn(volume)
        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)
        cinder.volume_get(IsA(http.HttpRequest), snapshot.volume_id). \
            AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['snapshot'].id, snapshot.id)

    @test.create_stubs({cinder: ('volume_snapshot_get',
                                 'volume_get')})
    def test_get_volume_snapshot_details_with_snapshot_exception(self):
        # Test to verify redirect if get volume snapshot fails
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id).\
            AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, reverse(INDEX_URL))

    @test.create_stubs({cinder: ('volume_snapshot_get',
                                 'volume_get')})
    def test_get_volume_snapshot_details_with_volume_exception(self):
        # Test to verify redirect if get volume fails
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndRaise(self.exceptions.cinder)
        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, reverse(INDEX_URL))

    def test_get_snapshot_status_choices_without_current(self):
        current_status = 'available'
        status_choices = forms.populate_status_choices(current_status,
                                                       forms.STATUS_CHOICES)
        self.assertEqual(len(status_choices), len(forms.STATUS_CHOICES))
        self.assertNotIn(current_status,
                         [status[0] for status in status_choices])

    @test.create_stubs({cinder: ('volume_snapshot_get',)})
    def test_update_volume_status_get(self):
        snapshot = self.cinder_volume_snapshots.first()
        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:snapshots:update_status',
                      args=[snapshot.id])
        res = self.client.get(url)
        status_option = "<option value=\"%s\"></option>" % snapshot.status
        self.assertNotContains(res, status_option)
