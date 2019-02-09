# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.urls import reverse

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:group_types:index')


class GroupTypeTests(test.BaseAdminViewTests):
    @test.create_mocks({cinder: ('group_type_create',)})
    def test_create_group_type(self):
        group_type = self.cinder_group_types.first()
        formData = {'name': 'group type 1',
                    'group_type_description': 'test desc',
                    'is_public': True}

        self.mock_group_type_create.return_value = group_type

        url = reverse('horizon:admin:group_types:create_type')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_type_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            formData['group_type_description'],
            formData['is_public'])

    @test.create_mocks({api.cinder: ('group_type_get',
                                     'group_type_update')})
    def _test_update_group_type(self, is_public):
        group_type = self.cinder_group_types.first()
        formData = {'name': group_type.name,
                    'description': 'test desc updated',
                    'is_public': is_public}
        self.mock_group_type_get.return_value = group_type
        self.mock_group_type_update.return_value = group_type

        url = reverse('horizon:admin:group_types:update_type',
                      args=[group_type.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_type_get.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)
        self.mock_group_type_update.assert_called_once_with(
            test.IsHttpRequest(),
            group_type.id,
            formData['name'],
            formData['description'],
            formData['is_public'])

    def test_update_group_type_public_true(self):
        self._test_update_group_type(True)

    def test_update_group_type_public_false(self):
        self._test_update_group_type(False)

    @test.create_mocks({api.cinder: ('group_type_list',
                                     'group_type_delete',)})
    def test_delete_group_type(self):
        group_type = self.cinder_group_types.first()
        formData = {'action': 'group_types__delete__%s' % group_type.id}

        self.mock_group_type_list.return_value = \
            self.cinder_group_types.list()
        self.mock_group_type_delete.return_value = None

        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_type_list.\
            assert_called_once_with(test.IsHttpRequest())
        self.mock_group_type_delete.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)

    @test.create_mocks({api.cinder: ('group_type_list',
                                     'group_type_delete',)})
    def test_delete_group_type_exception(self):
        group_type = self.cinder_group_types.first()
        formData = {'action': 'group_types__delete__%s' % group_type.id}

        self.mock_group_type_list.return_value = \
            self.cinder_group_types.list()
        self.mock_group_type_delete.side_effect = exceptions.BadRequest()

        res = self.client.post(INDEX_URL, formData)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_type_list.\
            assert_called_once_with(test.IsHttpRequest())
        self.mock_group_type_delete.assert_called_once_with(
            test.IsHttpRequest(), group_type.id)
