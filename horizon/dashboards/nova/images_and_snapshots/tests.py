# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack LLC
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

from copy import deepcopy
from django import http
from django.core.urlresolvers import reverse
from glance.common import exception as glance_exception
from mox import IsA

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class ImagesAndSnapshotsTests(test.TestCase):
    def test_index(self):
        images = self.images.list()
        snapshots = self.snapshots.list()
        self.mox.StubOutWithMock(api, 'image_list_detailed')
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn(images)
        api.snapshot_list_detailed(IsA(http.HttpRequest)).AndReturn(snapshots)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'nova/images_and_snapshots/index.html')
        self.assertIn('images_table', res.context)
        images = res.context['images_table'].data
        filter_func = lambda im: im.container_format not in ['aki', 'ari']
        filtered_images = filter(filter_func, images)
        self.assertItemsEqual(images, filtered_images)

    def test_index_no_images(self):
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        self.mox.StubOutWithMock(api, 'image_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn([])
        api.snapshot_list_detailed(IsA(http.HttpRequest)) \
                                   .AndReturn(self.snapshots.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'nova/images_and_snapshots/index.html')

    def test_index_client_conn_error(self):
        self.mox.StubOutWithMock(api, 'image_list_detailed')
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        exc = glance_exception.ClientConnectionError('clientConnError')
        api.image_list_detailed(IsA(http.HttpRequest)).AndRaise(exc)
        api.snapshot_list_detailed(IsA(http.HttpRequest)) \
                                   .AndReturn(self.snapshots.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'nova/images_and_snapshots/index.html')

    def test_queued_snapshot_actions(self):
        images = self.images.list()
        snapshots = self.snapshots.list()
        snapshot1 = deepcopy(snapshots[0])
        snapshot1.status = 'active'
        snapshot2 = deepcopy(snapshots[0])
        snapshot2.id = 4
        snapshot2.name = "snap2"
        snapshot2.status = "queued"
        snapshot2.owner = '1'
        new_snapshots = [snapshot1, snapshot2]
        self.mox.StubOutWithMock(api, 'image_list_detailed')
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn(images)
        api.snapshot_list_detailed(IsA(http.HttpRequest)).\
                AndReturn(new_snapshots)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'nova/images_and_snapshots/index.html')
        self.assertIn('snapshots_table', res.context)
        snaps = res.context['snapshots_table']
        self.assertEqual(len(snaps.get_rows()), 2)

        row_actions = snaps.get_row_actions(snaps.data[0])

        #first instance - status active, not owned
        self.assertEqual(row_actions[0].verbose_name, u"Launch")
        self.assertEqual(len(row_actions), 1)

        row_actions = snaps.get_row_actions(snaps.data[1])
        #first instance - status queued, but editable
        self.assertEqual(row_actions[0].verbose_name, u"Edit")
        self.assertEqual(str(row_actions[1]), "<DeleteSnapshot: delete>")
        self.assertEqual(len(row_actions), 2)
