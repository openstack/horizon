# vim: tabstop=4 shiftwidth=4 softtabstop=4
import logging

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from glance.common import exception as glance_exception
from openstackx.api import exceptions as api_exceptions
from mox import IgnoreArg, IsA


class FakeQuota:
    ram = 100


class ImageViewTests(base.BaseViewTests):
    def setUp(self):
        super(ImageViewTests, self).setUp()
        image_dict = {'name': 'visibleImage',
                      'container_format': 'novaImage'}
        self.visibleImage = api.Image(image_dict)

        image_dict = {'name': 'invisibleImage',
                      'container_format': 'aki'}
        self.invisibleImage = api.Image(image_dict)

        self.images = (self.visibleImage, self.invisibleImage)

        flavor_inner = base.Object()
        flavor_inner.id = 1
        flavor_inner.name = 'm1.massive'
        flavor_inner.vcpus = 1000
        flavor_inner.disk = 1024
        flavor_inner.ram = 10000
        self.flavors = (api.Flavor(flavor_inner),)

        keypair_inner = base.Object()
        keypair_inner.key_name = 'keyName'
        self.keypairs = (api.KeyPair(keypair_inner),)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest), self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'image_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn(self.images)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'dash_images.html')

        self.assertIn('images', res.context)
        images = res.context['images']
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].name, 'visibleImage')

        self.mox.VerifyAll()

    def test_index_no_images(self):
        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest), self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'image_list_detailed')
        api.image_list_detailed(IsA(http.HttpRequest)).AndReturn([])

        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(str))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'dash_images.html')

        self.mox.VerifyAll()

    def test_index_client_conn_error(self):
        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest), self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'image_list_detailed')
        exception = glance_exception.ClientConnectionError('clientConnError')
        api.image_list_detailed(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(str))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'dash_images.html')

        self.mox.VerifyAll()

    def test_index_glance_error(self):
        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest), self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'image_list_detailed')
        exception = glance_exception.Error('glanceError')
        api.image_list_detailed(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(str))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images', args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res, 'dash_images.html')

        self.mox.VerifyAll()

    def test_launch_get(self):
        IMAGE_ID = '1'

        self.mox.StubOutWithMock(api, 'image_get')
        api.image_get(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images_launch',
                              args=[self.TEST_TENANT, IMAGE_ID]))

        self.assertTemplateUsed(res, 'dash_launch.html')

        image = res.context['image']
        self.assertEqual(image.name, self.visibleImage.name)

        self.assertEqual(res.context['tenant'], self.TEST_TENANT)

        form = res.context['form']

        form_flavorfield = form.fields['flavor']
        self.assertIn('m1.massive', form_flavorfield.choices[0][1])

        form_keyfield = form.fields['key_name']
        self.assertEqual(form_keyfield.choices[0][0],
                         self.keypairs[0].key_name)

        self.mox.VerifyAll()

    def test_launch_post(self):
        FLAVOR_ID = self.flavors[0].id
        IMAGE_ID = '1'
        KEY_NAME = self.keypairs[0].key_name
        SERVER_NAME = 'serverName'
        USER_DATA = 'userData'

        form_data = {'method': 'LaunchForm',
                     'flavor': FLAVOR_ID,
                     'image_id': IMAGE_ID,
                     'key_name': KEY_NAME,
                     'name': SERVER_NAME,
                     'user_data': USER_DATA,
                     'tenant_id': self.TEST_TENANT,
                     }

        self.mox.StubOutWithMock(api, 'image_get')
        api.image_get(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        # called again by the form
        api.image_get(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'flavor_get')
        api.flavor_get(IsA(http.HttpRequest),
                       IsA(unicode)).AndReturn(self.flavors[0])

        self.mox.StubOutWithMock(api, 'server_create')

        api.server_create(IsA(http.HttpRequest), SERVER_NAME,
                          self.visibleImage, self.flavors[0],
                          KEY_NAME, USER_DATA)

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IsA(http.HttpRequest), IsA(str))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_images_launch',
                                        args=[self.TEST_TENANT, IMAGE_ID]),
                               form_data)

        self.assertRedirectsNoFollow(res, reverse('dash_instances',
                                          args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_launch_flavorlist_error(self):
        IMAGE_ID = '1'

        self.mox.StubOutWithMock(api, 'image_get')
        api.image_get(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        exception = api_exceptions.ApiException('apiException')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images_launch',
                              args=[self.TEST_TENANT, IMAGE_ID]))

        self.assertTemplateUsed(res, 'dash_launch.html')

        form = res.context['form']

        form_flavorfield = form.fields['flavor']
        self.assertIn('m1.tiny', form_flavorfield.choices[0][1])

        self.mox.VerifyAll()

    def test_launch_keypairlist_error(self):
        IMAGE_ID = '2'

        self.mox.StubOutWithMock(api, 'image_get')
        api.image_get(IsA(http.HttpRequest),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors)

        exception = api_exceptions.ApiException('apiException')
        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_images_launch',
                              args=[self.TEST_TENANT, IMAGE_ID]))

        self.assertTemplateUsed(res, 'dash_launch.html')

        form = res.context['form']

        form_keyfield = form.fields['key_name']
        self.assertEqual(len(form_keyfield.choices), 0)

        self.mox.VerifyAll()

    def test_launch_form_apiexception(self):
        FLAVOR_ID = self.flavors[0].id
        IMAGE_ID = '1'
        KEY_NAME = self.keypairs[0].key_name
        SERVER_NAME = 'serverName'
        USER_DATA = 'userData'

        form_data = {'method': 'LaunchForm',
                     'flavor': FLAVOR_ID,
                     'image_id': IMAGE_ID,
                     'key_name': KEY_NAME,
                     'name': SERVER_NAME,
                     'tenant_id': self.TEST_TENANT,
                     'user_data': USER_DATA,
                     }

        self.mox.StubOutWithMock(api, 'image_get')
        api.image_get(IgnoreArg(),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'token_get_tenant')
        api.token_get_tenant(IgnoreArg(),
                             self.TEST_TENANT).AndReturn(self.TEST_TENANT)

        self.mox.StubOutWithMock(api, 'tenant_quota_get')
        api.tenant_quota_get(IsA(http.HttpRequest),
                             self.TEST_TENANT).AndReturn(FakeQuota)

        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors)

        self.mox.StubOutWithMock(api, 'keypair_list')
        api.keypair_list(IgnoreArg()).AndReturn(self.keypairs)

        # called again by the form
        api.image_get(IgnoreArg(),
                      IMAGE_ID).AndReturn(self.visibleImage)

        self.mox.StubOutWithMock(api, 'flavor_get')
        api.flavor_get(IgnoreArg(),
                       IsA(unicode)).AndReturn(self.flavors[0])

        self.mox.StubOutWithMock(api, 'server_create')

        exception = api_exceptions.ApiException('apiException')
        api.server_create(IsA(http.HttpRequest), SERVER_NAME,
                          self.visibleImage, self.flavors[0],
                          KEY_NAME,
                          USER_DATA).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(str))

        self.mox.ReplayAll()
        url = reverse('dash_images_launch',
                      args=[self.TEST_TENANT, IMAGE_ID])
        res = self.client.post(url, form_data)

        self.assertTemplateUsed(res, 'dash_launch.html')

        self.mox.VerifyAll()
