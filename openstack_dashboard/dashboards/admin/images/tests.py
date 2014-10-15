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

import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.images import tables

IMAGE_METADATA_URL = reverse('horizon:admin:images:update_metadata',
                             kwargs={
                                 "id": "007e7d55-fe1e-4c5c-bf08-44b4a4964822"})


class ImageCreateViewTest(test.BaseAdminViewTests):
    def test_admin_image_create_view_uses_admin_template(self):
        res = self.client.get(
            reverse('horizon:admin:images:create'))
        self.assertTemplateUsed(res, 'admin/images/create.html')


class ImagesViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_images_list(self):
        filters = {'is_public': None}
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([self.images.list(),
                        False, False])
        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:admin:images:index'))
        self.assertTemplateUsed(res, 'admin/images/index.html')
        self.assertEqual(len(res.context['images_table'].data),
                         len(self.images.list()))

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_images_list_get_pagination(self):
        images = self.images.list()[:5]
        filters = {'is_public': None}
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images, True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images[:2], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images[2:4], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[4].id,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images[4:], True, True])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(images))
        self.assertTemplateUsed(res, 'admin/images/index.html')

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # get second page (items 2-4)
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[4].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # get third page (item 5)
        self.assertEqual(len(res.context['images_table'].data),
                         1)

    @test.create_stubs({api.glance: ('image_get',
                                     'metadefs_namespace_list',
                                     'metadefs_namespace_get')})
    def test_images_metadata_get(self):
        image = self.images.first()

        api.glance.image_get(
            IsA(http.HttpRequest),
            image.id
        ).AndReturn(image)

        namespaces = self.metadata_defs.list()

        api.glance.metadefs_namespace_list(IsA(http.HttpRequest), filters={
            'resource_types': ['OS::Glance::Image']}).AndReturn(
                (namespaces, False, False))

        for namespace in namespaces:
            api.glance.metadefs_namespace_get(
                IsA(http.HttpRequest),
                namespace.namespace,
                'OS::Glance::Image'
            ).AndReturn(namespace)

        self.mox.ReplayAll()
        res = self.client.get(IMAGE_METADATA_URL)

        self.assertTemplateUsed(res, 'admin/images/update_metadata.html')
        self.assertContains(res, 'namespace_1')
        self.assertContains(res, 'namespace_2')
        self.assertContains(res, 'namespace_3')
        self.assertContains(res, 'namespace_4')

    @test.create_stubs({api.glance: ('image_get', 'image_update_properties')})
    def test_images_metadata_update(self):
        image = self.images.first()

        api.glance.image_get(
            IsA(http.HttpRequest),
            image.id
        ).AndReturn(image)
        api.glance.image_update_properties(
            IsA(http.HttpRequest), image.id, ['image_type'],
            hw_machine_type='mock_value').AndReturn(None)

        self.mox.ReplayAll()

        metadata = [{"value": "mock_value", "key": "hw_machine_type"}]
        formData = {"metadata": json.dumps(metadata)}

        res = self.client.post(IMAGE_METADATA_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(
            res, reverse('horizon:admin:images:index')
        )

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_images_list_get_prev_pagination(self):
        images = self.images.list()[:3]
        filters = {'is_public': None}
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images, True, False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images[:2], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='desc') \
            .AndReturn([images[2:], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='asc') \
            .AndReturn([images[:2], True, True])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(images))
        self.assertTemplateUsed(res, 'admin/images/index.html')

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # get second page (item 3)
        self.assertEqual(len(res.context['images_table'].data), 1)

        params = "=".join([tables.AdminImagesTable._meta.prev_pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # prev back to get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)
