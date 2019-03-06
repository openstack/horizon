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

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class VolTypeExtrasTests(test.BaseAdminViewTests):

    @test.create_mocks({api.cinder: ('volume_type_extra_get',
                                     'volume_type_get')})
    def test_list_extras_when_none_exists(self):
        vol_type = self.cinder_volume_types.first()
        extras = [api.cinder.VolTypeExtraSpec(vol_type.id, 'k1', 'v1')]

        self.mock_volume_type_get.return_value = vol_type
        self.mock_volume_type_extra_get.return_value = extras
        url = reverse('horizon:admin:volume_types:extras:index',
                      args=[vol_type.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                "admin/volume_types/extras/index.html")
        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id)
        self.mock_volume_type_extra_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id)

    @test.create_mocks({api.cinder: ('volume_type_extra_get',
                                     'volume_type_get')})
    def test_extras_view_with_exception(self):
        vol_type = self.cinder_volume_types.first()

        self.mock_volume_type_get.return_value = vol_type
        self.mock_volume_type_extra_get.side_effect = self.exceptions.cinder
        url = reverse('horizon:admin:volume_types:extras:index',
                      args=[vol_type.id])
        resp = self.client.get(url)
        self.assertEqual(len(resp.context['extras_table'].data), 0)
        self.assertMessageCount(resp, error=1)
        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id)
        self.mock_volume_type_extra_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id)

    @test.create_mocks({api.cinder: ('volume_type_extra_set',
                                     'volume_type_extra_get')})
    def test_extra_create_post(self):
        vol_type = self.cinder_volume_types.first()
        create_url = reverse(
            'horizon:admin:volume_types:extras:create',
            args=[vol_type.id])
        index_url = reverse(
            'horizon:admin:volume_types:extras:index',
            args=[vol_type.id])

        data = {'key': u'k1',
                'value': u'v1'}

        self.mock_volume_type_extra_set.return_value = None
        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)
        self.mock_volume_type_extra_set.assert_called_once_with(
            test.IsHttpRequest(),
            vol_type.id,
            {data['key']: data['value']})

    @test.create_mocks({api.cinder: ('volume_type_get', )})
    def test_extra_create_get(self):
        vol_type = self.cinder_volume_types.first()
        create_url = reverse(
            'horizon:admin:volume_types:extras:create',
            args=[vol_type.id])

        self.mock_volume_type_get.return_value = vol_type
        resp = self.client.get(create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(
            resp, 'admin/volume_types/extras/create.html')
        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id)

    @test.create_mocks({api.cinder: ('volume_type_extra_get',
                                     'volume_type_extra_set',)})
    def test_extra_edit(self):
        vol_type = self.cinder_volume_types.first()
        key = 'foo'
        edit_url = reverse('horizon:admin:volume_types:extras:edit',
                           args=[vol_type.id, key])
        index_url = reverse('horizon:admin:volume_types:extras:index',
                            args=[vol_type.id])

        data = {'value': u'v1'}
        extras = {key: data['value']}

        self.mock_volume_type_extra_get.return_value = extras
        self.mock_volume_type_extra_set.return_value = None

        resp = self.client.post(edit_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

        self.mock_volume_type_extra_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id, raw=True)
        self.mock_volume_type_extra_set.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id, extras)

    @test.create_mocks({api.cinder: ('volume_type_extra_get',
                                     'volume_type_extra_delete')})
    def test_extra_delete(self):
        vol_type = self.cinder_volume_types.first()
        extras = [api.cinder.VolTypeExtraSpec(vol_type.id, 'k1', 'v1')]
        formData = {'action': 'extras__delete__k1'}
        index_url = reverse('horizon:admin:volume_types:extras:index',
                            args=[vol_type.id])

        self.mock_volume_type_extra_get.return_value = extras
        self.mock_volume_type_extra_delete.return_value = vol_type

        res = self.client.post(index_url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, index_url)

        self.mock_volume_type_extra_get.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id)
        self.mock_volume_type_extra_delete.assert_called_once_with(
            test.IsHttpRequest(), vol_type.id, ['k1'])
