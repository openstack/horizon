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

from django.core.urlresolvers import reverse
from django import http
from mox import IsA  # noqa

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:admin:volumes:index')


class VolumeSnapshotsViewTests(test.BaseAdminViewTests):
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
        url = reverse('horizon:admin:volumes:snapshots:update_status',
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

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertContains(res,
                            "<h1>Volume Snapshot Details: %s</h1>" %
                            snapshot.name,
                            1, 200)
        self.assertContains(res, "<dd>test snapshot</dd>", 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % snapshot.id, 1, 200)
        self.assertContains(res, "<dd>Available</dd>", 1, 200)

    @test.create_stubs({cinder: ('volume_snapshot_get',
                                 'volume_get')})
    def test_get_volume_snapshot_details_with_snapshot_exception(self):
        # Test to verify redirect if get volume snapshot fails
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id).\
            AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

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

        url = reverse('horizon:admin:volumes:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)
