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
from django.core.files.uploadedfile import InMemoryUploadedFile  # noqa
from django.core.urlresolvers import reverse
from django.forms.widgets import HiddenInput  # noqa
from django import http
from django.test.utils import override_settings

from mox import IsA  # noqa

from horizon import tables as horizon_tables
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.images.images import forms
from openstack_dashboard.dashboards.project.images.images import tables


IMAGES_INDEX_URL = reverse('horizon:project:images:index')


class CreateImageFormTests(test.TestCase):
    def test_no_location_or_file(self):
        """The form will not be valid if both image_url and image_file are not
        provided.
        """
        post = {
            'name': u'Ubuntu 11.10',
            'source_type': u'file',
            'description': u'Login with admin/admin',
            'disk_format': u'qcow2',
            'architecture': u'x86-64',
            'minimum_disk': 15,
            'minimum_ram': 512,
            'is_public': 1}
        files = {}
        form = forms.CreateImageForm(post, files)
        self.assertEqual(form.is_valid(), False)

    @override_settings(HORIZON_IMAGES_ALLOW_UPLOAD=False)
    def test_image_upload_disabled(self):
        """If HORIZON_IMAGES_ALLOW_UPLOAD is false, the image_file field widget
        will be a HiddenInput widget instead of a FileInput widget.
        """
        form = forms.CreateImageForm({})
        self.assertEqual(
            isinstance(form.fields['image_file'].widget, HiddenInput), True)
        source_type_dict = dict(form.fields['source_type'].choices)
        self.assertNotIn('file', source_type_dict)


class UpdateImageFormTests(test.TestCase):
    def test_is_format_field_editable(self):
        form = forms.UpdateImageForm({})
        disk_format = form.fields['disk_format']
        self.assertFalse(disk_format.widget.attrs.get('readonly', False))

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_update(self):
        image = self.images.first()
        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
           .AndReturn(image)
        self.mox.ReplayAll()

        url = reverse('horizon:project:images:images:update',
                      args=[image.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertEqual(res.context['image'].disk_format,
                         image.disk_format)

    @test.create_stubs({api.glance: ('image_update', 'image_get')})
    def test_image_update_post(self):
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
            'minimum_disk': 15,
            'minimum_ram': 512,
            'is_public': False,
            'protected': False,
            'method': 'UpdateImageForm'}
        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
           .AndReturn(image)
        api.glance.image_update(IsA(http.HttpRequest),
                                image.id,
                                is_public=data['is_public'],
                                protected=data['protected'],
                                disk_format=data['disk_format'],
                                container_format="bare",
                                name=data['name'],
                                min_ram=data['minimum_ram'],
                                min_disk=data['minimum_disk'],
                                properties={'description': data['description'],
                                            'architecture':
                                            data['architecture']},
                                purge_props=False).AndReturn(image)
        self.mox.ReplayAll()
        url = reverse('horizon:project:images:images:update',
                      args=[image.id])
        res = self.client.post(url, data)
        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)


