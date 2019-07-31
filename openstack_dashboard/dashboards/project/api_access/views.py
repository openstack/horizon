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

from contextlib import closing
import logging
import tempfile
import zipfile

from django.conf import settings
from django import http
from django import shortcuts
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.api_access \
    import forms as api_access_forms
from openstack_dashboard.dashboards.project.api_access \
    import tables as api_access_tables

LOG = logging.getLogger(__name__)


def _get_ec2_credentials(request):
    tenant_id = request.user.tenant_id
    all_keys = api.keystone.list_ec2_credentials(request,
                                                 request.user.id)

    key = next((x for x in all_keys if x.tenant_id == tenant_id), None)
    if not key:
        key = api.keystone.create_ec2_credentials(request,
                                                  request.user.id,
                                                  tenant_id)
    try:
        s3_endpoint = api.base.url_for(request,
                                       's3',
                                       endpoint_type='publicURL')
    except exceptions.ServiceCatalogException:
        s3_endpoint = None

    try:
        ec2_endpoint = api.base.url_for(request,
                                        'ec2',
                                        endpoint_type='publicURL')
    except exceptions.ServiceCatalogException:
        ec2_endpoint = None

    return {'ec2_access_key': key.access,
            'ec2_secret_key': key.secret,
            'ec2_endpoint': ec2_endpoint,
            's3_endpoint': s3_endpoint}


def _get_openrc_credentials(request):
    keystone_url = api.base.url_for(request,
                                    'identity',
                                    endpoint_type='publicURL')
    return {
        'tenant_id': request.user.tenant_id,
        'tenant_name': request.user.tenant_name,
        'auth_url': keystone_url,
        'user': request.user,
        'interface': 'public',
        'os_endpoint_type': 'publicURL',
        'region': getattr(request.user, 'services_region') or "",
    }


# TODO(stephenfin): Migrate to CBV
def download_ec2_bundle(request):
    tenant_name = request.user.tenant_name

    # Gather or create our EC2 credentials
    try:
        context = _get_ec2_credentials(request)
    except Exception:
        exceptions.handle(request,
                          _('Unable to fetch EC2 credentials.'),
                          redirect=request.build_absolute_uri())

    # Create our file bundle
    template = 'project/api_access/ec2rc.sh.template'
    try:
        temp_zip = tempfile.NamedTemporaryFile(delete=True)
        with closing(zipfile.ZipFile(temp_zip.name, mode='w')) as archive:
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


# TODO(stephenfin): Migrate to CBV
def download_rc_file(request):
    template = settings.OPENRC_CUSTOM_TEMPLATE

    context = _get_openrc_credentials(request)
    # make v3 specific changes
    context['user_domain_name'] = request.user.user_domain_name
    try:
        project_domain_id = request.user.token.project['domain_id']
    except KeyError:
        project_domain_id = ''
    context['project_domain_id'] = project_domain_id
    context['os_identity_api_version'] = 3
    context['os_auth_version'] = 3
    return _download_rc_file_for_template(request, context, template)


# TODO(stephenfin): Migrate to CBV
def download_clouds_yaml_file(request):
    template = settings.OPENSTACK_CLOUDS_YAML_CUSTOM_TEMPLATE

    context = _get_openrc_credentials(request)
    context['cloud_name'] = settings.OPENSTACK_CLOUDS_YAML_NAME
    context['profile'] = settings.OPENSTACK_CLOUDS_YAML_PROFILE
    context['regions'] = [
        region_tuple[1] for region_tuple in settings.AVAILABLE_REGIONS
    ]

    context['user_domain_name'] = request.user.user_domain_name
    context['os_identity_api_version'] = 3
    context['os_auth_version'] = 3

    return _download_rc_file_for_template(request, context, template,
                                          'clouds.yaml')


def _download_rc_file_for_template(request, context, template, filename=None):
    try:
        content = render_to_string(template, context, request=request)
        content = '\n'.join([line for line in content.split('\n')
                             if line.strip()])
        response = http.HttpResponse(content, content_type="text/plain")

        if not filename:
            filename = '%s-openrc.sh' % context['tenant_name']
        disposition = 'attachment; filename="%s"' % filename
        response['Content-Disposition'] = disposition.encode('utf-8')
        response['Content-Length'] = str(len(response.content))
        return response

    except Exception as e:
        LOG.exception("Exception in DownloadOpenRCForm.")
        messages.error(request, _('Error Downloading RC File: %s') % e)
        return shortcuts.redirect(request.build_absolute_uri())


class CredentialsView(forms.ModalFormMixin, views.HorizonTemplateView):
    template_name = 'project/api_access/credentials.html'
    page_title = _("User Credentials Details")

    def get_context_data(self, **kwargs):
        context = super(CredentialsView, self).get_context_data(**kwargs)
        try:
            context['openrc_creds'] = _get_openrc_credentials(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to get openrc credentials'))
        if api.base.is_service_enabled(self.request, 'ec2'):
            try:
                context['ec2_creds'] = _get_ec2_credentials(self.request)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to get EC2 credentials'))
        return context


class RecreateCredentialsView(forms.ModalFormView):
    form_class = api_access_forms.RecreateCredentials
    form_id = "recreate_credentials"
    page_title = _("Recreate EC2 Credentials")
    template_name = \
        'project/api_access/recreate_credentials.html'
    submit_label = _("Recreate EC2 Credentials")
    submit_url = reverse_lazy(
        "horizon:project:api_access:recreate_credentials")
    success_url = reverse_lazy('horizon:project:api_access:index')


class IndexView(tables.DataTableView):
    table_class = api_access_tables.EndpointsTable
    page_title = _("API Access")

    def get_data(self):
        services = []
        for i, service in enumerate(self.request.user.service_catalog):
            service['id'] = i
            services.append(
                api.keystone.Service(service,
                                     self.request.user.services_region))
        return sorted(services, key=lambda s: s.type)
