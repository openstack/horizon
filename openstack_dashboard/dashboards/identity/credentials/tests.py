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

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:identity:credentials:index')
INDEX_VIEW_TEMPLATE = 'horizon/common/_data_table_view.html'


class UserCredentialsViewTests(test.TestCase):

    def _get_credentials(self, user):
        credentials = [cred for cred in self.credentials.list()
                       if cred.user_id == user.id]
        return credentials

    @test.create_mocks({api.keystone: ('credentials_list',
                                       'user_get', 'tenant_get')})
    def test_index(self):
        user = self.users.list()[0]
        self.mock_user_get.return_value = user
        credentials = self._get_credentials(user)
        self.mock_credentials_list.return_value = credentials

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_VIEW_TEMPLATE)
        self.assertCountEqual(res.context['table'].data, credentials)
