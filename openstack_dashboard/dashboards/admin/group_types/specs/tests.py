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


class GroupTypeSpecTests(test.BaseAdminViewTests):

    @test.create_mocks({api.cinder: ('group_type_spec_list',
                                     'group_type_get')})
    def test_list_specs_when_none_exists(self):
        group_type = self.cinder_group_types.first()
        specs = [api.cinder.GroupTypeSpec(group_type.id, 'k1', 'v1')]

        self.mock_group_type_get.return_value = group_type
        self.mock_group_type_spec_list.return_value = specs
        url = reverse('horizon:admin:group_types:specs:index',
                      args=[group_type.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                "admin/group_types/specs/index.html")
        self.mock_group_type_get.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)
        self.mock_group_type_spec_list.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)

    @test.create_mocks({api.cinder: ('group_type_spec_list',
                                     'group_type_get')})
    def test_specs_view_with_exception(self):
        group_type = self.cinder_group_types.first()

        self.mock_group_type_get.return_value = group_type
        self.mock_group_type_spec_list.side_effect = self.exceptions.cinder
        url = reverse('horizon:admin:group_types:specs:index',
                      args=[group_type.id])
        resp = self.client.get(url)
        self.assertEqual(len(resp.context['specs_table'].data), 0)
        self.assertMessageCount(resp, error=1)
        self.mock_group_type_get.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)
        self.mock_group_type_spec_list.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)

    @test.create_mocks({api.cinder: ('group_type_spec_list',
                                     'group_type_spec_set', )})
    def test_spec_create_post(self):
        group_type = self.cinder_group_types.first()
        create_url = reverse(
            'horizon:admin:group_types:specs:create',
            args=[group_type.id])
        index_url = reverse(
            'horizon:admin:group_types:index')

        data = {'key': u'k1',
                'value': u'v1'}

        self.mock_group_type_spec_set.return_value = None
        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)
        self.mock_group_type_spec_set.assert_called_once_with(
            test.IsHttpRequest(),
            group_type.id,
            {data['key']: data['value']})

    @test.create_mocks({api.cinder: ('group_type_get', )})
    def test_spec_create_get(self):
        group_type = self.cinder_group_types.first()
        create_url = reverse(
            'horizon:admin:group_types:specs:create',
            args=[group_type.id])

        self.mock_group_type_get.return_value = group_type
        resp = self.client.get(create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(
            resp, 'admin/group_types/specs/create.html')
        self.mock_group_type_get.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)

    @test.create_mocks({api.cinder: ('group_type_spec_list',
                                     'group_type_spec_set',)})
    def test_spec_edit(self):
        group_type = self.cinder_group_types.first()
        key = 'foo'
        edit_url = reverse('horizon:admin:group_types:specs:edit',
                           args=[group_type.id, key])
        index_url = reverse('horizon:admin:group_types:index')

        data = {'value': u'v1'}
        specs = {key: data['value']}

        self.mock_group_type_spec_list.return_value = specs
        self.mock_group_type_spec_set.return_value = None

        resp = self.client.post(edit_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

        self.mock_group_type_spec_list.assert_called_once_with(
            test.IsHttpRequest(), group_type.id, raw=True)
        self.mock_group_type_spec_set.assert_called_once_with(
            test.IsHttpRequest(), group_type.id, specs)

    @test.create_mocks({api.cinder: ('group_type_spec_list',
                                     'group_type_spec_unset')})
    def test_spec_delete(self):
        group_type = self.cinder_group_types.first()
        specs = [api.cinder.GroupTypeSpec(group_type.id, 'k1', 'v1')]
        formData = {'action': 'specs__delete__k1'}
        index_url = reverse('horizon:admin:group_types:specs:index',
                            args=[group_type.id])

        self.mock_group_type_spec_list.return_value = specs
        self.mock_group_type_spec_unset.return_value = group_type

        res = self.client.post(index_url, formData)

        redirect = reverse('horizon:admin:group_types:index')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)

        self.mock_group_type_spec_list.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)
        self.mock_group_type_spec_unset.assert_called_once_with(
            test.IsHttpRequest(), group_type.id, ['k1'])
