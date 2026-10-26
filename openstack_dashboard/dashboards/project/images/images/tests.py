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
from unittest import mock

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.utils import override_settings
from django.urls import reverse

from horizon import tables as horizon_tables
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.images.images import forms
from openstack_dashboard.dashboards.project.images.images import tables


IMAGES_INDEX_URL = reverse('horizon:project:images:index')


class CreateImageFormTests(test.ResetImageAPIVersionMixin, test.TestCase):
    @mock.patch.object(api.glance, 'get_image_formats')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_no_location_or_file(self, mock_image_list, mock_schemas_list):
        mock_image_list.side_effect = [
            [self.images.list(), False, False],
            [self.images.list(), False, False]
        ]

        image_calls = [
            mock.call(test.IsA(dict), filters={'disk_format': 'aki'}),
            mock.call(test.IsA(dict), filters={'disk_format': 'ari'})
        ]

        post = {
            'name': 'Ubuntu 11.10',
            'source_type': 'file',
            'description': 'Login with admin/admin',
            'disk_format': 'qcow2',
            'architecture': 'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': 1}
        files = {}
        form = forms.CreateImageForm(post, files)

        self.assertFalse(form.is_valid())
        mock_image_list.assert_has_calls(image_calls)


class UpdateImageFormTests(test.ResetImageAPIVersionMixin, test.TestCase):
    @mock.patch.object(api.glance, 'image_list_detailed',
                       return_value=[[], False, False])
    def test_is_format_field_editable(self, mock_image_list):
        form = forms.UpdateImageForm(self.request)
        disk_format = form.fields['disk_format']
        self.assertFalse(disk_format.widget.attrs.get('readonly', False))

    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_kernel_ramdisk_choices_preserve_initial_values(self,
                                                            mock_image_list):
        kernel = mock.Mock(id='kernel-b', name='kernel-b', size=1024)
        ramdisk = mock.Mock(id='ramdisk-b', name='ramdisk-b', size=1024)
        mock_image_list.side_effect = [
            [[kernel], False, False],
            [[ramdisk], False, False],
        ]

        current_kernel = 'kernel-a'
        current_ramdisk = 'ramdisk-a'
        form = forms.UpdateImageForm(
            self.request,
            initial={'kernel': current_kernel, 'ramdisk': current_ramdisk})

        self.assertEqual(form.initial['kernel'], current_kernel)
        self.assertEqual(form.initial['ramdisk'], current_ramdisk)
        kernel_choices = [
            choice[0] for choice in form.fields['kernel'].choices]
        ramdisk_choices = [
            choice[0] for choice in form.fields['ramdisk'].choices]
        self.assertIn(current_kernel, kernel_choices)
        self.assertIn(kernel.id, kernel_choices)
        self.assertIn(current_ramdisk, ramdisk_choices)
        self.assertIn(ramdisk.id, ramdisk_choices)

    @mock.patch.object(api.glance, 'image_list_detailed',
                       return_value=[[], False, False])
    def test_empty_choice_lookup_preserves_current_associations(
            self, mock_image_list):
        form = forms.UpdateImageForm(
            self.request,
            initial={'kernel': 'kernel-a', 'ramdisk': 'ramdisk-a'})

        self.assertEqual(form.fields['kernel'].choices,
                         [('kernel-a', 'kernel-a')])
        self.assertEqual(form.fields['ramdisk'].choices,
                         [('ramdisk-a', 'ramdisk-a')])
        self.assertEqual(form.fields['kernel'].clean('kernel-a'), 'kernel-a')
        self.assertEqual(form.fields['ramdisk'].clean('ramdisk-a'),
                         'ramdisk-a')
        self.assertTrue(form.fields['kernel'].widget.attrs['readonly'])
        self.assertTrue(form.fields['ramdisk'].widget.attrs['readonly'])
        self.assertEqual(mock_image_list.call_count, 2)

    @mock.patch.object(api.glance, 'image_list_detailed')
    @mock.patch.object(forms.messages, 'error')
    def test_glance_choice_lookup_error_uses_readonly_fallback(
            self, mock_error, mock_image_list):
        mock_image_list.side_effect = Exception('Glance unavailable')

        form = forms.UpdateImageForm(self.request)

        self.assertTrue(form.fields['kernel'].widget.attrs['readonly'])
        self.assertTrue(form.fields['ramdisk'].widget.attrs['readonly'])
        self.assertEqual(mock_error.call_count, 2)
        for call in mock_error.call_args_list:
            self.assertIs(call.args[0], self.request)

    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_invalid_kernel_choice_is_rejected(self, mock_image_list):
        mock_image_list.side_effect = [
            [[], False, False],
            [[], False, False],
        ]
        form = forms.UpdateImageForm(self.request)
        form.fields['kernel'].choices = [
            ('', 'Choose an image'), ('valid', 'valid')]

        with self.assertRaises(ValidationError):
            form.fields['kernel'].clean('not-valid')

    @mock.patch.object(api.glance, 'image_get')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_image_update(self, mock_image_list, mock_image_get):
        image = self.images.first()
        mock_image_get.return_value = image
        mock_image_list.side_effect = [
            [self.images.list(), False, False],
            [self.images.list(), False, False],
        ]

        url = reverse('horizon:project:images:images:update',
                      args=[image.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertEqual(res.context['image'].disk_format,
                         image.disk_format)
        mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                               image.id)

    @mock.patch.object(api.glance, 'image_get')
    @mock.patch.object(api.glance, 'image_update_properties')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_image_update_post_v2(self, mock_image_list,
                                  mock_image_update, mock_image_get):
        image = self.images.first()
        data = {
            'name': 'Ubuntu 11.10',
            'image_id': str(image.id),
            'description': 'Login with admin/admin',
            'source_type': 'url',
            'image_url': 'http://cloud-images.ubuntu.com/releases/'
                         'oneiric/release/ubuntu-11.10-server-cloudimg'
                         '-amd64-disk1.img',
            'disk_format': 'qcow2',
            'architecture': 'x86-64',
            'min_disk': 15,
            'min_ram': 512,
            'is_public': False,
            'protected': False,
            'kernel': 'kernel-id',
            'ramdisk': 'ramdisk-id',
            'method': 'UpdateImageForm'}

        mock_image_get.return_value = image
        mock_image_update.return_value = image
        kernel = mock.Mock(id=data['kernel'], size=1024)
        ramdisk = mock.Mock(id=data['ramdisk'], size=1024)
        mock_image_list.side_effect = [
            [[kernel], False, False],
            [[ramdisk], False, False],
        ]

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
            remove_props=[],
            visibility='private',
            protected=data['protected'],
            disk_format=data['disk_format'],
            container_format="bare",
            name=data['name'],
            min_ram=data['min_ram'],
            min_disk=data['min_disk'],
            description=data['description'],
            architecture=data['architecture'],
            kernel_id=data['kernel'],
            ramdisk_id=data['ramdisk'])

    @mock.patch.object(api.glance, 'image_update_properties')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_image_update_clears_empty_associations(self, mock_image_list,
                                                    mock_image_update):
        mock_image_list.side_effect = [
            [[], False, False],
            [[], False, False],
        ]
        mock_image_update.return_value = self.images.first()
        request = self.request
        form = forms.UpdateImageForm(request)

        with mock.patch.object(forms.messages, 'success'):
            form.handle(request, {
                'image_id': 'image-id',
                'kernel': '',
                'ramdisk': '',
            })

        _, kwargs = mock_image_update.call_args
        self.assertEqual(kwargs['remove_props'], ['kernel_id', 'ramdisk_id'])


