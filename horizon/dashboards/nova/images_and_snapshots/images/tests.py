# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import http
from django.core.urlresolvers import reverse

from glance.common import exception as glance_exception

from horizon import api
from horizon import test

from keystoneclient import exceptions as keystone_exceptions

from mox import IgnoreArg, IsA


IMAGES_INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class ImageViewTests(test.TestCase):
    def test_launch_get(self):
        image = self.images.first()
        quota_usages = self.quota_usages.first()

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'tenant_quota_usages')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        api.image_get_meta(IsA(http.HttpRequest), image.id).AndReturn(image)
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(quota_usages)
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        self.mox.ReplayAll()

        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[image.id])
        res = self.client.get(url)
        form = res.context['form']
        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/launch.html')
        self.assertEqual(res.context['image'].name, image.name)
        self.assertIn(self.flavors.first().name,
                      form.fields['flavor'].choices[0][1])
        self.assertEqual(self.keypairs.first().name,
                         form.fields['keypair'].choices[1][0])

    def test_launch_post(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        USER_DATA = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        block_device_mapping = {device_name: u"%s::0" % volume_choice}

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'server_create')
        self.mox.StubOutWithMock(api, 'volume_list')

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.image_get_meta(IsA(http.HttpRequest), image.id).AndReturn(image)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_create(IsA(http.HttpRequest),
                          server.name,
                          image.id,
                          flavor.id,
                          keypair.name,
                          USER_DATA,
                          [sec_group.name],
                          block_device_mapping,
                          instance_count=IsA(int))
        self.mox.ReplayAll()

        form_data = {'method': 'LaunchForm',
                     'flavor': flavor.id,
                     'image_id': image.id,
                     'keypair': keypair.name,
                     'name': server.name,
                     'user_data': USER_DATA,
                     'tenant_id': self.tenants.first().id,
                     'security_groups': sec_group.name,
                     'volume': volume_choice,
                     'device_name': device_name,
                     'count': 1}
        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[image.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                 reverse('horizon:nova:instances_and_volumes:index'))

    def test_launch_flavorlist_error(self):
        image = self.images.first()

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'tenant_quota_usages')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        api.image_get_meta(IsA(http.HttpRequest),
                           image.id).AndReturn(image)
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(
                self.quota_usages.first())
        exc = keystone_exceptions.ClientException('Failed.')
        api.flavor_list(IsA(http.HttpRequest)).AndRaise(exc)
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        self.mox.ReplayAll()

        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[image.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/launch.html')

    def test_launch_keypairlist_error(self):
        image = self.images.first()

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'tenant_quota_usages')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        api.image_get_meta(IsA(http.HttpRequest), image.id).AndReturn(image)
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(
                self.quota_usages.first())
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        exception = keystone_exceptions.ClientException('Failed.')
        api.keypair_list(IsA(http.HttpRequest)).AndRaise(exception)
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        self.mox.ReplayAll()

        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[image.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/launch.html')
        self.assertEqual(len(res.context['form'].fields['keypair'].choices), 1)

    def test_launch_form_keystone_exception(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        USER_DATA = 'userData'

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'server_create')
        self.mox.StubOutWithMock(api, 'volume_list')

        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.keypair_list(IgnoreArg()).AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.image_get_meta(IgnoreArg(), image.id).AndReturn(image)
        api.volume_list(IgnoreArg()).AndReturn(self.volumes.list())
        exc = keystone_exceptions.ClientException('Failed')
        api.server_create(IsA(http.HttpRequest),
                          server.name,
                          image.id,
                          flavor.id,
                          keypair.name,
                          USER_DATA,
                          [sec_group.name],
                          None,
                          instance_count=IsA(int)).AndRaise(exc)
        self.mox.ReplayAll()

        form_data = {'method': 'LaunchForm',
                     'flavor': flavor.id,
                     'image_id': image.id,
                     'keypair': keypair.name,
                     'name': server.name,
                     'tenant_id': self.tenant.id,
                     'user_data': USER_DATA,
                     'count': 1,
                     'security_groups': sec_group.name}
        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[image.id])
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, IMAGES_INDEX_URL)

    def test_launch_form_instance_count_error(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        USER_DATA = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        block_device_mapping = {device_name: u"%s::0" % volume_choice}

        self.mox.StubOutWithMock(api, 'image_get_meta')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'volume_snapshot_list')
        self.mox.StubOutWithMock(api, 'tenant_quota_usages')

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.image_get_meta(IsA(http.HttpRequest), image.id).AndReturn(image)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        api.tenant_quota_usages(IsA(http.HttpRequest)) \
                                .AndReturn(self.quota_usages.first())
        self.mox.ReplayAll()

        form_data = {'method': 'LaunchForm',
                     'flavor': flavor.id,
                     'image_id': image.id,
                     'keypair': keypair.name,
                     'name': server.name,
                     'user_data': USER_DATA,
                     'tenant_id': self.tenants.first().id,
                     'security_groups': sec_group.name,
                     'volume': volume_choice,
                     'device_name': device_name,
                     'count': 0}
        url = reverse('horizon:nova:images_and_snapshots:images:launch',
                      args=[image.id])
        res = self.client.post(url, form_data)
        self.assertFormErrors(res, count=1)

    def test_image_detail_get(self):
        image = self.images.first()
        self.mox.StubOutWithMock(api.glance, 'image_get_meta')
        api.glance.image_get_meta(IsA(http.HttpRequest), str(image.id)) \
                                 .AndReturn(self.images.first())
        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:images_and_snapshots:images:detail',
                args=[image.id]))
        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/detail.html')
        self.assertEqual(res.context['image'].name, image.name)

    def test_image_detail_get_with_exception(self):
        image = self.images.first()
        self.mox.StubOutWithMock(api.glance, 'image_get_meta')
        api.glance.image_get_meta(IsA(http.HttpRequest), str(image.id)) \
                                 .AndRaise(glance_exception.NotFound)
        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:images_and_snapshots:images:detail',
                args=[image.id]))
        self.assertRedirectsNoFollow(res, IMAGES_INDEX_URL)
