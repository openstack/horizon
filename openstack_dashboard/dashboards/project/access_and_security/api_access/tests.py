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


EC2_URL = reverse("horizon:project:access_and_security:api_access:ec2")


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
