# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.admin.images import tables


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
                                       filters=filters) \
            .AndReturn([self.images.list(),
                        False])
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
                                       filters=filters) \
                                .AndReturn([images,
                                            True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       filters=filters) \
                                .AndReturn([images[:2],
                                            True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[2].id,
                                       paginate=True,
                                       filters=filters) \
                                .AndReturn([images[2:4],
                                            True])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=images[4].id,
                                       paginate=True,
                                       filters=filters) \
                                .AndReturn([images[4:],
                                            True])
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

        url = "?".join([reverse('horizon:admin:images:index'),
                    "=".join([tables.AdminImagesTable._meta.pagination_param,
                              images[2].id])])
        res = self.client.get(url)
        # get second page (items 2-4)
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        url = "?".join([reverse('horizon:admin:images:index'),
                    "=".join([tables.AdminImagesTable._meta.pagination_param,
                              images[4].id])])
        res = self.client.get(url)
        # get third page (item 5)
        self.assertEqual(len(res.context['images_table'].data),
                         1)
