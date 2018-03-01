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
from django.test.utils import override_settings
from django.urls import reverse

import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.images import tables

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class ImageCreateViewTest(test.BaseAdminViewTests):
    @mock.patch.object(api.glance, 'image_list_detailed')
    def test_admin_image_create_view_uses_admin_template(self,
                                                         mock_image_list):
        filters1 = {'disk_format': 'aki'}
        filters2 = {'disk_format': 'ari'}

        mock_image_list.return_value = [self.images.list(), False, False]

        res = self.client.get(
            reverse('horizon:admin:images:create'))

        calls = [mock.call(test.IsHttpRequest(), filters=filters1),
                 mock.call(test.IsHttpRequest(), filters=filters2)]
        mock_image_list.assert_has_calls(calls)

        self.assertTemplateUsed(res, 'admin/images/create.html')


class ImagesViewTest(test.BaseAdminViewTests):
    @mock.patch.object(api.glance, 'image_list_detailed')
    @mock.patch.object(api.keystone, 'tenant_list')
    def test_images_list(self, mock_tenant_list, mock_image_list):
        filters = {'is_public': None}
        mock_image_list.return_value = [self.images.list(), False, False]
        mock_tenant_list.return_value = [self.tenants.list(), False]

        # Test tenant list
        res = self.client.get(
            reverse('horizon:admin:images:index'))

        mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        mock_image_list.assert_called_once_with(test.IsHttpRequest(),
                                                marker=None,
                                                paginate=True,
                                                filters=filters,
                                                sort_dir='asc',
                                                sort_key='name',
                                                reversed_order=False)
        self.assertContains(res, 'test_tenant', 9, 200)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['images_table'].data),
                         len(self.images.list()))

    @test.update_settings(FILTER_DATA_FIRST={'admin.images': True})
    def test_images_list_with_admin_filter_first(self):
        res = self.client.get(reverse('horizon:admin:images:index'))
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        images = res.context['table'].data
        self.assertItemsEqual(images, [])

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'image_list_detailed')
    @mock.patch.object(api.keystone, 'tenant_list')
    def test_images_list_get_pagination(self, mock_tenant_list,
                                        mock_image_list):
        images = self.images.list()[:5]
        filters = {'is_public': None}
        kwargs = {'paginate': True, 'filters': filters,
                  'sort_dir': 'asc', 'sort_key': 'name',
                  'reversed_order': False}
        mock_image_list.side_effect = [[images, True, True],
                                       [images[:2], True, True],
                                       [images[2:4], True, True],
                                       [images[4:], True, True]]

        mock_tenant_list.return_value = [self.tenants.list(), False]
        # Test tenant list
        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)

        image_calls = [mock.call(test.IsHttpRequest(), marker=None, **kwargs),
                       mock.call(test.IsHttpRequest(), marker=None, **kwargs),
                       mock.call(test.IsHttpRequest(),
                                 marker=images[2].id, **kwargs),
                       mock.call(test.IsHttpRequest(),
                                 marker=images[4].id, **kwargs)]
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(images))
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertContains(res, 'test_tenant', 7, 200)

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
        self.assertContains(res, 'test_tenant', 4, 200)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[4].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)

        # get third page (item 5)
        self.assertEqual(len(res.context['images_table'].data),
                         1)
        self.assertContains(res, 'test_tenant', 3, 200)

        mock_image_list.assert_has_calls(image_calls)
        mock_tenant_list.assert_called_with(test.IsHttpRequest())

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @mock.patch.object(api.glance, 'image_list_detailed')
    @mock.patch.object(api.keystone, 'tenant_list')
    def test_images_list_get_prev_pagination(self, mock_tenant_list,
                                             mock_image_list):
        images = self.images.list()[:3]
        filters = {'is_public': None}
        kwargs = {'paginate': True, 'filters': filters,
                  'sort_dir': 'asc', 'sort_key': 'name'}

        mock_image_list.side_effect = [[images, True, False],
                                       [images[:2], True, True],
                                       [images[2:], True, True],
                                       [images[:2], True, True]]

        mock_tenant_list.return_value = [self.tenants.list(), False]

        image_calls = [mock.call(test.IsHttpRequest(), marker=None,
                                 reversed_order=False, **kwargs),
                       mock.call(test.IsHttpRequest(), marker=None,
                                 reversed_order=False, **kwargs),
                       mock.call(test.IsHttpRequest(), marker=images[2].id,
                                 reversed_order=False, **kwargs),
                       mock.call(test.IsHttpRequest(), marker=images[2].id,
                                 reversed_order=True, **kwargs)]

        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(images))
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertContains(res, 'test_tenant', 5, 200)

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)
        self.assertContains(res, 'test_tenant', 4, 200)

        params = "=".join([tables.AdminImagesTable._meta.pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # get second page (item 3)
        self.assertEqual(len(res.context['images_table'].data), 1)
        self.assertContains(res, 'test_tenant', 3, 200)

        params = "=".join([tables.AdminImagesTable._meta.prev_pagination_param,
                           images[2].id])
        url = "?".join([reverse('horizon:admin:images:index'), params])
        res = self.client.get(url)
        # prev back to get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)
        self.assertContains(res, 'test_tenant', 4, 200)

        mock_image_list.assert_has_calls(image_calls)
        mock_tenant_list.assert_called_with(test.IsHttpRequest())
