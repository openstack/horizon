# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import http
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse
from django.forms.widgets import HiddenInput
from django.test.utils import override_settings

from mox import IsA

from horizon import tables as horizon_tables
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from . import tables
from .forms import CreateImageForm


IMAGES_INDEX_URL = reverse('horizon:project:images_and_snapshots:index')


class CreateImageFormTests(test.TestCase):
    def test_no_location_or_file(self):
        """
        The form will not be valid if both copy_from and image_file are not
        provided.
        """
        post = {
            'name': u'Ubuntu 11.10',
            'disk_format': u'qcow2',
            'minimum_disk': 15,
            'minimum_ram': 512,
            'is_public': 1}
        files = {}
        form = CreateImageForm(post, files)
        self.assertEqual(form.is_valid(), False)

    @override_settings(HORIZON_IMAGES_ALLOW_UPLOAD=False)
    def test_image_upload_disabled(self):
        """
        If HORIZON_IMAGES_ALLOW_UPLOAD is false, the image_file field widget
        will be a HiddenInput widget instead of a FileInput widget.
        """
        form = CreateImageForm({})
        self.assertEqual(
            isinstance(form.fields['image_file'].widget, HiddenInput), True)


class ImageViewTests(test.TestCase):
    def test_image_create_get(self):
        url = reverse('horizon:project:images_and_snapshots:images:create')
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                            'project/images_and_snapshots/images/create.html')

    @test.create_stubs({api.glance: ('image_create',)})
    def test_image_create_post_copy_from(self):
        data = {
            'name': u'Ubuntu 11.10',
            'copy_from': u'http://cloud-images.ubuntu.com/releases/'
                        u'oneiric/release/ubuntu-11.10-server-cloudimg'
                        u'-amd64-disk1.img',
            'disk_format': u'qcow2',
            'minimum_disk': 15,
            'minimum_ram': 512,
            'is_public': 1,
            'method': 'CreateImageForm'}

        api.glance.image_create(IsA(http.HttpRequest),
                                container_format="bare",
                                copy_from=data['copy_from'],
                                disk_format=data['disk_format'],
                                is_public=True,
                                min_disk=data['minimum_disk'],
                                min_ram=data['minimum_ram'],
                                name=data['name']). \
                        AndReturn(self.images.first())
        self.mox.ReplayAll()

        url = reverse('horizon:project:images_and_snapshots:images:create')
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)

    @test.create_stubs({api.glance: ('image_create',)})
    def test_image_create_post_upload(self):
        temp_file = tempfile.TemporaryFile()
        temp_file.write('123')
        temp_file.flush()
        temp_file.seek(0)
        data = {
            'name': u'Test Image',
            'image_file': temp_file,
            'disk_format': u'qcow2',
            'minimum_disk': 15,
            'minimum_ram': 512,
            'is_public': 1,
            'method': 'CreateImageForm'}

        api.glance.image_create(IsA(http.HttpRequest),
                                container_format="bare",
                                disk_format=data['disk_format'],
                                is_public=True,
                                min_disk=data['minimum_disk'],
                                min_ram=data['minimum_ram'],
                                name=data['name'],
                                data=IsA(InMemoryUploadedFile)). \
                        AndReturn(self.images.first())
        self.mox.ReplayAll()

        url = reverse('horizon:project:images_and_snapshots:images:create')
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 302)

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_detail_get(self):
        image = self.images.first()

        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
                                 .AndReturn(self.images.first())
        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:project:images_and_snapshots:images:detail',
                args=[image.id]))
        self.assertTemplateUsed(res,
                            'project/images_and_snapshots/images/detail.html')
        self.assertEqual(res.context['image'].name, image.name)

    @test.create_stubs({api.glance: ('image_get',)})
    def test_image_detail_get_with_exception(self):
        image = self.images.first()

        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
                  .AndRaise(self.exceptions.glance)
        self.mox.ReplayAll()

        url = reverse('horizon:project:images_and_snapshots:images:detail',
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
            reverse('horizon:project:images_and_snapshots:images:update',
                    args=[image.id]))

        self.assertTemplateUsed(res,
                            'project/images_and_snapshots/images/_update.html')
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
                                                    'icon': 'icon-ok'}])
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
            return filter(lambda im: not im.is_public and
                                     im.owner != my_tenant_id and
                                     im.owner not in special, images)
        if filter_string == 'project':
            filter_string = my_tenant_id
        return filter(lambda im: im.owner == filter_string, images)
