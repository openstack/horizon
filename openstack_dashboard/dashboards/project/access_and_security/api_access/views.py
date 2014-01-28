# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

from contextlib import closing  # noqa
import logging
import tempfile
import zipfile

from django import http
from django import shortcuts
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


def download_ec2_bundle(request):
    tenant_id = request.user.tenant_id
    tenant_name = request.user.tenant_name

    # Gather or create our EC2 credentials
    try:
        credentials = api.nova.get_x509_credentials(request)
        cacert = api.nova.get_x509_root_certificate(request)

        all_keys = api.keystone.list_ec2_credentials(request,
                                                     request.user.id)
        keys = None
        for key in all_keys:
            if key.tenant_id == tenant_id:
                keys = key
        if keys is None:
            keys = api.keystone.create_ec2_credentials(request,
                                                       request.user.id,
                                                       tenant_id)
    except Exception:
        exceptions.handle(request,
                          _('Unable to fetch EC2 credentials.'),
                          redirect=request.build_absolute_uri())

    # Get our S3 endpoint if it exists
    try:
        s3_endpoint = api.base.url_for(request,
                                       's3',
                                       endpoint_type='publicURL')
    except exceptions.ServiceCatalogException:
        s3_endpoint = None

    # Get our EC2 endpoint (it should exist since we just got creds for it)
    try:
        ec2_endpoint = api.base.url_for(request,
                                        'ec2',
                                        endpoint_type='publicURL')
    except exceptions.ServiceCatalogException:
        ec2_endpoint = None

    # Build the context
    context = {'ec2_access_key': keys.access,
               'ec2_secret_key': keys.secret,
               'ec2_endpoint': ec2_endpoint,
               's3_endpoint': s3_endpoint}

    # Create our file bundle
    template = 'project/access_and_security/api_access/ec2rc.sh.template'
    try:
        temp_zip = tempfile.NamedTemporaryFile(delete=True)
        with closing(zipfile.ZipFile(temp_zip.name, mode='w')) as archive:
            archive.writestr('pk.pem', credentials.private_key)
            archive.writestr('cert.pem', credentials.data)
            archive.writestr('cacert.pem', cacert.data)
            archive.writestr('ec2rc.sh', render_to_string(template, context))
    except Exception:
        exceptions.handle(request,
                          _('Error writing zipfile: %(exc)s'),
                          redirect=request.build_absolute_uri())

    # Send it back
    response = http.HttpResponse(content_type='application/zip')
    response.write(temp_zip.read())
    response['Content-Disposition'] = ('attachment; '
                                       'filename="%s-x509.zip"'
                                       % tenant_name)
    response['Content-Length'] = temp_zip.tell()
    return response


def download_rc_file(request):
    tenant_id = request.user.tenant_id
    tenant_name = request.user.tenant_name

    template = 'project/access_and_security/api_access/openrc.sh.template'

    try:
        keystone_url = api.base.url_for(request,
                                        'identity',
                                        endpoint_type='publicURL')

        context = {'user': request.user,
                   'auth_url': keystone_url,
                   'tenant_id': tenant_id,
                   'tenant_name': tenant_name}

        response = shortcuts.render(request,
                                    template,
                                    context,
                                    content_type="text/plain")
        response['Content-Disposition'] = ('attachment; '
                                           'filename="%s-openrc.sh"'
                                           % tenant_name)
        response['Content-Length'] = str(len(response.content))
        return response

    except Exception as e:
        LOG.exception("Exception in DownloadOpenRCForm.")
        messages.error(request, _('Error Downloading RC File: %s') % e)
        return shortcuts.redirect(request.build_absolute_uri())
