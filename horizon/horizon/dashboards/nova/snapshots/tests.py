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

    def test_index(self):
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        api.snapshot_list_detailed(IsA(http.HttpRequest)).\
                                   AndReturn(self.images)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.StubOutWithMock(api, 'security_group_list')
        api.security_group_list(IsA(http.HttpRequest)).AndReturn(
                                    self.security_groups)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:snapshots:index'))

        self.assertTemplateUsed(res, 'nova/snapshots/index.html')

        self.assertIn('images', res.context)
        images = res.context['images']
        self.assertEqual(len(images), 1)

    def test_index_client_conn_error(self):
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        exception = glance_exception.ClientConnectionError('clientConnError')
        api.snapshot_list_detailed(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:snapshots:index'))

        self.assertTemplateUsed(res, 'nova/snapshots/index.html')

    def test_index_glance_error(self):
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        exception = glance_exception.GlanceException('glanceError')
        api.snapshot_list_detailed(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:snapshots:index'))

        self.assertTemplateUsed(res, 'nova/snapshots/index.html')

    def test_create_snapshot_get(self):
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndReturn(self.good_server)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:snapshots:create',
                                      args=[self.good_server.id]))

        self.assertTemplateUsed(res, 'nova/snapshots/create.html')

    def test_create_snapshot_get_with_invalid_status(self):
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.bad_server.id)).AndReturn(self.bad_server)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:snapshots:create',
                                      args=[self.bad_server.id]))

        self.assertRedirectsNoFollow(res,
                reverse('horizon:nova:instances_and_volumes:instances:index'))

    def test_create_get_server_exception(self):
        self.mox.StubOutWithMock(api, 'server_get')
        exception = api_exceptions.ApiException('apiException')
        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:snapshots:create',
                                      args=[self.good_server.id]))

        self.assertRedirectsNoFollow(res,
                reverse('horizon:nova:instances_and_volumes:instances:index'))

    def test_create_snapshot_post(self):
        SNAPSHOT_NAME = 'snappy'

        new_snapshot = self.mox.CreateMock(api.Image)
        new_snapshot.name = SNAPSHOT_NAME

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.TEST_TENANT,
                    'instance_id': self.good_server.id,
                    'name': SNAPSHOT_NAME}

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest),
                       str(self.good_server.id)).AndReturn(self.good_server)

        self.mox.StubOutWithMock(api, 'snapshot_create')
        api.snapshot_create(IsA(http.HttpRequest),
                            str(self.good_server.id), SNAPSHOT_NAME).\
                            AndReturn(new_snapshot)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:snapshots:create',
                                      args=[self.good_server.id]),
                               formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:nova:snapshots:index'))

    def test_create_snapshot_post_exception(self):
        SNAPSHOT_NAME = 'snappy'

        new_snapshot = self.mox.CreateMock(api.Image)
        new_snapshot.name = SNAPSHOT_NAME

        formData = {'method': 'CreateSnapshot',
                    'tenant_id': self.TEST_TENANT,
                    'instance_id': self.good_server.id,
                    'name': SNAPSHOT_NAME}

        self.mox.StubOutWithMock(api, 'snapshot_create')
        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')
        api.snapshot_create(IsA(http.HttpRequest),
                            str(self.good_server.id), SNAPSHOT_NAME).\
                            AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:snapshots:create',
                                      args=[self.good_server.id]),
                               formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:nova:snapshots:create',
                                             args=[self.good_server.id]))
