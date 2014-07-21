# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class ImageCustomPropertiesTests(test.BaseAdminViewTests):

    @test.create_stubs({api.glance: ('image_get',
                                     'image_get_properties'), })
    def test_list_properties(self):
        image = self.images.first()
        props = [api.glance.ImageCustomProperty(image.id, 'k1', 'v1')]
        api.glance.image_get(IsA(http.HttpRequest), image.id).AndReturn(image)
        api.glance.image_get_properties(IsA(http.HttpRequest),
                                 image.id, False).AndReturn(props)
        self.mox.ReplayAll()
        url = reverse('horizon:admin:images:properties:index', args=[image.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/images/properties/index.html")

    @test.create_stubs({api.glance: ('image_update_properties',), })
    def test_property_create_post(self):
        image = self.images.first()
        create_url = reverse('horizon:admin:images:properties:create',
                             args=[image.id])
        index_url = reverse('horizon:admin:images:properties:index',
                            args=[image.id])
        api.glance.image_update_properties(IsA(http.HttpRequest),
                                           image.id, **{'k1': 'v1'})
        self.mox.ReplayAll()
        data = {'image_id': image.id,
                'key': 'k1',
                'value': 'v1'}
        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

    @test.create_stubs({api.glance: ('image_get',), })
    def test_property_create_get(self):
        image = self.images.first()
        create_url = reverse('horizon:admin:images:properties:create',
                             args=[image.id])
        api.glance.image_get(IsA(http.HttpRequest), image.id).AndReturn(image)
        self.mox.ReplayAll()
        resp = self.client.get(create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/images/properties/create.html')

    @test.create_stubs({api.glance: ('image_update_properties',
                                     'image_get_property'), })
    def test_property_update_post(self):
        image = self.images.first()
        prop = api.glance.ImageCustomProperty(image.id, 'k1', 'v1')
        edit_url = reverse('horizon:admin:images:properties:edit',
                            args=[image.id, prop.id])
        index_url = reverse('horizon:admin:images:properties:index',
                            args=[image.id])
        api.glance.image_get_property(IsA(http.HttpRequest),
                                      image.id, 'k1', False).AndReturn(prop)
        api.glance.image_update_properties(IsA(http.HttpRequest),
                                           image.id, **{'k1': 'v2'})
        self.mox.ReplayAll()
        data = {'image_id': image.id,
                'key': 'k1',
                'value': 'v2'}
        resp = self.client.post(edit_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

    @test.create_stubs({api.glance: ('image_get',
                                     'image_get_property'), })
    def test_property_update_get(self):
        image = self.images.first()
        prop = api.glance.ImageCustomProperty(image.id, 'k1', 'v1')
        edit_url = reverse('horizon:admin:images:properties:edit',
                            args=[image.id, prop.id])
        api.glance.image_get(IsA(http.HttpRequest), image.id).AndReturn(image)
        api.glance.image_get_property(IsA(http.HttpRequest),
                                      image.id, 'k1', False).AndReturn(prop)
        self.mox.ReplayAll()
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin/images/properties/edit.html')