class ImageViewTests(test.ResetImageAPIVersionMixin, test.TestCase):
    @mock.patch.object(api.glance, 'get_image_schemas')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_image_create_get(self, mock_image_list, mock_schemas_list):
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

    @override_settings(IMAGES_ALLOW_LOCATION=True)
    @mock.patch.object(api.glance, 'get_image_schemas')
    def test_image_create_post_location_v2(self, mock_schemas_list):
        mock_schemas_list.return_value = self.image_schemas.first()
        data = {
            'source_type': 'url',
            'image_url': 'http://cloud-images.ubuntu.com/releases/'
                         'oneiric/release/ubuntu-11.10-server-cloudimg'
                         '-amd64-disk1.img'}

        api_data = {'location': data['image_url']}
        self._test_image_create(data, api_data)

    @mock.patch.object(api.glance, 'get_image_schemas')
    def test_image_create_post_upload_v2(self, mock_schemas_list):
        mock_schemas_list.return_value = self.image_schemas.first()
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(b'123')
        temp_file.flush()
        temp_file.seek(0)

        data = {'source_type': 'file',
                'image_file': temp_file}

        api_data = {'data': test.IsA(InMemoryUploadedFile)}
        self._test_image_create(data, api_data)

    @mock.patch.object(api.glance, 'get_image_schemas')
    def test_image_create_post_with_kernel_ramdisk_v2(self, mock_schemas_list):
        mock_schemas_list.return_value = self.image_schemas.first()
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(b'123')
        temp_file.flush()
        temp_file.seek(0)

        data = {
            'source_type': 'file',
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
            'name': 'Ubuntu 11.10',
            'description': 'Login with admin/admin',
            'disk_format': 'qcow2',
            'architecture': 'x86-64',
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
        mock_image_get.assert_called_once_with(test.IsHttpRequest(), image.id)

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
        self.assertContains(res, '<dd class="word-wrap">bar val</dd>')
        self.assertContains(res, '<dt title="foo">foo</dt>')
        self.assertContains(res, '<dd class="word-wrap">foo val</dd>')

        mock_image_get.assert_called_once_with(test.IsHttpRequest(), image.id)

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
                                               image.id)

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
        mock_image_get.assert_called_once_with(test.IsHttpRequest(), image.id)

    @mock.patch.object(api.glance, 'image_get')
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_image_update_get(self, mock_image_list, mock_image_get):
        image = self.images.filter(is_public=True)[0]
        mock_image_get.return_value = image
        mock_image_list.side_effect = [
            [self.images.list(), False, False],
            [self.images.list(), False, False],
        ]

        res = self.client.get(
            reverse('horizon:project:images:images:update',
                    args=[image.id]))

        self.assertTemplateUsed(res,
                                'project/images/images/_update.html')
        self.assertEqual(res.context['image'].name, image.name)
        self.assertEqual(res.context['form'].initial['kernel'], image.kernel_id)
        self.assertEqual(
            res.context['form'].initial['ramdisk'], image.ramdisk_id)
        # Bug 1076216 - is_public checkbox not being set correctly
        self.assertContains(res, "<input type='checkbox' id='id_is_public'"
                                 " name='is_public' checked='checked'>",
                            html=True,
                            msg_prefix="The is_public checkbox is not checked")
        mock_image_get.assert_called_once_with(test.IsHttpRequest(), image.id)