class ImageViewTests(test.TestCase):
    def test_image_create_get(self):
        url = reverse('horizon:project:images:images:create')
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'project/images/images/create.html')

    @test.create_stubs({api.glance: ('image_create',)})
    def test_image_create_post_copy_from(self):
        data = {
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img',
            'is_copying': True}

        api_data = {'copy_from': data['image_url']}
        self._test_image_create(data, api_data)

    @test.create_stubs({api.glance: ('image_create',)})
    def test_image_create_post_location(self):
        data = {
            'source_type': u'url',
            'image_url': u'http://cloud-images.ubuntu.com/releases/'
                         u'oneiric/release/ubuntu-11.10-server-cloudimg'
                         u'-amd64-disk1.img',
            'is_copying': False}

        api_data = {'location': data['image_url']}
        self._test_image_create(data, api_data)

    @test.create_stubs({api.glance: ('image_create',)})
    def test_image_create_post_upload(self):
        temp_file = tempfile.TemporaryFile()
        temp_file.write('123')
        temp_file.flush()
        temp_file.seek(0)

        data = {'source_type': u'file',
                'image_file': temp_file}

        api_data = {'data': IsA(InMemoryUploadedFile)}
        self._test_image_create(data, api_data)

    def _test_image_create(self, extra_form_data, extra_api_data):
        data = {
            'name': u'Ubuntu 11.10',
            'description': u'Login with admin/admin',
            'disk_format': u'qcow2',
            'architecture': u'x86-64',
            'minimum_disk': 15,
            'minimum_ram': 512,
            'is_public': True,
            'protected': False,
            'method': 'CreateImageForm'}
        data.update(extra_form_data)

        api_data = {'container_format': 'bare',
                    'disk_format': data['disk_format'],
                    'is_public': True,
                    'protected': False,
                    'min_disk': data['minimum_disk'],
                    'min_ram': data['minimum_ram'],
                    'properties': {
                        'description': data['description'],
                        'architecture': data['architecture']},
                    'name': data['name']}
        api_data.update(extra_api_data)

        api.glance.image_create(
            IsA(http.HttpRequest),
            **api_data).AndReturn(self.images.first())
        self.mox.ReplayAll()

        url = reverse('horizon:project:images:images:create')
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_detail_get(self):
        image = self.images.first()

        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
            .AndReturn(self.images.first())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:images:images:detail',
                                      args=[image.id]))

        self.assertTemplateUsed(res,
                                'project/images/images/detail.html')
        self.assertEqual(res.context['image'].name, image.name)
        self.assertEqual(res.context['image'].protected, image.protected)
        self.assertContains(res, "<h1>Image Details: %s</h1>" % image.name,
                            1, 200)

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_detail_custom_props_get(self):
        image = self.images.list()[8]

        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
            .AndReturn(image)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:images:images:detail',
                                      args=[image.id]))

        image_props = res.context['image_props']

        # Test description property not displayed
        image_keys = [prop[0] for prop in image_props]
        self.assertNotIn(('description'), image_keys)

        # Test custom properties are sorted
        self.assertEqual(image_props[0], ('bar', 'bar', 'bar val'))
        self.assertEqual(image_props[1], ('foo', 'foo', 'foo val'))

        # Test all custom properties appear in template
        self.assertContains(res, '<dt title="bar">bar</dt>')
        self.assertContains(res, '<dd>bar val</dd>')
        self.assertContains(res, '<dt title="foo">foo</dt>')
        self.assertContains(res, '<dd>foo val</dd>')

    @test.create_stubs({api.glance: ('image_get',)})
    def test_protected_image_detail_get(self):
        image = self.images.list()[2]

        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
            .AndReturn(image)
        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:project:images:images:detail',
                    args=[image.id]))
        self.assertTemplateUsed(res,
                                'project/images/images/detail.html')
        self.assertEqual(res.context['image'].protected, image.protected)

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_detail_get_with_exception(self):
        image = self.images.first()

        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
            .AndRaise(self.exceptions.glance)
        self.mox.ReplayAll()

        url = reverse('horizon:project:images:images:detail',
                      args=[image.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, IMAGES_INDEX_URL)

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_update_get(self):
        image = self.images.first()
        image.disk_format = "ami"
        image.is_public = True
        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
           .AndReturn(image)
        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:project:images:images:update',
                    args=[image.id]))

        self.assertTemplateUsed(res,
                                'project/images/images/_update.html')
        self.assertEqual(res.context['image'].name, image.name)
        # Bug 1076216 - is_public checkbox not being set correctly
        self.assertContains(res, "<input type='checkbox' id='id_public'"
                                 " name='public' checked='checked'>",
                            html=True,
                            msg_prefix="The is_public checkbox is not checked")


class OwnerFilterTests(test.TestCase):
    def setUp(self):
        super(OwnerFilterTests, self).setUp()
        self.table = self.mox.CreateMock(horizon_tables.DataTable)
        self.table.request = self.request

    @override_settings(IMAGES_LIST_FILTER_TENANTS=[{'name': 'Official',
                                                    'tenant': 'officialtenant',
                                                    'icon': 'fa-check'}])
    def test_filter(self):
        self.mox.ReplayAll()
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
            return filter(lambda im: im.is_public, images)
        if filter_string == 'shared':
            return filter(lambda im: (not im.is_public and
                                      im.owner != my_tenant_id and
                                      im.owner not in special),
                          images)
        if filter_string == 'project':
            filter_string = my_tenant_id
        return filter(lambda im: im.owner == filter_string, images)
