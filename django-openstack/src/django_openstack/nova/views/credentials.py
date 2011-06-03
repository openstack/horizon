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
Views for downloading X509 credentials. Useful when using an invitation
style system for configuring first time users.
"""

from django import http
from django.conf import settings
from django.shortcuts import render_to_response
from django_openstack import log as logging
from django_openstack import models


LOG = logging.getLogger('django_openstack.nova')


def authorize_credentials(request, auth_token):
    """Sends X509 credentials to user if their auth token is valid."""
    auth_token = auth_token.lower()
    credentials = models.CredentialsAuthorization.get_by_token(auth_token)

    # NOTE(devcamcar): If nothing returned, then token was bad or has expired.
    if not credentials:
        LOG.info("Credentials token bad or expired for user %s" %
                 str(request.user))
        return render_to_response(
                'django_openstack/nova/credentials/expired.html')

    response = http.HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = \
        'attachment; filename=%s-%s-%s-x509.zip' % \
        (settings.SITE_NAME, credentials.project, credentials.username)
    response.write(credentials.get_zip())

    return response
