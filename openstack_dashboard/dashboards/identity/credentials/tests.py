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


def _update_url(credential_id):
    return reverse('horizon:identity:credentials:update',
                   args=[credential_id])


class UserCredentialsViewTests(test.TestCase):

    def _get_credentials(self, user_id):
        credentials = [cred for cred in self.credentials.list()
                       if cred.user_id == user_id]
        return credentials

    @test.create_mocks({api.keystone: ('credentials_list',
                                       'user_get', 'tenant_get')})
    def test_index(self):
        user = self.users.list()[0]
        self.mock_user_get.return_value = user
        credentials = self._get_credentials(user.id)
        self.mock_credentials_list.return_value = credentials

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_VIEW_TEMPLATE)
        self.assertCountEqual(res.context['table'].data, credentials)

    @test.create_mocks({api.keystone: ('credential_get', 'credential_update',
                                       'user_list', 'tenant_list')})
    def test_update_sends_only_the_blob(self):
        """Keystone rejects type, user_id and project_id on PATCH.

        They became immutable, so a request carrying them comes back as
        HTTP 400 and the whole update fails.
        """
        credential = self.credentials.first()
        self.mock_credential_get.return_value = credential
        self.mock_user_list.return_value = self.users.list()
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        form_data = {
            'id': credential.id,
            'data': 'NEWBLOBONSWG4TFOQYTM43FMNZGK5BR',
            # Sent by the browser but ignored: the fields are disabled.
            'user_name': credential.user_id,
            'cred_type': credential.type,
            'project': credential.project_id,
        }
        res = self.client.post(_update_url(credential.id), form_data)

        self.assertNoFormErrors(res)
        self.mock_credential_update.assert_called_once_with(
            test.IsHttpRequest(), credential.id,
            'NEWBLOBONSWG4TFOQYTM43FMNZGK5BR')

    @test.create_mocks({api.keystone: ('credential_get', 'credential_update',
                                       'user_list', 'tenant_list')})
    def test_update_ignores_tampered_immutable_fields(self):
        """A POST forging the disabled fields must not reach keystone."""
        credential = self.credentials.first()
        self.mock_credential_get.return_value = credential
        self.mock_user_list.return_value = self.users.list()
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        form_data = {
            'id': credential.id,
            'data': 'NEWBLOBONSWG4TFOQYTM43FMNZGK5BR',
            'user_name': 'someone-else',
            'cred_type': 'ec2',
            'project': 'another-project',
        }
        res = self.client.post(_update_url(credential.id), form_data)

        self.assertNoFormErrors(res)
        __, called_id, called_blob = \
            self.mock_credential_update.call_args.args
        self.assertEqual(credential.id, called_id)
        self.assertEqual('NEWBLOBONSWG4TFOQYTM43FMNZGK5BR', called_blob)
        self.assertEqual({}, self.mock_credential_update.call_args.kwargs)

    @test.create_mocks({api.keystone: ('credential_get', 'credential_update',
                                       'user_list', 'tenant_list')})
    def test_update_when_the_project_cannot_be_listed(self):
        """The form must survive a project missing from the listing.

        A disabled field still validates its initial against the choices, so
        a credential whose project is disabled or invisible to this operator
        would otherwise be impossible to edit at all.
        """
        credential = self.credentials.first()
        self.mock_credential_get.return_value = credential
        self.mock_user_list.return_value = self.users.list()
        self.mock_tenant_list.return_value = [[], False]

        form_data = {
            'id': credential.id,
            'data': 'NEWBLOBONSWG4TFOQYTM43FMNZGK5BR',
        }
        res = self.client.post(_update_url(credential.id), form_data)

        self.assertNoFormErrors(res)
        self.mock_credential_update.assert_called_once_with(
            test.IsHttpRequest(), credential.id,
            'NEWBLOBONSWG4TFOQYTM43FMNZGK5BR')
