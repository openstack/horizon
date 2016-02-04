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

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.images import tables


class ImageCreateViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_admin_image_create_view_uses_admin_template(self):
        filters = {'disk_format': 'aki'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        filters = {'disk_format': 'ari'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        self.mox.ReplayAll()
        res = self.client.get(
            reverse('horizon:admin:images:create'))
        self.assertTemplateUsed(res, 'admin/images/create.html')


class ImagesViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.keystone: ('tenant_list',)})
    def test_images_list(self):
        filters = {'is_public': None}
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters,
                                       sort_dir='asc',
                                       sort_key='name',
                                       reversed_order=False) \
            .AndReturn([self.images.list(),
                        False, False])
        # Test tenant list
        api.keystone.tenant_list(IsA(http.HttpRequest)).\
            AndReturn([self.tenants.list(), False])
        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:admin:images:index'))
        self.assertContains(res, 'test_tenant', 8, 200)
        self.assertTemplateUsed(res, 'admin/images/index.html')
        self.assertEqual(len(res.context['images_table'].data),
                         len(self.images.list()))

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.keystone: ('tenant_list',)})
    def test_images_list_get_pagination(self):
        images = self.images.list()[:5]
        filters = {'is_public': None}
        kwargs = {'paginate': True, 'filters': filters,
                  'sort_dir': 'asc', 'sort_key': 'name',
                  'reversed_order': False}
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       **kwargs) \
            .AndReturn([images, True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       **kwargs) \
            .AndReturn([images[:2], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       **kwargs) \
            .AndReturn([images[2:4], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[4].id,
                                       **kwargs) \
            .AndReturn([images[4:], True, True])
        # Test tenant list
        api.keystone.tenant_list(IsA(http.HttpRequest)).MultipleTimes().\
            AndReturn([self.tenants.list(), False])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(images))
        self.assertTemplateUsed(res, 'admin/images/index.html')
        self.assertContains(res, 'test_tenant', 6, 200)

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
        self.assertContains(res, 'test_tenant', 3, 200)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[4].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # get third page (item 5)
        self.assertEqual(len(res.context['images_table'].data),
                         1)
        self.assertContains(res, 'test_tenant', 2, 200)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.keystone: ('tenant_list',)})
    def test_images_list_get_prev_pagination(self):
        images = self.images.list()[:3]
        filters = {'is_public': None}
        kwargs = {'paginate': True, 'filters': filters,
                  'sort_dir': 'asc', 'sort_key': 'name'}
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       reversed_order=False,
                                       **kwargs) \
            .AndReturn([images, True, False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       reversed_order=False,
                                       **kwargs) \
            .AndReturn([images[:2], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       reversed_order=False,
                                       **kwargs) \
            .AndReturn([images[2:], True, True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       reversed_order=True,
                                       **kwargs) \
            .AndReturn([images[:2], True, True])
        # Test tenant list
        api.keystone.tenant_list(IsA(http.HttpRequest)).MultipleTimes().\
            AndReturn([self.tenants.list(), False])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(images))
        self.assertTemplateUsed(res, 'admin/images/index.html')
        self.assertContains(res, 'test_tenant', 4, 200)

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)
        self.assertContains(res, 'test_tenant', 3, 200)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # get second page (item 3)
        self.assertEqual(len(res.context['images_table'].data), 1)
        self.assertContains(res, 'test_tenant', 2, 200)

        params = "=".join([tables.AdminImagesTable._meta.prev_pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # prev back to get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)
        self.assertContains(res, 'test_tenant', 3, 200)
