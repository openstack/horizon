# Copyright 2018 SUSE Linux GmbH
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

import mock
import six

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


APP_CREDS_INDEX_URL = reverse('horizon:identity:application_credentials:index')


class ApplicationCredentialViewTests(test.TestCase):
    def test_application_credential_create_get(self):
        url = reverse('horizon:identity:application_credentials:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                                'identity/application_credentials/create.html')

    @mock.patch.object(api.keystone, 'application_credential_create')
    @mock.patch.object(api.keystone, 'application_credential_list')
    def test_application_credential_create(self, mock_app_cred_list,
                                           mock_app_cred_create):
        new_app_cred = self.application_credentials.first()
        mock_app_cred_create.return_value = new_app_cred
        data = {
            'name': new_app_cred.name,
            'description': new_app_cred.description
        }
        api_data = {
            'name': new_app_cred.name,
            'description': new_app_cred.description,
            'expires_at': new_app_cred.expires_at,
            'roles': None,
            'unrestricted': False,
            'secret': None
        }

        url = reverse('horizon:identity:application_credentials:create')
        res = self.client.post(url, data)

        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)

        mock_app_cred_create.assert_called_once_with(test.IsHttpRequest(),
                                                     **api_data)

    @mock.patch.object(api.keystone, 'application_credential_get')
    def test_application_credential_detail_get(self, mock_app_cred_get):
        app_cred = self.application_credentials.list()[1]
        mock_app_cred_get.return_value = app_cred

        res = self.client.get(
            reverse('horizon:identity:application_credentials:detail',
                    args=[app_cred.id]))

        self.assertTemplateUsed(
            res, 'identity/application_credentials/detail.html')
        self.assertEqual(res.context['application_credential'].name,
                         app_cred.name)
        mock_app_cred_get.assert_called_once_with(test.IsHttpRequest(),
                                                  six.text_type(app_cred.id))

    @mock.patch.object(api.keystone, 'application_credential_get')
    def test_application_credential_detail_get_with_exception(
            self, mock_app_cred_get):
        app_cred = self.application_credentials.list()[1]

        mock_app_cred_get.side_effect = self.exceptions.keystone

        url = reverse('horizon:identity:application_credentials:detail',
                      args=[app_cred.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, APP_CREDS_INDEX_URL)
        mock_app_cred_get.assert_called_once_with(test.IsHttpRequest(),
                                                  six.text_type(app_cred.id))

    @mock.patch.object(api.keystone, 'application_credential_create')
    @mock.patch.object(api.keystone, 'application_credential_list')
    def test_application_credential_openrc(self, mock_app_cred_list,
                                           mock_app_cred_create):

        new_app_cred = self.application_credentials.first()
        mock_app_cred_create.return_value = new_app_cred
        data = {
            'name': new_app_cred.name,
            'description': new_app_cred.description
        }
        url = reverse('horizon:identity:application_credentials:create')
        res = self.client.post(url, data)

        download_url = (
            'horizon:identity:application_credentials:download_openrc'
        )
        url = reverse(download_url)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(
            res, 'identity/application_credentials/openrc.sh.template')

    @mock.patch.object(api.keystone, 'application_credential_create')
    @mock.patch.object(api.keystone, 'application_credential_list')
    def test_application_credential_cloudsyaml(self, mock_app_cred_list,
                                               mock_app_cred_create):

        new_app_cred = self.application_credentials.first()
        mock_app_cred_create.return_value = new_app_cred
        data = {
            'name': new_app_cred.name,
            'description': new_app_cred.description
        }
        url = reverse('horizon:identity:application_credentials:create')
        res = self.client.post(url, data)

        download_url = (
            'horizon:identity:application_credentials:download_clouds_yaml'
        )
        url = reverse(download_url)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(
            res, 'identity/application_credentials/clouds.yaml.template')
