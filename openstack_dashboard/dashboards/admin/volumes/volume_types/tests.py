# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA  # noqa

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.test import helpers as test


class VolumeTypeTests(test.BaseAdminViewTests):
    @test.create_stubs({cinder: ('volume_type_create',)})
    def test_create_volume_type(self):
        formData = {'name': 'volume type 1',
                    'vol_type_description': 'test desc'}
        cinder.volume_type_create(
            IsA(http.HttpRequest),
            formData['name'],
            formData['vol_type_description']).AndReturn(
                self.volume_types.first())
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volume_types:create_type'),
            formData)
        self.assertNoFormErrors(res)
        redirect = reverse('horizon:admin:volumes:volume_types_tab')
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({cinder: ('volume_type_get',
                                 'volume_type_update')})
    def test_update_volume_type(self):
        volume_type = self.cinder_volume_types.first()
        formData = {'name': volume_type.name,
                    'description': 'test desc updated'}
        volume_type = cinder.volume_type_get(
            IsA(http.HttpRequest), volume_type.id).AndReturn(volume_type)
        cinder.volume_type_update(
            IsA(http.HttpRequest),
            volume_type.id,
            formData['name'],
            formData['description']).AndReturn(volume_type)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:volume_types:update_type',
                      args=[volume_type.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        redirect = reverse('horizon:admin:volumes:volume_types_tab')
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list',
                                 'volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'volume_type_delete',
                                 'volume_encryption_type_list'),
                        keystone: ('tenant_list',)})
    def test_delete_volume_type(self):
        volume_type = self.cinder_volume_types.first()
        formData = {'action': 'volume_types__delete__%s' % volume_type.id}
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])

        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_qos_specs.list())
        cinder.volume_encryption_type_list(IsA(http.HttpRequest))\
            .AndReturn(encryption_list)
        cinder.volume_type_delete(IsA(http.HttpRequest),
                                  volume_type.id)
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volumes_tab'),
            formData)

        redirect = reverse('horizon:admin:volumes:volumes_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list',
                                 'volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'volume_type_delete',
                                 'volume_encryption_type_list'),
                        keystone: ('tenant_list',)})
    def test_delete_volume_type_exception(self):
        volume_type = self.volume_types.first()
        formData = {'action': 'volume_types__delete__%s' % volume_type.id}
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])

        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_qos_specs.list())
        cinder.volume_encryption_type_list(IsA(http.HttpRequest))\
            .AndReturn(encryption_list)
        cinder.volume_type_delete(IsA(http.HttpRequest),
                                  str(volume_type.id))\
            .AndRaise(exceptions.BadRequest())
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volumes_tab'),
            formData)

        redirect = reverse('horizon:admin:volumes:volumes_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({cinder: ('volume_encryption_type_create',
                                 'volume_type_list',)})
    def test_create_volume_type_encryption(self):
        volume_type1 = self.volume_types.list()[0]
        volume_type2 = self.volume_types.list()[1]
        volume_type1.id = u'1'
        volume_type2.id = u'2'
        volume_type_list = [volume_type1, volume_type2]
        formData = {'name': u'An Encrypted Volume Type',
                    'provider': u'a-provider',
                    'control_location': u'front-end',
                    'cipher': u'a-cipher',
                    'key_size': 512,
                    'volume_type_id': volume_type1.id}

        cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn(volume_type_list)
        cinder.volume_encryption_type_create(IsA(http.HttpRequest),
                                             formData['volume_type_id'],
                                             formData)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:'
                      'volume_types:create_type_encryption',
                      args=[volume_type1.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(
            res,
            'admin/volumes/volume_types/create_volume_type_encryption.html')

    @test.create_stubs({cinder: ('volume_encryption_type_get',
                                 'volume_type_list',)})
    def test_type_encryption_detail_view_unencrypted(self):
        volume_type1 = self.volume_types.list()[0]
        volume_type1.id = u'1'
        volume_type_list = [volume_type1]
        vol_unenc_type = self.cinder_volume_encryption_types.list()[2]

        cinder.volume_encryption_type_get(IsA(http.HttpRequest),
                                          volume_type1.id)\
            .AndReturn(vol_unenc_type)
        cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn(volume_type_list)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:'
                      'volume_types:type_encryption_detail',
                      args=[volume_type1.id])
        res = self.client.get(url)

        self.assertTemplateUsed(
            res,
            'admin/volumes/volume_types/volume_encryption_type_detail.html')

        self.assertContains(res,
                            "<h3>Volume Type is Unencrypted.</h3>", 1, 200)
        self.assertNoMessages()

    @test.create_stubs({cinder: ('volume_encryption_type_get',
                                 'volume_type_list',)})
    def test_type_encryption_detail_view_encrypted(self):
        volume_type = self.volume_types.first()
        volume_type.id = u'1'
        volume_type.name = "An Encrypted Volume Name"
        volume_type_list = [volume_type]
        vol_enc_type = self.cinder_volume_encryption_types.list()[0]

        cinder.volume_encryption_type_get(IsA(http.HttpRequest),
                                          volume_type.id)\
            .AndReturn(vol_enc_type)
        cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn(volume_type_list)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes'
                      ':volume_types:type_encryption_detail',
                      args=[volume_type.id])
        res = self.client.get(url)

        self.assertTemplateUsed(
            res,
            'admin/volumes/volume_types/volume_encryption_type_detail.html')

        self.assertContains(res, "<h3>Volume Type Encryption Overview</h3>", 1,
                            200)
        self.assertContains(res, "<dd>%s</dd>" % volume_type.name, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.control_location,
                            1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.key_size, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.provider, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.cipher, 1, 200)

        self.assertNoMessages()

    @test.create_stubs({cinder: ('extension_supported',
                                 'volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'volume_encryption_type_list',
                                 'volume_encryption_type_delete',)})
    def test_delete_volume_type_encryption(self):
        volume_type = self.volume_types.first()
        volume_type.id = u'1'
        formData = {'action': 'volume_types__delete_encryption__%s' %
                    volume_type.id}
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])

        cinder.extension_supported(IsA(http.HttpRequest),
                                   'VolumeTypeEncryption')\
            .AndReturn(True)
        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest))\
            .AndReturn(self.volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest))\
            .AndReturn(self.cinder_qos_specs.list())
        cinder.volume_encryption_type_list(IsA(http.HttpRequest))\
            .AndReturn(encryption_list)
        cinder.volume_encryption_type_delete(IsA(http.HttpRequest),
                                             volume_type.id)
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volume_types_tab'),
            formData)

        redirect = reverse('horizon:admin:volumes:volume_types_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({cinder: ('volume_encryption_type_update',
                                 'volume_encryption_type_get',
                                 'volume_type_list')})
    def test_update_volume_type_encryption(self):
        volume_type = self.volume_types.first()
        volume_type.id = u'1'
        volume_type_list = [volume_type]
        formData = {'name': u'An Encrypted Volume Type',
                    'provider': u'a-provider',
                    'control_location': u'front-end',
                    'cipher': u'a-cipher',
                    'key_size': 256,
                    'volume_type_id': volume_type.id}
        vol_enc_type = self.cinder_volume_encryption_types.list()[0]

        cinder.volume_encryption_type_get(IsA(http.HttpRequest),
                                          volume_type.id)\
            .AndReturn(vol_enc_type)
        cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn(volume_type_list)
        cinder.volume_encryption_type_update(IsA(http.HttpRequest),
                                             formData['volume_type_id'],
                                             formData)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:volumes:'
                      'volume_types:update_type_encryption',
                      args=[volume_type.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(
            res,
            'admin/volumes/volume_types/update_volume_type_encryption.html')
