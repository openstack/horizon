# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright 2011 OpenStack LLC
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
from mox import IsA

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class ImagesAndSnapshotsTests(test.BaseViewTests):
    def setUp(self):
        super(ImagesAndSnapshotsTests, self).setUp()
        snapshot_dict = {'name': 'snapshot',
                         'container_format': 'ami',
                         'id': 3}
        snapshot = api.Image(snapshot_dict)
        self.snapshots = [snapshot, ]

        image_dict = {'name': 'visibleImage',
                      'container_format': 'novaImage'}
        self.visibleImage = api.Image(image_dict)
        self.visibleImage.id = '1'

        image_dict = {'name': 'invisibleImage',
                      'container_format': 'aki'}
        self.invisibleImage = api.Image(image_dict)
        self.invisibleImage.id = '2'

        flavor = api.Flavor(None)
        flavor.id = 1
        flavor.name = 'm1.massive'
        flavor.vcpus = 1000
        flavor.disk = 1024
        flavor.ram = 10000
        self.flavors = (flavor,)

        self.images = (self.visibleImage, self.invisibleImage)

        keypair = api.KeyPair(None)
        keypair.name = 'keyName'
        self.keypairs = (keypair,)

        security_group = api.SecurityGroup(None)
        security_group.name = 'default'
        self.security_groups = (security_group,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'image_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn(self.images)

        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        api.snapshot_list_detailed(IsA(http.HttpRequest)).AndReturn(
                self.snapshots)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        self.mox.StubOutWithMock(api, 'security_group_list')
        api.security_group_list(IsA(http.HttpRequest)).\
                                AndReturn(self.security_groups)
        api.security_group_list(IsA(http.HttpRequest)).\
                                AndReturn(self.security_groups)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                self.TEST_TENANT).AndReturn({})

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/index.html')

        self.assertIn('images', res.context)
        images = res.context['images']
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].name, 'visibleImage')

    def test_index_no_images(self):
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        api.snapshot_list_detailed(IsA(http.HttpRequest)).\
                                   AndReturn(self.snapshots)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        self.mox.StubOutWithMock(api, 'security_group_list')
        api.security_group_list(IsA(http.HttpRequest)).\
                                AndReturn(self.security_groups)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.StubOutWithMock(api, 'image_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn([])

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest), self.TEST_TENANT) \
                .AndReturn({})

        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'nova/images_and_snapshots/index.html')

    def test_index_client_conn_error(self):

        self.mox.StubOutWithMock(api, 'image_list_detailed')
        exception = glance_exception.ClientConnectionError('clientConnError')
        api.image_list_detailed(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest), self.TEST_TENANT) \
                .AndReturn({})

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'nova/images_and_snapshots/index.html')
