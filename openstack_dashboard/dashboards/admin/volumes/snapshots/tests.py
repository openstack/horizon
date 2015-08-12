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
from mox3.mox import IsA  # noqa

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.volumes.snapshots import forms

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

    def test_get_snapshot_status_choices_without_current(self):
        current_status = {'status': 'available'}
        status_choices = forms.populate_status_choices(current_status,
                                                       forms.STATUS_CHOICES)
        self.assertEqual(len(status_choices), len(forms.STATUS_CHOICES))
        self.assertNotIn(current_status['status'],
                         [status[0] for status in status_choices])

    @test.create_stubs({cinder: ('volume_snapshot_get',)})
    def test_update_volume_status_get(self):
        snapshot = self.cinder_volume_snapshots.first()
        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:snapshots:update_status',
                      args=[snapshot.id])
        res = self.client.get(url)
        status_option = "<option value=\"%s\"></option>" % snapshot.status
        self.assertNotContains(res, status_option)
