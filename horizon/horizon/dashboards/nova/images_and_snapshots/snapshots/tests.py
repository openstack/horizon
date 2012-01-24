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
from django.contrib import messages
from django.core.urlresolvers import reverse
from glance.common import exception as glance_exception
from openstackx.api import exceptions as api_exceptions
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class SnapshotsViewTests(test.BaseViewTests):
    def setUp(self):
        super(SnapshotsViewTests, self).setUp()
        image_dict = {'name': 'snapshot',
                      'container_format': 'novaImage',
                      'id': 3}
        self.images = [image_dict]

        server = api.Server(None, self.request)
        server.id = 1
        server.status = 'ACTIVE'
        server.name = 'sgoody'
        self.good_server = server

        server = api.Server(None, self.request)
        server.id = 2
        server.status = 'BUILD'
        server.name = 'baddy'
        self.bad_server = server

        flavor = api.Flavor(None)
        flavor.id = 1
        flavor.name = 'm1.massive'
        flavor.vcpus = 1000
        flavor.disk = 1024
        flavor.ram = 10000
        self.flavors = (flavor,)

        keypair = api.KeyPair(None)
        keypair.name = 'keyName'
        self.keypairs = (keypair,)

        security_group = api.SecurityGroup(None)
        security_group.name = 'default'
        self.security_groups = (security_group,)

    def test_create_snapshot_get(self):
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndReturn(self.good_server)

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:images_and_snapshots:snapshots:create',
                        args=[self.good_server.id]))

        self.assertTemplateUsed(res,
                            'nova/images_and_snapshots/snapshots/create.html')

    def test_create_snapshot_get_with_invalid_status(self):
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.bad_server.id)).AndReturn(self.bad_server)

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:images_and_snapshots:snapshots:create',
                        args=[self.bad_server.id]))

        url = reverse("horizon:nova:instances_and_volumes:index")
        self.assertRedirectsNoFollow(res, url)

    def test_create_get_server_exception(self):
        self.mox.StubOutWithMock(api, 'server_get')
        exception = api_exceptions.ApiException('apiException')
        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:images_and_snapshots:snapshots:create',
                        args=[self.good_server.id]))

        url = reverse("horizon:nova:instances_and_volumes:index")
        self.assertRedirectsNoFollow(res, url)

    def test_create_snapshot_post(self):
        SNAPSHOT_NAME = 'snappy'

        new_snapshot = self.mox.CreateMock(api.Image)
        new_snapshot.name = SNAPSHOT_NAME

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.TEST_TENANT,
                    'instance_id': self.good_server.id,
                    'name': SNAPSHOT_NAME}

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'snapshot_create')

        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndReturn(self.good_server)
        api.snapshot_create(IsA(http.HttpRequest),
                            str(self.good_server.id), SNAPSHOT_NAME).\
                            AndReturn(new_snapshot)
        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndReturn(self.good_server)

        self.mox.ReplayAll()

        res = self.client.post(
                reverse('horizon:nova:images_and_snapshots:snapshots:create',
                        args=[self.good_server.id]),
                        formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_snapshot_post_exception(self):
        SNAPSHOT_NAME = 'snappy'

        new_snapshot = self.mox.CreateMock(api.Image)
        new_snapshot.name = SNAPSHOT_NAME

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.TEST_TENANT,
                    'instance_id': self.good_server.id,
                    'name': SNAPSHOT_NAME}

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'snapshot_create')

        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndReturn(self.good_server)
        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')
        api.snapshot_create(IsA(http.HttpRequest),
                            str(self.good_server.id), SNAPSHOT_NAME).\
                            AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(
                reverse('horizon:nova:images_and_snapshots:snapshots:create',
                        args=[self.good_server.id]),
                        formData)

        url = reverse("horizon:nova:instances_and_volumes:index")
        self.assertRedirectsNoFollow(res, url)