class ImageFilterActionTests(test.TestCase):
    def test_filter_action_in_table_actions(self):
        self.assertIn(tables.ImageFilterAction,
                      tables.ImagesTable._meta.table_actions)

    def test_filter_action_is_server_side(self):
        action = tables.ImageFilterAction()
        self.assertEqual(action.filter_type, 'server')

    def test_filter_choices_include_name_status_format(self):
        action = tables.ImageFilterAction()
        choice_fields = [c[0] for c in action.filter_choices]
        self.assertIn('name', choice_fields)
        self.assertIn('status', choice_fields)
        self.assertIn('disk_format', choice_fields)
        self.assertIn('visibility', choice_fields)
        self.assertIn('owner', choice_fields)

    def test_owner_filter_not_in_table_actions(self):
        """OwnerFilter replaced by ImageFilterAction; class still exists."""
        self.assertNotIn(tables.OwnerFilter,
                         tables.ImagesTable._meta.table_actions)


class ImageDisplayLabelTests(test.TestCase):
    def test_visibility_label_uses_api_value_mapping(self):
        expected_labels = {
            'public': 'Public',
            'private': 'Private',
            'shared': 'Shared',
            'community': 'Community',
        }

        for visibility, expected in expected_labels.items():
            image = mock.Mock(visibility=visibility)
            self.assertEqual(
                str(tables.get_visibility_label(image)), expected)

    def test_unknown_visibility_is_preserved(self):
        image = mock.Mock(visibility='future-value')

        self.assertEqual(tables.get_visibility_label(image), 'future-value')

    def test_protected_label_uses_boolean_filter(self):
        protected = mock.Mock(protected=True)
        unprotected = mock.Mock(protected=False)

        self.assertEqual(tables.get_protected_label(protected), 'Yes')
        self.assertEqual(tables.get_protected_label(unprotected), 'No')


class OwnerFilterTests(test.TestCase):
    def setUp(self):
        super().setUp()
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
