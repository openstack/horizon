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
from keystoneclient import exceptions as keystone_exceptions
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test


IMAGES_INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class FakeQuota:
    ram = 100


class ImageViewTests(test.BaseViewTests):
    def setUp(self):
        super(ImageViewTests, self).setUp()
        image_dict = {'name': 'visibleImage',
                      'container_format': 'novaImage'}
        self.visibleImage = api.Image(image_dict)
        self.visibleImage.id = 1

        image_dict = {'name': 'invisibleImage',
                      'container_format': 'aki'}
        self.invisibleImage = api.Image(image_dict)
        self.invisibleImage.id = 2

        self.images = (self.visibleImage, self.invisibleImage)

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

        volume = api.Volume(None)
        volume.id = 1
        volume.name = 'vol'
        volume.status = 'available'
        volume.size = 40
        volume.displayName = ''
        self.volumes = (volume,)

    def test_launch_get(self):
        IMAGE_ID = 1

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')

        api.image_get_meta(IsA(http.HttpRequest), str(IMAGE_ID)) \
                          .AndReturn(self.visibleImage)

        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        api.security_group_list(IsA(http.HttpRequest)).AndReturn(
                                    self.security_groups)

        self.mox.ReplayAll()

        res = self.client.get(
                    reverse('horizon:nova:images_and_snapshots:images:launch',
                            args=[IMAGE_ID]))
        form = res.context['form']

        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/launch.html')
        self.assertEqual(res.context['image'].name, self.visibleImage.name)
        self.assertIn('m1.massive', form.fields['flavor'].choices[0][1])
        self.assertEqual(form.fields['keypair'].choices[0][0],
                         self.keypairs[0].name)

    def test_launch_post(self):
        FLAVOR_ID = self.flavors[0].id
        IMAGE_ID = '1'
        keypair = self.keypairs[0].name
        SERVER_NAME = 'serverName'
        USER_DATA = 'userData'
        volume = self.volumes[0].id
        device_name = 'vda'
        BLOCK_DEVICE_MAPPING = {device_name: "1:::0"}

        form_data = {'method': 'LaunchForm',
                     'flavor': FLAVOR_ID,
                     'image_id': IMAGE_ID,
                     'keypair': keypair,
                     'name': SERVER_NAME,
                     'user_data': USER_DATA,
                     'count': 1,
                     'tenant_id': self.TEST_TENANT,
                     'security_groups': 'default',
                     'volume': volume,
                     'device_name': device_name
                     }

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'server_create')
        self.mox.StubOutWithMock(api, 'volume_list')

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)
        api.security_group_list(IsA(http.HttpRequest)).AndReturn(
                                    self.security_groups)
        api.image_get_meta(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes)
        api.server_create(IsA(http.HttpRequest), SERVER_NAME,
                          str(IMAGE_ID), str(FLAVOR_ID),
                          keypair, USER_DATA, [self.security_groups[0].name],
                          BLOCK_DEVICE_MAPPING,
                          instance_count=IsA(int))

        self.mox.ReplayAll()

        res = self.client.post(
                    reverse('horizon:nova:images_and_snapshots:images:launch',
                            args=[IMAGE_ID]),
                            form_data)

        self.assertRedirectsNoFollow(res,
                 reverse('horizon:nova:instances_and_volumes:index'))

    def test_launch_flavorlist_error(self):
        IMAGE_ID = '1'

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')

        api.image_get_meta(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)
        exception = keystone_exceptions.ClientException('Failed.')
        api.flavor_list(IsA(http.HttpRequest)).AndRaise(exception)
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)
        api.security_group_list(IsA(http.HttpRequest)).AndReturn(
                                    self.security_groups)

        self.mox.ReplayAll()

        res = self.client.get(
                    reverse('horizon:nova:images_and_snapshots:images:launch',
                            args=[IMAGE_ID]))

        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/launch.html')

    def test_launch_keypairlist_error(self):
        IMAGE_ID = '2'

        self.mox.StubOutWithMock(api, 'image_get_meta')
        api.image_get_meta(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        exception = keystone_exceptions.ClientException('Failed.')
        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(api, 'security_group_list')
        api.security_group_list(IsA(http.HttpRequest)).AndReturn(
                                    self.security_groups)

        self.mox.ReplayAll()

        res = self.client.get(
                    reverse('horizon:nova:images_and_snapshots:images:launch',
                            args=[IMAGE_ID]))

        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/launch.html')

        form = res.context['form']

        form_keyfield = form.fields['keypair']
        self.assertEqual(len(form_keyfield.choices), 0)

    def test_launch_form_keystone_exception(self):
        FLAVOR_ID = self.flavors[0].id
        IMAGE_ID = '1'
        keypair = self.keypairs[0].name
        SERVER_NAME = 'serverName'
        USER_DATA = 'userData'

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'server_create')
        self.mox.StubOutWithMock(api, 'volume_list')

        form_data = {'method': 'LaunchForm',
                     'flavor': FLAVOR_ID,
                     'image_id': IMAGE_ID,
                     'keypair': keypair,
                     'name': SERVER_NAME,
                     'tenant_id': self.TEST_TENANT,
                     'user_data': USER_DATA,
                     'count': int(1),
                     'security_groups': 'default'}

        api.flavor_list(IgnoreArg()).AndReturn(self.flavors)
        api.keypair_list(IgnoreArg()).AndReturn(self.keypairs)
        api.security_group_list(IsA(http.HttpRequest)).AndReturn(
                                    self.security_groups)
        api.image_get_meta(IgnoreArg(),
                      IMAGE_ID).AndReturn(self.visibleImage)
        api.volume_list(IgnoreArg()).AndReturn(self.volumes)

        exception = keystone_exceptions.ClientException('Failed')
        api.server_create(IsA(http.HttpRequest),
                          SERVER_NAME,
                          IMAGE_ID,
                          str(FLAVOR_ID),
                          keypair,
                          USER_DATA,
                          [group.name for group in self.security_groups],
                          None,
                          instance_count=IsA(int)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()
        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[IMAGE_ID])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, IMAGES_INDEX_URL)
