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
from novaclient.v1_1 import volume_snapshots
from mox import IsA

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class SnapshotsViewTests(test.BaseViewTests):
    def test_create_snapshot_get(self):
        VOLUME_ID = u'1'

        res = self.client.get(reverse('horizon:nova:instances_and_volumes:'
                                      'volumes:create_snapshot',
                                      args=[VOLUME_ID]))

        self.assertTemplateUsed(res, 'nova/instances_and_volumes/'
                                     'volumes/create_snapshot.html')

    def test_create_snapshot_post(self):
        VOLUME_ID = u'1'
        SNAPSHOT_NAME = u'vol snap'
        SNAPSHOT_DESCRIPTION = u'vol snap desc'

        volume_snapshot = volume_snapshots.Snapshot(
                volume_snapshots.SnapshotManager,
                {'id': 1,
                 'displayName': 'test snapshot',
                 'displayDescription': 'test snapshot description',
                 'size': 40,
                 'status': 'available',
                 'volumeId': 1})

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.TEST_TENANT,
                    'volume_id': VOLUME_ID,
                    'name': SNAPSHOT_NAME,
                    'description': SNAPSHOT_DESCRIPTION}

        self.mox.StubOutWithMock(api, 'volume_snapshot_create')

        api.volume_snapshot_create(
                IsA(http.HttpRequest), str(VOLUME_ID), SNAPSHOT_NAME,
                SNAPSHOT_DESCRIPTION).AndReturn(volume_snapshot)

        self.mox.ReplayAll()

        res = self.client.post(
                reverse('horizon:nova:instances_and_volumes:volumes:'
                        'create_snapshot',
                        args=[VOLUME_ID]),
                        formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
