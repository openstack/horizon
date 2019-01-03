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

import tempfile

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.utils import override_settings
from django.urls import reverse

import mock
import six

from horizon import tables as horizon_tables
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.images.images import forms
from openstack_dashboard.dashboards.project.images.images import tables


IMAGES_INDEX_URL = reverse('horizon:project:images:index')


class CreateImageFormTests(test.ResetImageAPIVersionMixin, test.TestCase):
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_no_location_or_file(self, mock_image_list):
        mock_image_list.side_effect = [
            [self.images.list(), False, False],
            [self.images.list(), False, False]
        ]

        image_calls = [
            mock.call(test.IsA(dict), filters={'disk_format': 'aki'}),
            mock.call(test.IsA(dict), filters={'disk_format': 'ari'})
        ]

        post = {
            'name': u'Ubuntu 11.10',
            'source_type': u'file',
            'description': u'Login with admin/admin',
            'disk_format': u'qcow2',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': 1}
        files = {}
        form = forms.CreateImageForm(post, files)

        self.assertFalse(form.is_valid())
        mock_image_list.assert_has_calls(image_calls)


class UpdateImageFormTests(test.ResetImageAPIVersionMixin, test.TestCase):
    def test_is_format_field_editable(self):
        form = forms.UpdateImageForm({})
        disk_format = form.fields['disk_format']
        self.assertFalse(disk_format.widget.attrs.get('readonly', False))

    @mock.patch.object(api.glance, 'image_get')
    def test_image_update(self, mock_image_get):
        image = self.images.first()
        mock_image_get.return_value = image

        url = reverse('horizon:project:images:images:update',
                      args=[image.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertEqual(res.context['image'].disk_format,
                         image.disk_format)
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               image.id)

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    @mock.patch.object(api.glance, 'image_get')
    @mock.patch.object(api.glance, 'image_update')
    def test_image_update_post_v1(self, mock_image_update, mock_image_get):
        image = self.images.first()
        data = {
            'name': u'Ubuntu 11.10',
            'image_id': str(image.id),
            'description': u'Login with admin/admin',
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img',
            'disk_format': u'qcow2',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': False,
            'protected': False,
            'method': 'UpdateImageForm'}

        mock_image_get.return_value = image
        mock_image_update.return_value = image

        url = reverse('horizon:project:images:images:update',
                      args=[image.id])
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               str(image.id))
        mock_image_update.assert_called_once_with(
            test.IsHttpRequest(),
            image.id,
            is_public=data['is_public'],
            protected=data['protected'],
            disk_format=data['disk_format'],
            container_format="bare",
            name=data['name'],
            min_ram=data['min_ram'],
            min_disk=data['min_disk'],
            properties={
                'description': data['description'],
                'architecture': data['architecture']})

    @mock.patch.object(api.glance, 'image_get')
    @mock.patch.object(api.glance, 'image_update')
    def test_image_update_post_v2(self, mock_image_update, mock_image_get):
        image = self.images.first()
        data = {
            'name': u'Ubuntu 11.10',
            'image_id': str(image.id),
            'description': u'Login with admin/admin',
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img',
            'disk_format': u'qcow2',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': False,
            'protected': False,
            'method': 'UpdateImageForm'}

        mock_image_get.return_value = image
        mock_image_update.return_value = image

        url = reverse('horizon:project:images:images:update',
                      args=[image.id])
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               str(image.id))
        mock_image_update.assert_called_once_with(
            test.IsHttpRequest(),
            image.id,
            visibility='private',
            protected=data['protected'],
            disk_format=data['disk_format'],
            container_format="bare",
            name=data['name'],
            min_ram=data['min_ram'],
            min_disk=data['min_disk'],
            description=data['description'],
            architecture=data['architecture'])


