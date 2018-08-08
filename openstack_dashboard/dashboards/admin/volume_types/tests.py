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

from django.urls import reverse
import mock

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:volume_types:index')


class VolumeTypeTests(test.BaseAdminViewTests):

    @test.create_mocks({api.cinder: ('volume_type_list_with_qos_associations',
                                     'qos_spec_list',
                                     'extension_supported',
                                     'volume_encryption_type_list')})
    def test_volume_types_tab(self):
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])
        self.mock_volume_type_list_with_qos_associations.return_value = \
            self.cinder_volume_types.list()
        self.mock_qos_spec_list.return_value = self.cinder_qos_specs.list()
        self.mock_volume_encryption_type_list.return_value = encryption_list
        self.mock_extension_supported.return_value = True

        res = self.client.get(INDEX_URL)

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(
            res, 'admin/volume_types/volume_types_tables.html')
        volume_types = res.context['volume_types_table'].data
        self.assertItemsEqual(volume_types, self.cinder_volume_types.list())
        qos_specs = res.context['qos_specs_table'].data
        self.assertItemsEqual(qos_specs, self.cinder_qos_specs.list())

        self.mock_volume_type_list_with_qos_associations.\
            assert_called_once_with(test.IsHttpRequest())
        self.mock_qos_spec_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_encryption_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_extension_supported.assert_has_calls(
            [mock.call(test.IsHttpRequest(), 'VolumeTypeEncryption')] * 9)
        self.assertEqual(9, self.mock_extension_supported.call_count)

    @test.create_mocks({api.cinder: ('volume_type_create',)})
    def test_create_volume_type(self):
        formData = {'name': 'volume type 1',
                    'vol_type_description': 'test desc',
                    'is_public': True}
        self.mock_volume_type_create.return_value = \
            self.cinder_volume_types.first()

        res = self.client.post(
            reverse('horizon:admin:volume_types:create_type'),
            formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_type_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            formData['vol_type_description'],
            formData['is_public'])

    @test.create_mocks({api.cinder: ('volume_type_get',
                                     'volume_type_update')})
    def _test_update_volume_type(self, is_public):
        volume_type = self.cinder_volume_types.first()
        formData = {'name': volume_type.name,
                    'description': 'test desc updated',
                    'is_public': is_public}
        self.mock_volume_type_get.return_value = volume_type
        self.mock_volume_type_update.return_value = volume_type

        url = reverse('horizon:admin:volume_types:update_type',
                      args=[volume_type.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        self.mock_volume_type_update.assert_called_once_with(
            test.IsHttpRequest(),
            volume_type.id,
            formData['name'],
            formData['description'],
            formData['is_public'])

    def test_update_volume_type_public_true(self):
        self._test_update_volume_type(True)

    def test_update_volume_type_public_false(self):
        self._test_update_volume_type(False)

    @test.create_mocks({api.cinder: ('volume_type_list_with_qos_associations',
                                     'qos_spec_list',
                                     'volume_type_delete',
                                     'volume_encryption_type_list')})
    def test_delete_volume_type(self):
        volume_type = self.cinder_volume_types.first()
        formData = {'action': 'volume_types__delete__%s' % volume_type.id}
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])

        self.mock_volume_type_list_with_qos_associations.return_value = \
            self.cinder_volume_types.list()
        self.mock_qos_spec_list.return_value = self.cinder_qos_specs.list()
        self.mock_volume_encryption_type_list.return_value = encryption_list
        self.mock_volume_type_delete.return_value = None

        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_type_list_with_qos_associations.\
            assert_called_once_with(test.IsHttpRequest())
        self.mock_qos_spec_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_encryption_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_delete.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)

    @test.create_mocks({api.cinder: ('volume_type_list_with_qos_associations',
                                     'qos_spec_list',
                                     'volume_type_delete',
                                     'volume_encryption_type_list')})
    def test_delete_volume_type_exception(self):
        volume_type = self.cinder_volume_types.first()
        formData = {'action': 'volume_types__delete__%s' % volume_type.id}
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])

        self.mock_volume_type_list_with_qos_associations.return_value = \
            self.cinder_volume_types.list()
        self.mock_qos_spec_list.return_value = self.cinder_qos_specs.list()
        self.mock_volume_encryption_type_list.return_value = encryption_list
        self.mock_volume_type_delete.side_effect = exceptions.BadRequest()

        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_type_list_with_qos_associations.\
            assert_called_once_with(test.IsHttpRequest())
        self.mock_qos_spec_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_encryption_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_delete.assert_called_once_with(
            test.IsHttpRequest(), str(volume_type.id))

    @test.create_mocks({api.cinder: ('volume_encryption_type_create',
                                     'volume_type_list',)})
    def test_create_volume_type_encryption(self):
        volume_type1 = self.cinder_volume_types.list()[0]
        volume_type2 = self.cinder_volume_types.list()[1]
        volume_type1.id = u'1'
        volume_type2.id = u'2'
        volume_type_list = [volume_type1, volume_type2]
        formData = {'name': u'An Encrypted Volume Type',
                    'provider': u'a-provider',
                    'control_location': u'front-end',
                    'cipher': u'a-cipher',
                    'key_size': 512,
                    'volume_type_id': volume_type1.id}

        self.mock_volume_type_list.return_value = volume_type_list
        self.mock_volume_encryption_type_create.return_value = None

        url = reverse('horizon:admin:volume_types:create_type_encryption',
                      args=[volume_type1.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(
            res,
            'admin/volume_types/create_volume_type_encryption.html')
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        expected = {
            'provider': u'a-provider',
            'control_location': u'front-end',
            'cipher': u'a-cipher',
            'key_size': 512,
        }
        self.mock_volume_encryption_type_create.assert_called_once_with(
            test.IsHttpRequest(),
            volume_type1.id,
            expected)

    @test.create_mocks({api.cinder: ('volume_encryption_type_get',
                                     'volume_type_list',)})
    def test_type_encryption_detail_view_unencrypted(self):
        volume_type1 = self.cinder_volume_types.list()[0]
        volume_type1.id = u'1'
        volume_type_list = [volume_type1]
        vol_unenc_type = self.cinder_volume_encryption_types.list()[2]

        self.mock_volume_encryption_type_get.return_value = vol_unenc_type
        self.mock_volume_type_list.return_value = volume_type_list

        url = reverse('horizon:admin:volume_types:type_encryption_detail',
                      args=[volume_type1.id])
        res = self.client.get(url)

        self.assertTemplateUsed(
            res,
            'admin/volume_types/volume_encryption_type_detail.html')

        self.assertContains(res,
                            "<h3>Volume Type is Unencrypted.</h3>", 1, 200)
        self.assertNoMessages()
        self.mock_volume_encryption_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type1.id)
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.cinder: ('volume_encryption_type_get',
                                     'volume_type_list',)})
    def test_type_encryption_detail_view_encrypted(self):
        volume_type = self.cinder_volume_types.first()
        volume_type.id = u'1'
        volume_type.name = "An Encrypted Volume Name"
        volume_type_list = [volume_type]
        vol_enc_type = self.cinder_volume_encryption_types.list()[0]

        self.mock_volume_encryption_type_get.return_value = vol_enc_type
        self.mock_volume_type_list.return_value = volume_type_list

        url = reverse('horizon:admin:volume_types:type_encryption_detail',
                      args=[volume_type.id])
        res = self.client.get(url)

        self.assertTemplateUsed(
            res,
            'admin/volume_types/volume_encryption_type_detail.html')

        self.assertContains(res, "<h3>Volume Type Encryption Overview</h3>", 1,
                            200)
        self.assertContains(res, "<dd>%s</dd>" % volume_type.name, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.control_location,
                            1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.key_size, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.provider, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % vol_enc_type.cipher, 1, 200)

        self.assertNoMessages()

        self.mock_volume_encryption_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.cinder: ('extension_supported',
                                     'volume_type_list_with_qos_associations',
                                     'qos_spec_list',
                                     'volume_encryption_type_list',
                                     'volume_encryption_type_delete',)})
    def test_delete_volume_type_encryption(self):
        volume_type = self.cinder_volume_types.first()
        volume_type.id = u'1'
        formData = {'action': 'volume_types__delete_encryption__%s' %
                    volume_type.id}
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])

        self.mock_extension_supported.return_value = True
        self.mock_volume_type_list_with_qos_associations.return_value = \
            self.cinder_volume_types.list()
        self.mock_qos_spec_list.return_value = self.cinder_qos_specs.list()
        self.mock_volume_encryption_type_list.return_value = encryption_list
        self.mock_volume_encryption_type_delete.return_value = None

        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'VolumeTypeEncryption')
        self.mock_volume_type_list_with_qos_associations.\
            assert_called_once_with(test.IsHttpRequest())
        self.mock_qos_spec_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_encryption_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_encryption_type_delete.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)

    @test.create_mocks({api.cinder: ('volume_encryption_type_update',
                                     'volume_encryption_type_get',
                                     'volume_type_list')})
    def test_update_volume_type_encryption(self):
        volume_type = self.cinder_volume_types.first()
        volume_type.id = u'1'
        volume_type_list = [volume_type]
        formData = {'name': u'An Encrypted Volume Type',
                    'provider': u'a-provider',
                    'control_location': u'front-end',
                    'cipher': u'a-cipher',
                    'key_size': 256,
                    'volume_type_id': volume_type.id}
        vol_enc_type = self.cinder_volume_encryption_types.list()[0]

        self.mock_volume_encryption_type_get.return_value = vol_enc_type
        self.mock_volume_type_list.return_value = volume_type_list
        self.mock_volume_encryption_type_update.return_value = None

        url = reverse('horizon:admin:volume_types:update_type_encryption',
                      args=[volume_type.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(
            res,
            'admin/volume_types/update_volume_type_encryption.html')

        self.mock_volume_encryption_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        expected = {
            'provider': u'a-provider',
            'control_location': u'front-end',
            'cipher': u'a-cipher',
            'key_size': 256,
        }
        self.mock_volume_encryption_type_update.assert_called_once_with(
            test.IsHttpRequest(),
            volume_type.id,
            expected)

    @test.create_mocks({api.cinder: ('volume_type_get',
                                     'volume_type_access_list',
                                     'volume_type_add_project_access',
                                     'volume_type_remove_project_access'),
                        api.keystone: ('tenant_list',)})
    def _test_edit_volume_type_access(self, exception=False):
        volume_type = self.cinder_volume_types.list()[2]
        volume_type.id = u'1'
        type_access = self.cinder_type_access.list()
        formData = {'member': [u'3'],
                    'volume_type_id': volume_type.id}

        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_volume_type_get.return_value = volume_type
        self.mock_volume_type_access_list.return_value = type_access
        self.mock_volume_type_add_project_access.return_value = None
        if exception:
            self.mock_volume_type_remove_project_access.side_effect = \
                exceptions.BadRequest()
        else:
            self.mock_volume_type_remove_project_access.return_value = None

        url = reverse('horizon:admin:volume_types:edit_access',
                      args=[volume_type.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        self.mock_volume_type_access_list.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        self.mock_volume_type_add_project_access.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id, u'3')
        self.mock_volume_type_remove_project_access.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id, u'1')

    def test_edit_volume_type_access(self):
        self._test_edit_volume_type_access()

    def test_edit_volume_type_access_exception(self):
        self._test_edit_volume_type_access(exception=True)
