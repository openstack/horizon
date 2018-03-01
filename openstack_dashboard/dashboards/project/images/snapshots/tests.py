# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from django.urls import reverse

import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:images:index')


class SnapshotsViewTests(test.TestCase):
    def test_create_snapshot_get(self):
        server = self.servers.first()

        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'project/images/snapshots/create.html')

    @mock.patch.object(api.nova, 'snapshot_create')
    @mock.patch.object(api.nova, 'server_get')
    def test_create_snapshot_post(self, mock_server_get, mock_snapshot_create):
        server = self.servers.first()
        snapshot = self.snapshots.first()

        mock_server_get.return_value = server
        mock_snapshot_create.return_value = snapshot

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.tenant.id,
                    'instance_id': server.id,
                    'name': snapshot.name}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        mock_server_get.assert_called_once_with(test.IsHttpRequest(),
                                                server.id)
        mock_snapshot_create.assert_called_once_with(test.IsHttpRequest(),
                                                     server.id, snapshot.name)

    @mock.patch.object(api.nova, 'snapshot_create')
    def test_create_snapshot_post_exception(self,
                                            mock_snapshot_create):
        server = self.servers.first()
        snapshot = self.snapshots.first()

        mock_snapshot_create.side_effect = self.exceptions.nova

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.tenant.id,
                    'instance_id': server.id,
                    'name': snapshot.name}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        res = self.client.post(url, formData)
        redirect = reverse("horizon:project:instances:index")

        self.assertRedirectsNoFollow(res, redirect)
        mock_snapshot_create.assert_called_once_with(test.IsHttpRequest(),
                                                     server.id, snapshot.name)
