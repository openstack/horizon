# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
Unit tests for credential views.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django_openstack import models
from django_openstack.nova.tests.base import BaseViewTests


class CredentialViewTests(BaseViewTests):
    def test_download_expired_credentials(self):
        auth_token = 'expired'
        self.mox.StubOutWithMock(models.CredentialsAuthorization,
                                 'get_by_token')
        models.CredentialsAuthorization.get_by_token(auth_token) \
                                       .AndReturn(None)
        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_credentials_authorize',
                                      args=[auth_token]))
        self.assertTemplateUsed(res,
                'django_openstack/nova/credentials/expired.html')

        self.mox.VerifyAll()

    def test_download_good_credentials(self):
        auth_token = 'good'

        creds = models.CredentialsAuthorization()
        creds.username = 'test'
        creds.project = 'test'
        creds.auth_token = auth_token

        self.mox.StubOutWithMock(models.CredentialsAuthorization,
                                 'get_by_token')
        self.mox.StubOutWithMock(creds, 'get_zip')
        models.CredentialsAuthorization.get_by_token(auth_token) \
                                       .AndReturn(creds)
        creds.get_zip().AndReturn('zip')

        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_credentials_authorize',
                                      args=[auth_token]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Disposition'],
                         'attachment; filename=%s-test-test-x509.zip' %
                         settings.SITE_NAME)
        self.assertContains(res, 'zip')

        self.mox.VerifyAll()
