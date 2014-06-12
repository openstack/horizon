# Copyright 2012 Nebula Inc
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
from django.http import HttpRequest  # noqa

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


API_URL = "horizon:project:access_and_security:api_access"
EC2_URL = reverse(API_URL + ":ec2")
OPENRC_URL = reverse(API_URL + ":openrc")
CREDS_URL = reverse(API_URL + ":view_credentials")


class APIAccessTests(test.TestCase):
    def test_ec2_download_view(self):
        creds = self.ec2.first()
        cert = self.certs.first()

        self.mox.StubOutWithMock(api.keystone, "list_ec2_credentials")
        self.mox.StubOutWithMock(api.nova, "get_x509_credentials")
        self.mox.StubOutWithMock(api.nova, "get_x509_root_certificate")
        self.mox.StubOutWithMock(api.keystone, "create_ec2_credentials")

        api.keystone.list_ec2_credentials(IsA(HttpRequest), self.user.id) \
                    .AndReturn([])
        api.nova.get_x509_credentials(IsA(HttpRequest)).AndReturn(cert)
        api.nova.get_x509_root_certificate(IsA(HttpRequest)) \
                .AndReturn(cert)
        api.keystone.create_ec2_credentials(IsA(HttpRequest),
                                            self.user.id,
                                            self.tenant.id).AndReturn(creds)
        self.mox.ReplayAll()

        res = self.client.get(EC2_URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['content-type'], 'application/zip')

    def test_openrc_credentials(self):
        res = self.client.get(OPENRC_URL)
        self.assertEqual(res.status_code, 200)
        openrc = 'project/access_and_security/api_access/openrc.sh.template'
        self.assertTemplateUsed(res, openrc)
        name = 'export OS_USERNAME="{}"'.format(self.request.user.username)
        id = 'export OS_TENANT_ID={}'.format(self.request.user.tenant_id)
        self.assertTrue(name in res.content)
        self.assertTrue(id in res.content)

    @test.create_stubs({api.keystone: ("list_ec2_credentials",)})
    def test_credential_api(self):
        certs = self.ec2.list()
        api.keystone.list_ec2_credentials(IsA(HttpRequest), self.user.id) \
            .AndReturn(certs)

        self.mox.ReplayAll()

        res = self.client.get(CREDS_URL)
        self.assertEqual(res.status_code, 200)
        credentials = 'project/access_and_security/api_access/credentials.html'
        self.assertTemplateUsed(res, credentials)
        self.assertEqual(self.user.id, res.context['openrc_creds']['user'].id)
        self.assertEqual(certs[0].access,
                         res.context['ec2_creds']['ec2_access_key'])
