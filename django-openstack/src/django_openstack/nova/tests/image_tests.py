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
Unit tests for image views.
"""

import boto.ec2.image
import boto.ec2.instance
import mox

from django.core.urlresolvers import reverse
from django_openstack.nova import forms
from django_openstack.nova import shortcuts
from django_openstack.nova.tests.base import (BaseProjectViewTests,
                                              TEST_PROJECT)


TEST_IMAGE_ID = 'ami_test'
TEST_INSTANCE_ID = 'i-abcdefg'
TEST_KEY = 'foo'


class ImageViewTests(BaseProjectViewTests):
    def setUp(self):
        self.ami = boto.ec2.image.Image()
        self.ami.id = TEST_IMAGE_ID
        setattr(self.ami, 'displayName', TEST_IMAGE_ID)
        setattr(self.ami, 'description', TEST_IMAGE_ID)
        super(ImageViewTests, self).setUp()

    def test_index(self):
        self.mox.StubOutWithMock(self.project, 'get_images')
        self.mox.StubOutWithMock(forms, 'get_key_pair_choices')
        self.mox.StubOutWithMock(forms, 'get_instance_type_choices')

        self.project.get_images().AndReturn([])
        forms.get_key_pair_choices(self.project).AndReturn([])
        forms.get_instance_type_choices().AndReturn([])

        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_images', args=[TEST_PROJECT]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'django_openstack/nova/images/index.html')
        self.assertEqual(len(res.context['image_lists']), 3)

        self.mox.VerifyAll()

    def test_launch_form(self):
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.mox.StubOutWithMock(forms, 'get_key_pair_choices')
        self.mox.StubOutWithMock(forms, 'get_instance_type_choices')

        self.project.get_image(TEST_IMAGE_ID).AndReturn(self.ami)
        forms.get_key_pair_choices(self.project).AndReturn([])
        forms.get_instance_type_choices().AndReturn([])

        self.mox.ReplayAll()

        args = [TEST_PROJECT, TEST_IMAGE_ID]
        res = self.client.get(reverse('nova_images_launch', args=args))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                'django_openstack/nova/images/launch.html')
        self.assertEqual(res.context['ami'].id, TEST_IMAGE_ID)

        self.mox.VerifyAll()

    def test_launch(self):
        instance = boto.ec2.instance.Instance()
        instance.id = TEST_INSTANCE_ID
        instance.image_id = TEST_IMAGE_ID
        reservation = boto.ec2.instance.Reservation()
        reservation.instances = [instance]

        conn = self.mox.CreateMockAnything()

        self.mox.StubOutWithMock(forms, 'get_key_pair_choices')
        self.mox.StubOutWithMock(forms, 'get_instance_type_choices')
        self.mox.StubOutWithMock(self.project, 'get_openstack_connection')

        self.project.get_openstack_connection().AndReturn(conn)

        forms.get_key_pair_choices(self.project).AndReturn(
                self.create_key_pair_choices([TEST_KEY]))
        forms.get_instance_type_choices().AndReturn(
                self.create_instance_type_choices())

        params = {'addressing_type': 'private',
                'UserData': '', 'display_name': u'name',
                'MinCount': '1', 'key_name': TEST_KEY,
                'MaxCount': '1', 'InstanceType': 'm1.medium',
                'ImageId': TEST_IMAGE_ID}
        conn.get_object('RunInstances', params, boto.ec2.instance.Reservation,
                verb='POST').AndReturn(reservation)

        self.mox.ReplayAll()

        url = reverse('nova_images_launch', args=[TEST_PROJECT, TEST_IMAGE_ID])
        data = {'key_name': TEST_KEY,
                'count': '1',
                'size': 'm1.medium',
                'display_name': 'name',
                'user_data': ''}
        res = self.client.post(url, data)
        self.assertRedirectsNoFollow(res, reverse('nova_instances',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_detail(self):
        self.mox.StubOutWithMock(self.project, 'get_images')
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.mox.StubOutWithMock(shortcuts, 'get_user_image_permissions')
        self.mox.StubOutWithMock(forms, 'get_key_pair_choices')
        self.mox.StubOutWithMock(forms, 'get_instance_type_choices')

        self.project.get_images().AndReturn([self.ami])
        self.project.get_image(TEST_IMAGE_ID).AndReturn(self.ami)
        forms.get_key_pair_choices(self.project).AndReturn(
            self.create_key_pair_choices([TEST_KEY]))
        forms.get_instance_type_choices().AndReturn(
            self.create_instance_type_choices())

        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_images_detail',
                                      args=[TEST_PROJECT, TEST_IMAGE_ID]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'django_openstack/nova/images/index.html')
        self.assertEqual(res.context['ami'].id, TEST_IMAGE_ID)

        self.mox.VerifyAll()

    def test_remove_form(self):
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_images_remove',
                                      args=[TEST_PROJECT, TEST_IMAGE_ID]))
        self.assertRedirectsNoFollow(res, reverse('nova_images',
                                                  args=[TEST_PROJECT]))
        self.mox.VerifyAll()

    def test_remove(self):
        self.mox.StubOutWithMock(self.project, 'deregister_image')
        self.project.deregister_image(TEST_IMAGE_ID).AndReturn(True)
        self.mox.ReplayAll()

        res = self.client.post(reverse('nova_images_remove',
                                       args=[TEST_PROJECT, TEST_IMAGE_ID]))
        self.assertRedirectsNoFollow(res, reverse('nova_images',
                                                  args=[TEST_PROJECT]))

        self.mox.VerifyAll()

    def test_make_public(self):
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.mox.StubOutWithMock(self.project, 'modify_image_attribute')

        self.ami.is_public = False
        self.project.get_image(TEST_IMAGE_ID).AndReturn(self.ami)
        self.project.modify_image_attribute(TEST_IMAGE_ID,
                                            attribute='launchPermission',
                                            operation='add').AndReturn(True)
        self.mox.ReplayAll()

        res = self.client.post(reverse('nova_images_privacy',
                                       args=[TEST_PROJECT, TEST_IMAGE_ID]))
        self.assertRedirectsNoFollow(res, reverse('nova_images_detail',
                                          args=[TEST_PROJECT, TEST_IMAGE_ID]))
        self.mox.VerifyAll()

    def test_make_private(self):
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.mox.StubOutWithMock(self.project, 'modify_image_attribute')

        self.ami.is_public = True
        self.project.get_image(TEST_IMAGE_ID).AndReturn(self.ami)
        self.project.modify_image_attribute(TEST_IMAGE_ID,
                                            attribute='launchPermission',
                                            operation='remove').AndReturn(True)
        self.mox.ReplayAll()

        args = [TEST_PROJECT, TEST_IMAGE_ID]
        res = self.client.post(reverse('nova_images_privacy', args=args))
        self.assertRedirectsNoFollow(res, reverse('nova_images_detail',
                                                  args=args))
        self.mox.VerifyAll()

    def test_update_form(self):
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.project.get_image(TEST_IMAGE_ID).AndReturn(self.ami)
        self.mox.ReplayAll()

        args = [TEST_PROJECT, TEST_IMAGE_ID]
        res = self.client.get(reverse('nova_images_update', args=args))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'django_openstack/nova/images/edit.html')
        self.assertEqual(res.context['ami'].id, TEST_IMAGE_ID)

        self.mox.VerifyAll()

    def test_update(self):
        self.mox.StubOutWithMock(self.project, 'get_image')
        self.mox.StubOutWithMock(self.project, 'update_image')

        self.project.get_image(TEST_IMAGE_ID).AndReturn(self.ami)
        self.project.update_image(TEST_IMAGE_ID, 'test', 'test') \
                .AndReturn(True)

        self.mox.ReplayAll()

        args = [TEST_PROJECT, TEST_IMAGE_ID]
        data = {'nickname': 'test',
                'description': 'test'}
        url = reverse('nova_images_update', args=args)
        res = self.client.post(url, data)
        expected_url = reverse('nova_images_detail', args=args)
        self.assertRedirectsNoFollow(res, expected_url)

        self.mox.VerifyAll()
