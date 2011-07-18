from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IsA

import openstackx.api.exceptions as api_exceptions

class KeyPairViewTests(base.BaseViewTests):
    def setUp(self):
        super(KeyPairViewTests, self).setUp()
        keypair_inner = base.Object()
        keypair_inner.key_name = 'keyName'
        self.keypairs = (api.KeyPair(keypair_inner),)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_keypairs', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'dash_keypairs.html')
        self.assertItemsEqual(res.context['keypairs'], self.keypairs)

        self.mox.VerifyAll()

    def test_index_exception(self):
        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')
        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(str))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_keypairs', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'dash_keypairs.html')
        self.assertEqual(len(res.context['keypairs']), 0)

        self.mox.VerifyAll()

    def test_delete_keypair(self):
        KEYPAIR_ID = self.keypairs[0].key_name
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
        KEYPAIR_ID = self.keypairs[0].key_name
        formData = {'method': 'DeleteKeypair',
                    'keypair_id': KEYPAIR_ID,
                    }

        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')
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
        
        self.assertTemplateUsed(res, 'dash_keypairs_create.html')

    def test_create_keypair_post(self):
        KEYPAIR_NAME = 'newKeypair'
        PRIVATE_KEY = 'privateKey'

        newKeyPair = self.mox.CreateMock(api.KeyPair)
        newKeyPair.key_name = KEYPAIR_NAME
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

        exception = api_exceptions.ApiException('apiException',
                                                message='apiException')
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
