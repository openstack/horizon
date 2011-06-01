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
Unit tests for key pair views.
"""

import boto.ec2.keypair
import mox

from django.core.urlresolvers import reverse
from django_openstack.nova.tests.base import (BaseProjectViewTests,
                                              TEST_PROJECT)


TEST_KEY = 'test_key'


class KeyPairViewTests(BaseProjectViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(self.project, 'get_key_pairs')
        self.project.get_key_pairs().AndReturn([])

        self.mox.ReplayAll()

        response = self.client.get(reverse('nova_keypairs',
                                           args=[TEST_PROJECT]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                'django_openstack/nova/keypairs/index.html')
        self.assertEqual(len(response.context['keypairs']), 0)

        self.mox.VerifyAll()

    def test_add_keypair(self):
        key = boto.ec2.keypair.KeyPair()
        key.name = TEST_KEY

        self.mox.StubOutWithMock(self.project, 'create_key_pair')
        self.project.create_key_pair(key.name).AndReturn(key)
        self.mox.StubOutWithMock(self.project, 'has_key_pair')
        self.project.has_key_pair(key.name).AndReturn(False)

        self.mox.ReplayAll()

        url = reverse('nova_keypairs_add', args=[TEST_PROJECT])
        data = {'js': '0', 'name': key.name}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/binary')

        self.mox.VerifyAll()

    def test_delete_keypair(self):
        self.mox.StubOutWithMock(self.project, 'delete_key_pair')
        self.project.delete_key_pair(TEST_KEY).AndReturn(None)

        self.mox.ReplayAll()

        data = {'key_name': TEST_KEY}
        url = reverse('nova_keypairs_delete', args=[TEST_PROJECT])
        res = self.client.post(url, data)
        self.assertRedirectsNoFollow(res, reverse('nova_keypairs',
                                                  args=[TEST_PROJECT]))

        self.mox.VerifyAll()

    def test_download_keypair(self):
        material = 'abcdefgh'
        session = self.client.session
        session['key.%s' % TEST_KEY] = material
        session.save()

        res = self.client.get(reverse('nova_keypairs_download',
                                      args=['test', TEST_KEY]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/binary')
        self.assertContains(res, material)
