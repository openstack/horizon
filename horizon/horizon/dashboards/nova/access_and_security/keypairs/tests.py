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

from django import http
from django.core.urlresolvers import reverse
from mox import IsA
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import test


INDEX_VIEW_URL = reverse('horizon:nova:access_and_security:index')


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
        exc = novaclient_exceptions.ClientException('clientException')
        api.nova.keypair_delete(IsA(http.HttpRequest), keypair.name) \
                .AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'action': 'keypairs__delete__%s' % keypair.name}
        res = self.client.post(INDEX_VIEW_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_VIEW_URL)

    def test_create_keypair_get(self):
        res = self.client.get(
                reverse('horizon:nova:access_and_security:keypairs:create'))
        self.assertTemplateUsed(res,
                               'nova/access_and_security/keypairs/create.html')

    def test_create_keypair_post(self):
        keypair = self.keypairs.first()
        keypair.private_key = "secret"

        self.mox.StubOutWithMock(api, 'keypair_create')
        api.keypair_create(IsA(http.HttpRequest),
                           keypair.name).AndReturn(keypair)
        self.mox.ReplayAll()

        formData = {'method': 'CreateKeypair',
                    'name': keypair.name}
        url = reverse('horizon:nova:access_and_security:keypairs:create')
        res = self.client.post(url, formData)
        self.assertTrue(res.has_header('Content-Disposition'))

    def test_create_keypair_exception(self):
        keypair = self.keypairs.first()
        exc = novaclient_exceptions.ClientException('clientException')
        self.mox.StubOutWithMock(api, 'keypair_create')
        api.keypair_create(IsA(http.HttpRequest), keypair.name).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'method': 'CreateKeypair',
                    'name': keypair.name}
        url = reverse('horizon:nova:access_and_security:keypairs:create')
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)
