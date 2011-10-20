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
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IsA

from novaclient import exceptions as novaclient_exceptions


class KeyPairViewTests(base.BaseViewTests):
    def setUp(self):
        super(KeyPairViewTests, self).setUp()
        keypair = self.mox.CreateMock(api.KeyPair)
        keypair.name = 'keyName'
        self.keypairs = (keypair,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_keypairs',
            args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/keypairs/index.html')
        self.assertItemsEqual(res.context['keypairs'], self.keypairs)

        self.mox.VerifyAll()

    def test_index_exception(self):
        exception = novaclient_exceptions.ClientException('clientException',
                                                message='clientException')
        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_keypairs',
            args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/keypairs/index.html')
        self.assertEqual(len(res.context['keypairs']), 0)

        self.mox.VerifyAll()

    def test_delete_keypair(self):
        KEYPAIR_ID = self.keypairs[0].name
        formData = {'method': 'DeleteKeypair',
                    'keypair_id': KEYPAIR_ID,
                    }

        self.mox.StubOutWithMock(api, 'keypair_delete')
        api.keypair_delete(IsA(http.HttpRequest), unicode(KEYPAIR_ID))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_keypairs',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_keypairs',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_delete_keypair_exception(self):
        KEYPAIR_ID = self.keypairs[0].name
        formData = {'method': 'DeleteKeypair',
                    'keypair_id': KEYPAIR_ID,
                    }

        exception = novaclient_exceptions.ClientException('clientException',
                                                message='clientException')
        self.mox.StubOutWithMock(api, 'keypair_delete')
        api.keypair_delete(IsA(http.HttpRequest),
                           unicode(KEYPAIR_ID)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_keypairs',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_keypairs',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_create_keypair_get(self):
        res = self.client.get(reverse('dash_keypairs_create',
                                      args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/keypairs/create.html')

    def test_create_keypair_post(self):
        KEYPAIR_NAME = 'newKeypair'
        PRIVATE_KEY = 'privateKey'

        newKeyPair = self.mox.CreateMock(api.KeyPair)
        newKeyPair.name = KEYPAIR_NAME
        newKeyPair.private_key = PRIVATE_KEY

        formData = {'method': 'CreateKeypair',
                    'name': KEYPAIR_NAME,
                    }

        self.mox.StubOutWithMock(api, 'keypair_create')
        api.keypair_create(IsA(http.HttpRequest),
                           KEYPAIR_NAME).AndReturn(newKeyPair)

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_keypairs_create',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertTrue(res.has_header('Content-Disposition'))

        self.mox.VerifyAll()

    def test_create_keypair_exception(self):
        KEYPAIR_NAME = 'newKeypair'

        formData = {'method': 'CreateKeypair',
                    'name': KEYPAIR_NAME,
                    }

        exception = novaclient_exceptions.ClientException('clientException',
                                                message='clientException')
        self.mox.StubOutWithMock(api, 'keypair_create')
        api.keypair_create(IsA(http.HttpRequest),
                           KEYPAIR_NAME).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_keypairs_create',
                                       args=[self.TEST_TENANT]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_keypairs_create',
                                                  args=[self.TEST_TENANT]))

        self.mox.VerifyAll()
