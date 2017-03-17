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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:images:index')


class SnapshotsViewTests(test.TestCase):
    def test_create_snapshot_get(self):
        server = self.servers.first()

        self.mox.ReplayAll()

        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'project/images/snapshots/create.html')

    def test_create_snapshot_post(self):
        server = self.servers.first()
        snapshot = self.snapshots.first()

        self.mox.StubOutWithMock(api.nova, 'server_get')
        self.mox.StubOutWithMock(api.nova, 'snapshot_create')
        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.nova.snapshot_create(IsA(http.HttpRequest), server.id,
                                 snapshot.name).AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.tenant.id,
                    'instance_id': server.id,
                    'name': snapshot.name}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_snapshot_post_exception(self):
        server = self.servers.first()
        snapshot = self.snapshots.first()

        self.mox.StubOutWithMock(api.nova, 'server_get')
        self.mox.StubOutWithMock(api.nova, 'snapshot_create')
        api.nova.snapshot_create(IsA(http.HttpRequest), server.id,
                                 snapshot.name).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.tenant.id,
                    'instance_id': server.id,
                    'name': snapshot.name}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        res = self.client.post(url, formData)
        redirect = reverse("horizon:project:instances:index")
        self.assertRedirectsNoFollow(res, redirect)
