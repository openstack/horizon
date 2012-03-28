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

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class VolumeSnapshotsViewTests(test.TestCase):
    def test_create_snapshot_get(self):
        volume = self.volumes.first()
        res = self.client.get(reverse('horizon:nova:instances_and_volumes:'
                                      'volumes:create_snapshot',
                                      args=[volume.id]))

        self.assertTemplateUsed(res, 'nova/instances_and_volumes/'
                                     'volumes/create_snapshot.html')

    def test_create_snapshot_post(self):
        volume = self.volumes.first()
        snapshot = self.volume_snapshots.first()

        self.mox.StubOutWithMock(api, 'volume_snapshot_create')
        api.volume_snapshot_create(IsA(http.HttpRequest),
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
        url = reverse('horizon:nova:instances_and_volumes:volumes:'
                      'create_snapshot', args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)
