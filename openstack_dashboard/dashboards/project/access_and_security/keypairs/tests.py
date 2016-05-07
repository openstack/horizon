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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security.\
    keypairs.forms import CreateKeypair
from openstack_dashboard.dashboards.project.access_and_security.\
    keypairs.forms import KEYPAIR_ERROR_MESSAGES
from openstack_dashboard.test import helpers as test


INDEX_VIEW_URL = reverse('horizon:project:access_and_security:index')


class KeyPairViewTests(test.TestCase):
    def test_delete_keypair(self):
        keypair = self.keypairs.first()

        self.mox.StubOutWithMock(api.network, 'floating_ip_supported')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_delete')

        # floating_ip_supported is called in Floating IP tab allowed().
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.nova.keypair_delete(IsA(http.HttpRequest), keypair.name)
        self.mox.ReplayAll()

        formData = {'action': 'keypairs__delete__%s' % keypair.name}
        res = self.client.post(INDEX_VIEW_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_VIEW_URL)

    def test_delete_keypair_exception(self):
        keypair = self.keypairs.first()
        self.mox.StubOutWithMock(api.network, 'floating_ip_supported')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_delete')

        # floating_ip_supported is called in Floating IP tab allowed().
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.nova.keypair_delete(IsA(http.HttpRequest), keypair.name) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'keypairs__delete__%s' % keypair.name}
        res = self.client.post(INDEX_VIEW_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_VIEW_URL)

    def test_create_keypair_get(self):
        res = self.client.get(
            reverse('horizon:project:access_and_security:keypairs:create'))
        self.assertTemplateUsed(
            res, 'project/access_and_security/keypairs/create.html')

    def test_download_keypair_get(self):
        keypair_name = "keypair"
        context = {'keypair_name': keypair_name}
        url = reverse('horizon:project:access_and_security:keypairs:download',
                      kwargs={'keypair_name': keypair_name})
        res = self.client.get(url, context)
        self.assertTemplateUsed(
            res, 'project/access_and_security/keypairs/download.html')

    def test_generate_keypair_get(self):
        keypair = self.keypairs.first()
        keypair.private_key = "secret"

        self.mox.StubOutWithMock(api.nova, 'keypair_create')
        api.nova.keypair_create(IsA(http.HttpRequest),
                                keypair.name).AndReturn(keypair)
        self.mox.ReplayAll()

        context = {'keypair_name': keypair.name}
        url = reverse('horizon:project:access_and_security:keypairs:generate',
                      kwargs={'keypair_name': keypair.name})
        res = self.client.get(url, context)

        self.assertTrue(res.has_header('content-disposition'))

    def test_keypair_detail_get(self):
        keypair = self.keypairs.first()
        keypair.private_key = "secrete"

        self.mox.StubOutWithMock(api.nova, 'keypair_get')
        api.nova.keypair_get(IsA(http.HttpRequest),
                             keypair.name).AndReturn(keypair)
        self.mox.ReplayAll()

        context = {'keypair_name': keypair.name}
        url = reverse('horizon:project:access_and_security:keypairs:detail',
                      kwargs={'keypair_name': keypair.name})
        res = self.client.get(url, context)
        self.assertContains(res, "<dd>%s</dd>" % keypair.name, 1, 200)

    @test.create_stubs({api.nova: ("keypair_create", "keypair_delete")})
    def test_regenerate_keypair_get(self):
        keypair = self.keypairs.first()
        keypair.private_key = "secret"
        optional_param = "regenerate"
        api.nova.keypair_delete(IsA(http.HttpRequest), keypair.name)
        api.nova.keypair_create(IsA(http.HttpRequest),
                                keypair.name).AndReturn(keypair)
        self.mox.ReplayAll()
        url = reverse('horizon:project:access_and_security:keypairs:generate',
                      kwargs={'keypair_name': keypair.name,
                              'optional': optional_param})
        res = self.client.get(url)

        self.assertTrue(res.has_header('content-disposition'))

    @test.create_stubs({api.nova: ("keypair_import",)})
    def test_import_keypair(self):
        key1_name = "new_key_pair"
        public_key = "ssh-rsa ABCDEFGHIJKLMNOPQR\r\n" \
                     "STUVWXYZ1234567890\r" \
                     "XXYYZZ user@computer\n\n"
        api.nova.keypair_import(IsA(http.HttpRequest), key1_name,
                                public_key.replace("\r", "").replace("\n", ""))
        self.mox.ReplayAll()

        formData = {'method': 'ImportKeypair',
                    'name': key1_name,
                    'public_key': public_key}
        url = reverse('horizon:project:access_and_security:keypairs:import')
        res = self.client.post(url, formData)
        self.assertMessageCount(res, success=1)

    @test.create_stubs({api.nova: ("keypair_import",)})
    def test_import_keypair_invalid_key(self):
        key_name = "new_key_pair"
        public_key = "ABCDEF"

        api.nova.keypair_import(IsA(http.HttpRequest), key_name, public_key) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'method': 'ImportKeypair',
                    'name': key_name,
                    'public_key': public_key}
        url = reverse('horizon:project:access_and_security:keypairs:import')
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        msg = 'Unable to import key pair.'
        self.assertFormErrors(res, count=1, message=msg)

    def test_import_keypair_invalid_key_name(self):
        key_name = "invalid#key?name=!"
        public_key = "ABCDEF"

        formData = {'method': 'ImportKeypair',
                    'name': key_name,
                    'public_key': public_key}
        url = reverse('horizon:project:access_and_security:keypairs:import')
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        msg = six.text_type(KEYPAIR_ERROR_MESSAGES['invalid'])
        self.assertFormErrors(res, count=1, message=msg)

    @test.create_stubs({api.nova: ("keypair_create",)})
    def test_generate_keypair_exception(self):
        keypair = self.keypairs.first()

        api.nova.keypair_create(IsA(http.HttpRequest), keypair.name) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        context = {'keypair_name': keypair.name}
        url = reverse('horizon:project:access_and_security:keypairs:generate',
                      kwargs={'keypair_name': keypair.name})
        res = self.client.get(url, context)

        self.assertRedirectsNoFollow(
            res, reverse('horizon:project:access_and_security:index'))

    @test.create_stubs({api.nova: ("keypair_import",)})
    def test_import_keypair_with_regex_defined_name(self):
        key1_name = "new-key-pair with_regex"
        public_key = "ssh-rsa ABCDEFGHIJKLMNOPQR\r\n" \
                     "STUVWXYZ1234567890\r" \
                     "XXYYZZ user@computer\n\n"
        api.nova.keypair_import(IsA(http.HttpRequest), key1_name,
                                public_key.replace("\r", "").replace("\n", ""))
        self.mox.ReplayAll()

        formData = {'method': 'ImportKeypair',
                    'name': key1_name,
                    'public_key': public_key}
        url = reverse('horizon:project:access_and_security:keypairs:import')
        res = self.client.post(url, formData)
        self.assertMessageCount(res, success=1)

    @test.create_stubs({api.nova: ("keypair_create",)})
    def test_create_keypair_with_regex_name_get(self):
        keypair = self.keypairs.first()
        keypair.name = "key-space pair-regex_name-0123456789"
        keypair.private_key = "secret"

        api.nova.keypair_create(IsA(http.HttpRequest),
                                keypair.name).AndReturn(keypair)
        self.mox.ReplayAll()

        context = {'keypair_name': keypair.name}
        url = reverse('horizon:project:access_and_security:keypairs:generate',
                      kwargs={'keypair_name': keypair.name})
        res = self.client.get(url, context)

        self.assertTrue(res.has_header('content-disposition'))

    def test_download_with_regex_name_get(self):
        keypair_name = "key pair-regex_name-0123456789"
        context = {'keypair_name': keypair_name}
        url = reverse('horizon:project:access_and_security:keypairs:download',
                      kwargs={'keypair_name': keypair_name})
        res = self.client.get(url, context)
        self.assertTemplateUsed(
            res, 'project/access_and_security/keypairs/download.html')

    @test.create_stubs({api.nova: ('keypair_list',)})
    def test_create_duplicate_keypair(self):
        keypair_name = self.keypairs.first().name

        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        self.mox.ReplayAll()

        form = CreateKeypair(self.request, data={'name': keypair_name})
        self.assertFalse(form.is_valid())
        self.assertIn('The name is already in use.',
                      form.errors['name'][0])
