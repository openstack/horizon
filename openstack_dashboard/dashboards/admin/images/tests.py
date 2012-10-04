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

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from .tables import AdminImagesTable


class ImagesViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api: ('image_list_detailed',)})
    def test_images_list(self):
        api.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None) \
                                       .AndReturn([self.images.list(),
                                                   False])
        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:admin:images:index'))
        self.assertTemplateUsed(res, 'admin/images/index.html')
        self.assertEqual(len(res.context['images_table'].data),
                         len(self.images.list()))

    @test.create_stubs({api: ('image_list_detailed',)})
    def test_images_list_get_pagination(self):
        api.image_list_detailed(IsA(http.HttpRequest),
                                    marker=None) \
                                .AndReturn([self.images.list(),
                                           True])
        api.image_list_detailed(IsA(http.HttpRequest),
                                    marker=None) \
                                .AndReturn([self.images.list()[:2],
                                           True])
        api.image_list_detailed(IsA(http.HttpRequest),
                                    marker=self.images.list()[2].id) \
                                .AndReturn([self.images.list()[2:4],
                                           True])
        api.image_list_detailed(IsA(http.HttpRequest),
                                    marker=self.images.list()[4].id) \
                                .AndReturn([self.images.list()[4:],
                                           True])
        self.mox.ReplayAll()

        url = reverse('horizon:admin:images:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['images_table'].data),
                         len(self.images.list()))
        self.assertTemplateUsed(res, 'admin/images/index.html')

        page_size = getattr(settings, "API_RESULT_PAGE_SIZE", None)
        settings.API_RESULT_PAGE_SIZE = 2

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        url = "?".join([reverse('horizon:admin:images:index'),
                        "=".join([AdminImagesTable._meta.pagination_param,
                                  self.images.list()[2].id])])
        res = self.client.get(url)
        # get second page (items 2-4)
        self.assertEqual(len(res.context['images_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        url = "?".join([reverse('horizon:admin:images:index'),
                        "=".join([AdminImagesTable._meta.pagination_param,
                                  self.images.list()[4].id])])
        res = self.client.get(url)
        # get third page (item 5)
        self.assertEqual(len(res.context['images_table'].data),
                         1)

        # restore API_RESULT_PAGE_SIZE
        if page_size:
            settings.API_RESULT_PAGE_SIZE = page_size
        else:
            del settings.API_RESULT_PAGE_SIZE
