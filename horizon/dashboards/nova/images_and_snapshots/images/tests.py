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

from django import http
from django.core.urlresolvers import reverse

from horizon import api
from horizon import test

from mox import IsA


IMAGES_INDEX_URL = reverse('horizon:nova:images_and_snapshots:index')


class ImageViewTests(test.TestCase):
    def test_image_detail_get(self):
        image = self.images.first()
        self.mox.StubOutWithMock(api.glance, 'image_get')
        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
                                 .AndReturn(self.images.first())
        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:images_and_snapshots:images:detail',
                args=[image.id]))
        self.assertTemplateUsed(res,
                                'nova/images_and_snapshots/images/detail.html')
        self.assertEqual(res.context['image'].name, image.name)

    def test_image_detail_get_with_exception(self):
        image = self.images.first()
        self.mox.StubOutWithMock(api.glance, 'image_get')
        api.glance.image_get(IsA(http.HttpRequest), str(image.id)) \
                  .AndRaise(self.exceptions.glance)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:images_and_snapshots:images:detail',
                      args=[image.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, IMAGES_INDEX_URL)