class ImageViewTests(test.ResetImageAPIVersionMixin, test.TestCase):
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_image_create_get(self, mock_image_list):
        mock_image_list.side_effect = [
            [self.images.list(), False, False],
            [self.images.list(), False, False]
        ]
        image_calls = [
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'aki'}),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'ari'})
        ]

        url = reverse('horizon:project:images:images:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/images/images/create.html')
        mock_image_list.assert_has_calls(image_calls)

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_image_create_post_copy_from_v1(self):
        data = {
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img',
            'is_copying': True}

        api_data = {'copy_from': data['image_url']}
        self._test_image_create(data, api_data)

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_image_create_post_location_v1(self):
        data = {
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img',
            'is_copying': False}

        api_data = {'location': data['image_url']}
        self._test_image_create(data, api_data)

    @override_settings(IMAGES_ALLOW_LOCATION=True)
    def test_image_create_post_location_v2(self):
        data = {
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img'}

        api_data = {'location': data['image_url']}
        self._test_image_create(data, api_data)

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_image_create_post_upload_v1(self):
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(b'123')
        temp_file.flush()
        temp_file.seek(0)

        data = {'source_type': u'file',
                'image_file': temp_file}

        api_data = {'data': test.IsA(InMemoryUploadedFile)}
        self._test_image_create(data, api_data)

    def test_image_create_post_upload_v2(self):
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(b'123')
        temp_file.flush()
        temp_file.seek(0)

        data = {'source_type': u'file',
                'image_file': temp_file}

        api_data = {'data': test.IsA(InMemoryUploadedFile)}
        self._test_image_create(data, api_data)

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_image_create_post_with_kernel_ramdisk_v1(self):
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(b'123')
        temp_file.flush()
        temp_file.seek(0)

        data = {
            'source_type': u'file',
            'image_file': temp_file,
            'kernel_id': '007e7d55-fe1e-4c5c-bf08-44b4a496482e',
            'ramdisk_id': '007e7d55-fe1e-4c5c-bf08-44b4a496482a'
        }

        api_data = {'data': test.IsA(InMemoryUploadedFile)}
        self._test_image_create(data, api_data)

    def test_image_create_post_with_kernel_ramdisk_v2(self):
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(b'123')
        temp_file.flush()
        temp_file.seek(0)

        data = {
            'source_type': u'file',
            'image_file': temp_file,
            'kernel_id': '007e7d55-fe1e-4c5c-bf08-44b4a496482e',
            'ramdisk_id': '007e7d55-fe1e-4c5c-bf08-44b4a496482a'
        }

        api_data = {'data': test.IsA(InMemoryUploadedFile)}
        self._test_image_create(data, api_data)

    @mock.patch.object(api.glance, 'image_create')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def _test_image_create(self, extra_form_data, extra_api_data,
                           mock_image_list, mock_image_create):
        data = {
            'name': u'Ubuntu 11.10',
            'description': u'Login with admin/admin',
            'disk_format': u'qcow2',
            'architecture': u'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': True,
            'protected': False,
            'method': 'CreateImageForm'}
        data.update(extra_form_data)

        api_data = {'container_format': 'bare',
                    'disk_format': data['disk_format'],
                    'protected': False,
                    'min_disk': data['min_disk'],
                    'min_ram': data['min_ram'],
                    'name': data['name']}
        if api.glance.VERSIONS.active < 2:
            api_data.update({'is_public': True,
                             'properties': {
                                 'description': data['description'],
                                 'architecture': data['architecture']}
                             })
        else:
            api_data.update({'visibility': 'public',
                             'description': data['description'],
                             'architecture': data['architecture']
                             })

        api_data.update(extra_api_data)

        mock_image_list.side_effect = [
            [self.images.list(), False, False],
            [self.images.list(), False, False]
        ]
        image_list_calls = [
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'aki'}),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'ari'})
        ]

        mock_image_create.return_value = self.images.first()

        url = reverse('horizon:project:images:images:create')
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)

        mock_image_list.assert_has_calls(image_list_calls)
        mock_image_create.assert_called_once_with(test.IsHttpRequest(),
                                                  **api_data)

    @mock.patch.object(api.glance, 'image_get')
    def _test_image_detail_get(self, image, mock_image_get):
        mock_image_get.return_value = image

        res = self.client.get(reverse('horizon:project:images:images:detail',
                                      args=[image.id]))

        self.assertTemplateUsed(res,
                                'horizon/common/_detail.html')
        self.assertEqual(res.context['image'].name, image.name)
        self.assertEqual(res.context['image'].protected, image.protected)
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               six.text_type(image.id))

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_image_detail_get_v1(self):
        image = self.images.first()

        self._test_image_detail_get(image)

    def test_image_detail_get_v2(self):
        image = self.imagesV2.first()

        self._test_image_detail_get(image)

    @mock.patch.object(api.glance, 'image_get')
    def _test_image_detail_custom_props_get(self, image, mock_image_get):
        mock_image_get.return_value = image

        res = self.client.get(reverse('horizon:project:images:images:detail',
                                      args=[image.id]))

        image_props = res.context['image_props']

        # Test description property not displayed
        image_keys = [prop[0] for prop in image_props]
        self.assertNotIn(('description'), image_keys)

        # Test custom properties are sorted
        self.assertLess(image_props.index(('bar', 'bar', 'bar val')),
                        image_props.index(('foo', 'foo', 'foo val')))

        # Test all custom properties appear in template
        self.assertContains(res, '<dt title="bar">bar</dt>')
        self.assertContains(res, '<dd>bar val</dd>')
        self.assertContains(res, '<dt title="foo">foo</dt>')
        self.assertContains(res, '<dd>foo val</dd>')

        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               six.text_type(image.id))

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_image_detail_custom_props_get_v1(self):
        image = self.images.list()[9]

        self._test_image_detail_custom_props_get(image)

    def test_image_detail_custom_props_get_v2(self):
        image = self.imagesV2.list()[2]

        self._test_image_detail_custom_props_get(image)

    @mock.patch.object(api.glance, 'image_get')
    def _test_protected_image_detail_get(self, image, mock_image_get):
        mock_image_get.return_value = image

        res = self.client.get(
            reverse('horizon:project:images:images:detail',
                    args=[image.id]))
        self.assertTemplateUsed(res,
                                'horizon/common/_detail.html')
        self.assertEqual(res.context['image'].protected, image.protected)

        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               six.text_type(image.id))

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_protected_image_detail_get_v1(self):
        image = self.images.list()[2]

        self._test_protected_image_detail_get(image)

    def test_protected_image_detail_get_v2(self):
        image = self.imagesV2.list()[1]

        self._test_protected_image_detail_get(image)

    @mock.patch.object(api.glance, 'image_get')
    def test_image_detail_get_with_exception(self, mock_image_get):
        image = self.images.first()

        mock_image_get.side_effect = self.exceptions.glance

        url = reverse('horizon:project:images:images:detail',
                      args=[image.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, IMAGES_INDEX_URL)
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               six.text_type(image.id))

    @mock.patch.object(api.glance, 'image_get')
    def test_image_update_get(self, mock_image_get):
        image = self.images.filter(is_public=True)[0]
        mock_image_get.return_value = image

        res = self.client.get(
            reverse('horizon:project:images:images:update',
                    args=[image.id]))

        self.assertTemplateUsed(res,
                                'project/images/images/_update.html')
        self.assertEqual(res.context['image'].name, image.name)
        # Bug 1076216 - is_public checkbox not being set correctly
        self.assertContains(res, "<input type='checkbox' id='id_is_public'"
                                 " name='is_public' checked='checked'>",
                            html=True,
                            msg_prefix="The is_public checkbox is not checked")
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               six.text_type(image.id))


