# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:images_and_snapshots:index')


class VolumeSnapshotsViewTests(test.TestCase):
    def test_create_snapshot_get(self):
        volume = self.volumes.first()
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/volumes/create_snapshot.html')

    @test.create_stubs({cinder: ('volume_snapshot_create',)})
    def test_create_snapshot_post(self):
        volume = self.volumes.first()
        snapshot = self.volume_snapshots.first()

        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.display_name,
                                      snapshot.display_description) \
                                      .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.display_name,
                    'description': snapshot.display_description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',
                                     'snapshot_list_detailed'),
                        api.cinder: ('volume_snapshot_list',
                                     'volume_snapshot_delete')})
    def test_delete_volume_snapshot(self):
        vol_snapshots = self.volume_snapshots.list()
        snapshot = self.volume_snapshots.first()

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn(([], False))
        api.glance.snapshot_list_detailed(IsA(http.HttpRequest),
                                          marker=None).AndReturn(([], False))
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)). \
            AndReturn(vol_snapshots)
        api.cinder.volume_snapshot_delete(IsA(http.HttpRequest), snapshot.id)
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn(([], False))
        api.glance.snapshot_list_detailed(IsA(http.HttpRequest),
                                          marker=None).AndReturn(([], False))
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)). \
            AndReturn([])
        self.mox.ReplayAll()

        formData = {'action':
                    'volume_snapshots__delete__%s' % snapshot.id}
        res = self.client.post(INDEX_URL, formData, follow=True)

        self.assertIn("Scheduled deletion of Volume Snapshot: test snapshot",
                      [m.message for m in res.context['messages']])
