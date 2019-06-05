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

from django.urls import reverse
import mock
import six
from six.moves.urllib import parse

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.key_pairs.forms \
    import KEYPAIR_ERROR_MESSAGES
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:key_pairs:index')


class KeyPairTests(test.TestCase):
    @test.create_mocks({api.nova: ('keypair_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        keypairs = self.keypairs.list()
        quota_data = self.quota_usages.first()

        self.mock_tenant_quota_usages.return_value = quota_data
        self.mock_keypair_list.return_value = keypairs

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertItemsEqual(res.context['keypairs_table'].data, keypairs)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 4,
            mock.call(test.IsHttpRequest(), targets=('key_pairs', )))
        self.mock_keypair_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.nova: ('keypair_list',
                                   'keypair_delete')})
    def test_delete_keypair(self):
        keypair = self.keypairs.first()

        self.mock_keypair_list.return_value = self.keypairs.list()
        self.mock_keypair_delete.return_value = None

        keypair_name = parse.quote(keypair.name)
        formData = {'action': 'keypairs__delete__%s' % keypair_name}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_keypair_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_keypair_delete.assert_called_once_with(test.IsHttpRequest(),
                                                         keypair.name)

    @test.create_mocks({api.nova: ('keypair_list',
                                   'keypair_delete')})
    def test_delete_keypair_exception(self):
        keypair = self.keypairs.first()

        self.mock_keypair_list.return_value = self.keypairs.list()
        self.mock_keypair_delete.side_effect = self.exceptions.nova

        keypair_name = parse.quote(keypair.name)
        formData = {'action': 'keypairs__delete__%s' % keypair_name}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_keypair_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_keypair_delete.assert_called_once_with(test.IsHttpRequest(),
                                                         keypair.name)

    @test.create_mocks({api.nova: ('keypair_get',)})
    def test_keypair_detail_get(self):
        keypair = self.keypairs.first()
        keypair.private_key = "secret"

        self.mock_keypair_get.return_value = keypair

        context = {'keypair_name': keypair.name}
        url = reverse('horizon:project:key_pairs:detail',
                      kwargs={'keypair_name': keypair.name})
        res = self.client.get(url, context)
        self.assertContains(res, "<dd>%s</dd>" % keypair.name, 1, 200)

        self.mock_keypair_get.assert_called_once_with(test.IsHttpRequest(),
                                                      keypair.name)

    @test.create_mocks({api.nova: ('keypair_import',)})
    def test_import_keypair(self):
        key1_name = "new_key_pair"
        public_key = "ssh-rsa ABCDEFGHIJKLMNOPQR\r\n" \
                     "STUVWXYZ1234567890\r" \
                     "XXYYZZ user@computer\n\n"
        key_type = "ssh"
        self.mock_keypair_import.return_value = None

        formData = {'method': 'ImportKeypair',
                    'name': key1_name,
                    'public_key': public_key,
                    'key_type': key_type}
        url = reverse('horizon:project:key_pairs:import')
        res = self.client.post(url, formData)
        self.assertMessageCount(res, success=1)

        self.mock_keypair_import.assert_called_once_with(
            test.IsHttpRequest(), key1_name,
            public_key.replace("\r", "").replace("\n", ""),
            key_type)

    @test.create_mocks({api.nova: ('keypair_import',)})
    def test_import_keypair_invalid_key(self):
        key_name = "new_key_pair"
        public_key = "ABCDEF"
        key_type = "ssh"

        self.mock_keypair_import.side_effect = self.exceptions.nova

        formData = {'method': 'ImportKeypair',
                    'name': key_name,
                    'public_key': public_key,
                    'key_type': key_type}
        url = reverse('horizon:project:key_pairs:import')
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        msg = 'Unable to import key pair.'
        self.assertFormErrors(res, count=1, message=msg)

        self.mock_keypair_import.assert_called_once_with(
            test.IsHttpRequest(), key_name, public_key, key_type)

    def test_import_keypair_invalid_key_name(self):
        key_name = "invalid#key?name=!"
        public_key = "ABCDEF"
        key_type = "ssh"

        formData = {'method': 'ImportKeypair',
                    'name': key_name,
                    'public_key': public_key,
                    'key_type': key_type}
        url = reverse('horizon:project:key_pairs:import')
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        msg = six.text_type(KEYPAIR_ERROR_MESSAGES['invalid'])
        self.assertFormErrors(res, count=1, message=msg)

    def test_import_keypair_space_key_name(self):
        key_name = " "
        public_key = "ABCDEF"
        key_type = "ssh"

        formData = {'method': 'ImportKeypair',
                    'name': key_name,
                    'public_key': public_key,
                    'key_type': key_type}
        url = reverse('horizon:project:key_pairs:import')
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        msg = six.text_type(KEYPAIR_ERROR_MESSAGES['invalid'])
        self.assertFormErrors(res, count=1, message=msg)

    @test.create_mocks({api.nova: ('keypair_import',)})
    def test_import_keypair_with_regex_defined_name(self):
        key1_name = "new-key-pair with_regex"
        public_key = "ssh-rsa ABCDEFGHIJKLMNOPQR\r\n" \
                     "STUVWXYZ1234567890\r" \
                     "XXYYZZ user@computer\n\n"
        key_type = "ssh"
        self.mock_keypair_import.return_value = None

        formData = {'method': 'ImportKeypair',
                    'name': key1_name,
                    'public_key': public_key,
                    'key_type': key_type}
        url = reverse('horizon:project:key_pairs:import')
        res = self.client.post(url, formData)
        self.assertMessageCount(res, success=1)

        self.mock_keypair_import.assert_called_once_with(
            test.IsHttpRequest(), key1_name,
            public_key.replace("\r", "").replace("\n", ""),
            key_type)
