# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security.\
    keypairs.forms import KEYPAIR_ERROR_MESSAGES
from openstack_dashboard.test import helpers as test


INDEX_VIEW_URL = reverse('horizon:project:access_and_security:index')


class KeyPairViewTests(test.TestCase):
    def test_delete_keypair(self):
        keypair = self.keypairs.first()

        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_delete')

        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.keypair_delete(IsA(http.HttpRequest), keypair.name)
        self.mox.ReplayAll()

        formData = {'action': 'keypairs__delete__%s' % keypair.name}
        res = self.client.post(INDEX_VIEW_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_VIEW_URL)

    def test_delete_keypair_exception(self):
        keypair = self.keypairs.first()
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_delete')

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
        self.assertTemplateUsed(res,
                        'project/access_and_security/keypairs/create.html')

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

    def test_import_keypair_invalid_key(self):
        key_name = "new_key_pair"
        public_key = "ABCDEF"

        self.mox.StubOutWithMock(api.nova, 'keypair_import')
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
        key_name = "new key pair"
        public_key = "ABCDEF"

        formData = {'method': 'ImportKeypair',
                    'name': key_name,
                    'public_key': public_key}
        url = reverse('horizon:project:access_and_security:keypairs:import')
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        msg = unicode(KEYPAIR_ERROR_MESSAGES['invalid'])
        self.assertFormErrors(res, count=1, message=msg)

    def test_generate_keypair_exception(self):
        keypair = self.keypairs.first()

        self.mox.StubOutWithMock(api.nova, 'keypair_create')
        api.nova.keypair_create(IsA(http.HttpRequest), keypair.name) \
                        .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        context = {'keypair_name': keypair.name}
        url = reverse('horizon:project:access_and_security:keypairs:generate',
                      kwargs={'keypair_name': keypair.name})
        res = self.client.get(url, context)

        self.assertRedirectsNoFollow(
            res, reverse('horizon:project:access_and_security:index'))
