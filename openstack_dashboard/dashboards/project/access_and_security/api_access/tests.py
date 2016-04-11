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
from django.test.utils import override_settings  # noqa

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:access_and_security:index')
API_URL = "horizon:project:access_and_security:api_access"
EC2_URL = reverse(API_URL + ":ec2")
OPENRC_URL = reverse(API_URL + ":openrc")
OPENRCV2_URL = reverse(API_URL + ":openrcv2")
CREDS_URL = reverse(API_URL + ":view_credentials")
RECREATE_CREDS_URL = reverse(API_URL + ":recreate_credentials")


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

    def test_openrcv2_credentials(self):
        res = self.client.get(OPENRCV2_URL)
        self.assertEqual(res.status_code, 200)
        openrc = 'project/access_and_security/api_access/openrc_v2.sh.template'
        self.assertTemplateUsed(res, openrc)
        name = 'export OS_USERNAME="{}"'.format(self.request.user.username)
        t_id = 'export OS_TENANT_ID={}'.format(self.request.user.tenant_id)
        domain = 'export OS_USER_DOMAIN_NAME="{}"'.format(
            self.request.user.user_domain_name)
        self.assertIn(name.encode('utf-8'), res.content)
        self.assertIn(t_id.encode('utf-8'), res.content)
        # domain content should not be present for v2
        self.assertNotIn(domain.encode('utf-8'), res.content)

    @override_settings(OPENSTACK_API_VERSIONS={"identity": 3})
    def test_openrc_credentials(self):
        res = self.client.get(OPENRC_URL)
        self.assertEqual(res.status_code, 200)
        openrc = 'project/access_and_security/api_access/openrc.sh.template'
        self.assertTemplateUsed(res, openrc)
        name = 'export OS_USERNAME="{}"'.format(self.request.user.username)
        p_id = 'export OS_PROJECT_ID={}'.format(self.request.user.tenant_id)
        domain = 'export OS_USER_DOMAIN_NAME="{}"'.format(
            self.request.user.user_domain_name)
        self.assertIn(name.encode('utf-8'), res.content)
        self.assertIn(p_id.encode('utf-8'), res.content)
        self.assertIn(domain.encode('utf-8'), res.content)

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

    @test.create_stubs({api.keystone: ("list_ec2_credentials",
                                       "create_ec2_credentials",
                                       "delete_user_ec2_credentials",)})
    def _test_recreate_user_credentials(self, exists_credentials=True):
        old_creds = self.ec2.list() if exists_credentials else []
        new_creds = self.ec2.first()
        api.keystone.list_ec2_credentials(
            IsA(HttpRequest),
            self.user.id).AndReturn(old_creds)
        if exists_credentials:
            api.keystone.delete_user_ec2_credentials(
                IsA(HttpRequest),
                self.user.id,
                old_creds[0].access).AndReturn([])
        api.keystone.create_ec2_credentials(
            IsA(HttpRequest),
            self.user.id,
            self.tenant.id).AndReturn(new_creds)

        self.mox.ReplayAll()

        res_get = self.client.get(RECREATE_CREDS_URL)
        self.assertEqual(res_get.status_code, 200)
        credentials = \
            'project/access_and_security/api_access/recreate_credentials.html'
        self.assertTemplateUsed(res_get, credentials)

        res_post = self.client.post(RECREATE_CREDS_URL)
        self.assertNoFormErrors(res_post)
        self.assertRedirectsNoFollow(res_post, INDEX_URL)

    def test_recreate_user_credentials(self):
        self._test_recreate_user_credentials()

    def test_recreate_user_credentials_with_no_existing_creds(self):
        self._test_recreate_user_credentials(exists_credentials=False)