class OwnerFilterTests(test.TestCase):
    def setUp(self):
        super(OwnerFilterTests, self).setUp()
        self.table = mock.Mock(spec=horizon_tables.DataTable)
        self.table.request = self.request

    @override_settings(IMAGES_LIST_FILTER_TENANTS=[{'name': 'Official',
                                                    'tenant': 'officialtenant',
                                                    'icon': 'fa-check'}])
    def test_filter(self):
        all_images = self.images.list()
        table = self.table
        self.filter_tenants = settings.IMAGES_LIST_FILTER_TENANTS

        filter_ = tables.OwnerFilter()

        images = filter_.filter(table, all_images, 'project')
        self.assertEqual(images, self._expected('project'))

        images = filter_.filter(table, all_images, 'public')
        self.assertEqual(images, self._expected('public'))

        images = filter_.filter(table, all_images, 'shared')
        self.assertEqual(images, self._expected('shared'))

        images = filter_.filter(table, all_images, 'officialtenant')
        self.assertEqual(images, self._expected('officialtenant'))

    def _expected(self, filter_string):
        my_tenant_id = self.request.user.tenant_id
        images = self.images.list()
        special = map(lambda t: t['tenant'], self.filter_tenants)

        if filter_string == 'public':
            return [im for im in images if im.is_public]
        if filter_string == 'shared':
            return [im for im in images
                    if (not im.is_public and
                        im.owner != my_tenant_id and
                        im.owner not in special)]
        if filter_string == 'project':
            filter_string = my_tenant_id
        return [im for im in images if im.owner == filter_string]
