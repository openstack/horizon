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


class VolTypeExtrasTests(test.BaseAdminViewTests):

    @test.create_stubs({api.cinder: ('volume_type_extra_get',
                                     'volume_type_get'), })
    def test_list_extras_when_none_exists(self):
        vol_type = self.cinder_volume_types.first()
        extras = [api.cinder.VolTypeExtraSpec(vol_type.id, 'k1', 'v1')]

        api.cinder.volume_type_get(IsA(http.HttpRequest),
                                   vol_type.id).AndReturn(vol_type)
        api.cinder.volume_type_extra_get(IsA(http.HttpRequest),
                                         vol_type.id).AndReturn(extras)
        self.mox.ReplayAll()
        url = reverse('horizon:admin:volumes:volume_types:extras:index',
                      args=[vol_type.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                "admin/volumes/volume_types/extras/index.html")

    @test.create_stubs({api.cinder: ('volume_type_extra_get',
                                     'volume_type_get'), })
    def test_extras_view_with_exception(self):
        vol_type = self.cinder_volume_types.first()

        api.cinder.volume_type_get(IsA(http.HttpRequest),
                                   vol_type.id).AndReturn(vol_type)
        api.cinder.volume_type_extra_get(IsA(http.HttpRequest),
                                         vol_type.id) \
            .AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()
        url = reverse('horizon:admin:volumes:volume_types:extras:index',
                      args=[vol_type.id])
        resp = self.client.get(url)
        self.assertEqual(len(resp.context['extras_table'].data), 0)
        self.assertMessageCount(resp, error=1)

    @test.create_stubs({api.cinder: ('volume_type_extra_set', ), })
    def test_extra_create_post(self):
        vol_type = self.cinder_volume_types.first()
        create_url = reverse(
            'horizon:admin:volumes:volume_types:extras:create',
            args=[vol_type.id])
        index_url = reverse(
            'horizon:admin:volumes:volume_types:extras:index',
            args=[vol_type.id])

        data = {'key': u'k1',
                'value': u'v1'}

        api.cinder.volume_type_extra_set(IsA(http.HttpRequest),
                                         vol_type.id,
                                         {data['key']: data['value']})
        self.mox.ReplayAll()

        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

    @test.create_stubs({api.cinder: ('volume_type_get', ), })
    def test_extra_create_get(self):
        vol_type = self.cinder_volume_types.first()
        create_url = reverse(
            'horizon:admin:volumes:volume_types:extras:create',
            args=[vol_type.id])

        api.cinder.volume_type_get(IsA(http.HttpRequest),
                                   vol_type.id).AndReturn(vol_type)
        self.mox.ReplayAll()

        resp = self.client.get(create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(
            resp, 'admin/volumes/volume_types/extras/create.html')

    @test.create_stubs({api.cinder: ('volume_type_extra_get',
                                     'volume_type_extra_set',), })
    def test_extra_edit(self):
        vol_type = self.cinder_volume_types.first()
        key = 'foo'
        edit_url = reverse('horizon:admin:volumes:volume_types:extras:edit',
                           args=[vol_type.id, key])
        index_url = reverse('horizon:admin:volumes:volume_types:extras:index',
                            args=[vol_type.id])

        data = {'value': u'v1'}
        extras = {key: data['value']}

        api.cinder.volume_type_extra_get(IsA(http.HttpRequest),
                                         vol_type.id,
                                         raw=True).AndReturn(extras)
        api.cinder.volume_type_extra_set(IsA(http.HttpRequest),
                                         vol_type.id,
                                         extras)
        self.mox.ReplayAll()

        resp = self.client.post(edit_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

    @test.create_stubs({api.cinder: ('volume_type_extra_get',
                                     'volume_type_extra_delete'), })
    def test_extra_delete(self):
        vol_type = self.cinder_volume_types.first()
        extras = [api.cinder.VolTypeExtraSpec(vol_type.id, 'k1', 'v1')]
        formData = {'action': 'extras__delete__k1'}
        index_url = reverse('horizon:admin:volumes:volume_types:extras:index',
                            args=[vol_type.id])

        api.cinder.volume_type_extra_get(IsA(http.HttpRequest),
                                         vol_type.id).AndReturn(extras)
        api.cinder.volume_type_extra_delete(IsA(http.HttpRequest),
                                            vol_type.id,
                                            'k1').AndReturn(vol_type)
        self.mox.ReplayAll()

        res = self.client.post(index_url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, index_url)
