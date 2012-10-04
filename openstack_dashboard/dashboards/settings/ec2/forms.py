# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Openstack, LLC
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

import logging
import tempfile
import zipfile
from contextlib import closing

from django import http
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class DownloadX509Credentials(forms.SelfHandlingForm):
    tenant = forms.ChoiceField(label=_("Select a Project"))

    def __init__(self, request, *args, **kwargs):
        super(DownloadX509Credentials, self).__init__(request, *args, **kwargs)
        # Populate tenant choices
        tenant_choices = []
        try:
            tenant_list = api.keystone.tenant_list(request)
        except:
            tenant_list = []
            exceptions.handle(request, _("Unable to retrieve tenant list."))

        for tenant in tenant_list:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        if not tenant_choices:
            self.fields['tenant'].choices = [('', 'No Available Tenants')]
        else:
            self.fields['tenant'].choices = tenant_choices

    def handle(self, request, data):
        def find_or_create_access_keys(request, tenant_id):
            keys = api.keystone.list_ec2_credentials(request, request.user.id)
            for key in keys:
                if key.tenant_id == tenant_id:
                    return key
            return api.keystone.create_ec2_credentials(request,
                                                       request.user.id,
                                                       tenant_id)
        try:
            # NOTE(jakedahn): Keystone errors unless we specifically scope
            #                 the token to tenant before making the call.
            api.keystone.token_create_scoped(request,
                                             data.get('tenant'),
                                             request.user.token.id)
            credentials = api.nova.get_x509_credentials(request)
            cacert = api.nova.get_x509_root_certificate(request)
            keys = find_or_create_access_keys(request, data.get('tenant'))
            context = {'ec2_access_key': keys.access,
                       'ec2_secret_key': keys.secret,
                       'ec2_endpoint': api.url_for(request,
                                                   'ec2',
                                                   endpoint_type='publicURL')}
            try:
                s3_endpoint = api.url_for(request,
                                          's3',
                                          endpoint_type='publicURL')
            except exceptions.ServiceCatalogException:
                s3_endpoint = None
            context['s3_endpoint'] = s3_endpoint
        except:
            exceptions.handle(request,
                              _('Unable to fetch EC2 credentials.'),
                              redirect=request.build_absolute_uri())

        try:
            temp_zip = tempfile.NamedTemporaryFile(delete=True)
            with closing(zipfile.ZipFile(temp_zip.name, mode='w')) as archive:
                archive.writestr('pk.pem', credentials.private_key)
                archive.writestr('cert.pem', credentials.data)
                archive.writestr('cacert.pem', cacert.data)
                archive.writestr('ec2rc.sh', render_to_string(
                                 'settings/ec2/ec2rc.sh.template', context))
        except:
            exceptions.handle(request,
                              _('Error writing zipfile: %(exc)s'),
                              redirect=request.build_absolute_uri())

        response = http.HttpResponse(mimetype='application/zip')
        response.write(temp_zip.read())
        response['Content-Disposition'] = 'attachment; \
                                           filename=%s-x509.zip' \
                                           % data.get('tenant')
        response['Content-Length'] = temp_zip.tell()
        return response
