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


INDEX_URL = reverse(
    'horizon:project:data_processing.data_image_registry:index')
REGISTER_URL = reverse(
    'horizon:project:data_processing.data_image_registry:register')


class DataProcessingImageRegistryTests(test.TestCase):
    @test.create_stubs({api.sahara: ('image_list',)})
    def test_index(self):
        api.sahara.image_list(IsA(http.HttpRequest)) \
            .AndReturn(self.images.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(
            res,
            'project/data_processing.data_image_registry/image_registry.html')
        self.assertContains(res, 'Image Registry')
        self.assertContains(res, 'Image')
        self.assertContains(res, 'Tags')

    @test.create_stubs({api.sahara: ('image_get',
                                     'image_update',
                                     'image_tags_update',
                                     'image_list'),
                        api.glance: ('image_list_detailed',)})
    def test_register(self):
        image = self.images.first()
        image_id = image.id
        test_username = 'myusername'
        test_description = 'mydescription'
        api.sahara.image_get(IsA(http.HttpRequest),
                             image_id).MultipleTimes().AndReturn(image)
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'owner': self.user.id,
                                                'status': 'active'}) \
            .AndReturn((self.images.list(), False, False))
        api.sahara.image_update(IsA(http.HttpRequest),
                                image_id,
                                test_username,
                                test_description) \
            .AndReturn(True)
        api.sahara.image_tags_update(IsA(http.HttpRequest),
                                     image_id,
                                     {}) \
            .AndReturn(True)
        api.sahara.image_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        self.mox.ReplayAll()

        res = self.client.post(
            REGISTER_URL,
            {'image_id': image_id,
             'user_name': test_username,
             'description': test_description,
             'tags_list': '{}'})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('image_list',
                                     'image_unregister')})
    def test_unregister(self):
        image = self.images.first()
        api.sahara.image_list(IsA(http.HttpRequest)) \
            .AndReturn(self.images.list())
        api.sahara.image_unregister(IsA(http.HttpRequest), image.id)
        self.mox.ReplayAll()

        form_data = {'action': 'image_registry__delete__%s' % image.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('image_get',
                                     'image_update',
                                     'image_tags_update')})
    def test_edit_tags(self):
        image = self.registered_images.first()
        api.sahara.image_get(IsA(http.HttpRequest),
                             image.id).MultipleTimes().AndReturn(image)
        api.sahara.image_update(IsA(http.HttpRequest),
                                image.id,
                                image.username,
                                image.description) \
            .AndReturn(True)
        api.sahara.image_tags_update(IsA(http.HttpRequest),
                                     image.id,
                                     {"0": "mytag"}) \
            .AndReturn(True)
        self.mox.ReplayAll()

        edit_tags_url = reverse(
            'horizon:project:data_processing.data_image_registry:edit_tags',
            args=[image.id])
        res = self.client.post(
            edit_tags_url,
            {'image_id': image.id,
             'user_name': image.username,
             'description': image.description,
             'tags_list': '{"0": "mytag"}'})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
