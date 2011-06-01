# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
Unit tests for volume views.
"""

import boto.ec2.volume
import mox

from django.core.urlresolvers import reverse
from django_openstack.nova import forms
from django_openstack.nova.tests.base import (BaseProjectViewTests,
                                              TEST_PROJECT)


TEST_VOLUME = 'vol-0000001'


class VolumeTests(BaseProjectViewTests):
    def test_index(self):
        instance_id = 'i-abcdefgh'

        volume = boto.ec2.volume.Volume()
        volume.id = TEST_VOLUME
        volume.displayName = TEST_VOLUME
        volume.size = 1

        self.mox.StubOutWithMock(self.project, 'get_volumes')
        self.mox.StubOutWithMock(forms, 'get_available_volume_choices')
        self.mox.StubOutWithMock(forms, 'get_instance_choices')
        self.project.get_volumes().AndReturn([])
        forms.get_available_volume_choices(mox.IgnoreArg()).AndReturn(
                self.create_available_volume_choices([volume]))
        forms.get_instance_choices(mox.IgnoreArg()).AndReturn(
                self.create_instance_choices([instance_id]))

        self.mox.ReplayAll()

        response = self.client.get(reverse('nova_volumes',
                                           args=[TEST_PROJECT]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                'django_openstack/nova/volumes/index.html')
        self.assertEqual(len(response.context['volumes']), 0)

        self.mox.VerifyAll()

    def test_add_get(self):
        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_volumes_add', args=[TEST_PROJECT]))
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_add_post(self):
        vol = boto.ec2.volume.Volume()
        vol.name = TEST_VOLUME
        vol.displayName = TEST_VOLUME
        vol.size = 1

        self.mox.StubOutWithMock(self.project, 'create_volume')
        self.project.create_volume(vol.size, vol.name, vol.name).AndReturn(vol)

        self.mox.ReplayAll()

        url = reverse('nova_volumes_add', args=[TEST_PROJECT])
        data = {'size': '1',
                'nickname': TEST_VOLUME,
                'description': TEST_VOLUME}
        res = self.client.post(url, data)
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_delete_get(self):
        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_volumes_delete',
                                      args=[TEST_PROJECT, TEST_VOLUME]))
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_delete_post(self):
        self.mox.StubOutWithMock(self.project, 'delete_volume')
        self.project.delete_volume(TEST_VOLUME).AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.post(reverse('nova_volumes_delete',
                                       args=[TEST_PROJECT, TEST_VOLUME]))
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_attach_get(self):
        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_volumes_attach',
                                      args=[TEST_PROJECT]))
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_attach_post(self):
        volume = boto.ec2.volume.Volume()
        volume.id = TEST_VOLUME
        volume.displayName = TEST_VOLUME
        volume.size = 1

        instance_id = 'i-abcdefgh'
        device = '/dev/vdb'

        self.mox.StubOutWithMock(self.project, 'attach_volume')
        self.mox.StubOutWithMock(forms, 'get_available_volume_choices')
        self.mox.StubOutWithMock(forms, 'get_instance_choices')
        self.project.attach_volume(TEST_VOLUME, instance_id, device) \
                    .AndReturn(True)
        forms.get_available_volume_choices(mox.IgnoreArg()).AndReturn(
                self.create_available_volume_choices([volume]))
        forms.get_instance_choices(mox.IgnoreArg()).AndReturn(
                self.create_instance_choices([instance_id]))

        self.mox.ReplayAll()

        url = reverse('nova_volumes_attach', args=[TEST_PROJECT])
        data = {'volume': TEST_VOLUME,
                'instance': instance_id,
                'device': device}
        res = self.client.post(url, data)
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_detach_get(self):
        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_volumes_detach',
                                      args=[TEST_PROJECT, TEST_VOLUME]))
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_detach_post(self):
        self.mox.StubOutWithMock(self.project, 'detach_volume')
        self.project.detach_volume(TEST_VOLUME).AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.post(reverse('nova_volumes_detach',
                                       args=[TEST_PROJECT, TEST_VOLUME]))
        self.assertRedirectsNoFollow(res, reverse('nova_volumes',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()
