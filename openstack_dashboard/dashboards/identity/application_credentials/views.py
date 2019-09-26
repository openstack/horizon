# Copyright 2018 SUSE Linux GmbH
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

from django.conf import settings
from django import http
from django.template.loader import render_to_string
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import views

from openstack_dashboard import api
from openstack_dashboard.utils import settings as setting_utils

from openstack_dashboard.dashboards.identity.application_credentials \
    import forms as project_forms
from openstack_dashboard.dashboards.identity.application_credentials \
    import tables as project_tables

INDEX_URL = "horizon:identity:application_credentials:index"


class IndexView(tables.DataTableView):
    table_class = project_tables.ApplicationCredentialsTable
    template_name = 'identity/application_credentials/index.html'
    page_title = _("Application Credentials")

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def get_data(self):
        app_creds = []
        filters = self.get_filters()

        self._needs_filter_first = False

        # If filter_first is set and if there are not other filters
        # selected, then search criteria must be provided
        # and return an empty list
        if (setting_utils.get_dict_config(
                'FILTER_DATA_FIRST',
                'identity.application_credentials') and not filters):
            self._needs_filter_first = True
            return app_creds

        try:
            app_creds = api.keystone.application_credential_list(
                self.request, filters=filters)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve application credential list.'))

        return app_creds


class CreateView(forms.ModalFormView):
    template_name = 'identity/application_credentials/create.html'
    form_id = 'create_application_credential_form'
    form_class = project_forms.CreateApplicationCredentialForm
    submit_label = _("Create Application Credential")
    submit_url = reverse_lazy(
        'horizon:identity:application_credentials:create')
    success_url = reverse_lazy(
        'horizon:identity:application_credentials:success')
    page_title = _("Create Application Credential")

    def get_form_kwargs(self):
        kwargs = super(CreateView, self).get_form_kwargs()
        kwargs['next_view'] = CreateSuccessfulView
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['kubeconfig_enabled'] = settings.KUBECONFIG_ENABLED
        return context


class CreateSuccessfulView(forms.ModalFormView):
    template_name = 'identity/application_credentials/success.html'
    page_title = _("Your Application Credential")
    form_class = project_forms.CreateSuccessfulForm
    model_id = "create_application_credential_successful_modal"
    success_url = reverse_lazy(
        'horizon:identity:application_credentials:index')
    cancel_label = _("Close")
    download_openrc_label = _("Download openrc file")
    download_clouds_yaml_label = _("Download clouds.yaml")
    download_kubeconfig_label = _("Download kubeconfig file")

    def get_context_data(self, **kwargs):
        context = super(CreateSuccessfulView, self).get_context_data(**kwargs)
        context['download_openrc_label'] = self.download_openrc_label
        context['download_clouds_yaml_label'] = self.download_clouds_yaml_label
        context['download_kubeconfig_label'] = self.download_kubeconfig_label
        context['download_openrc_url'] = reverse(
            'horizon:identity:application_credentials:download_openrc')
        context['download_clouds_yaml_url'] = reverse(
            'horizon:identity:application_credentials:download_clouds_yaml')
        if settings.KUBECONFIG_ENABLED:
            context['download_kubeconfig_url'] = reverse(
                'horizon:identity:application_credentials:download_kubeconfig')
        return context

    def get_initial(self):
        app_cred = self.request.session['application_credential']
        return {
            'app_cred_id': app_cred['id'],
            'app_cred_name': app_cred['name'],
            'app_cred_secret': app_cred['secret']
        }


def _get_context(request):
    auth_url = api.base.url_for(request,
                                'identity',
                                endpoint_type='publicURL')
    interface = 'public'
    region = getattr(request.user, 'services_region', '')
    app_cred = request.session['application_credential']
    context = {
        'auth_url': auth_url,
        'interface': interface,
        'region': region,
        'user': request.user,
        'application_credential_id': app_cred['id'],
        'application_credential_name': app_cred['name'],
        'application_credential_secret': app_cred['secret'],
        'kubernetes_namespace': app_cred['kubernetes_namespace'],
        'kubernetes_url': settings.KUBECONFIG_KUBERNETES_URL,
        'kubernetes_certificate_authority_data':
            settings.KUBECONFIG_CERTIFICATE_AUTHORITY_DATA}
    return context


def _render_attachment(filename, template, context, request):
    content = render_to_string(template, context, request=request)
    disposition = 'attachment; filename="%s"' % filename
    response = http.HttpResponse(content, content_type="text/plain")
    response['Content-Disposition'] = disposition.encode('utf-8')
    response['Content-Length'] = str(len(response.content))
    return response


def download_rc_file(request):
    context = _get_context(request)
    template = 'identity/application_credentials/openrc.sh.template'
    filename = 'app-cred-%s-openrc.sh' % context['application_credential_name']
    response = _render_attachment(filename, template, context, request)
    return response


def download_clouds_yaml_file(request):
    context = _get_context(request)
    context['cloud_name'] = getattr(
        settings, "OPENSTACK_CLOUDS_YAML_NAME", 'openstack')
    context['profile'] = getattr(
        settings, "OPENSTACK_CLOUDS_YAML_PROFILE", None)
    context['regions'] = [
        region_tuple[1] for region_tuple in getattr(
            settings, "AVAILABLE_REGIONS", [])
    ]
    template = 'identity/application_credentials/clouds.yaml.template'
    filename = 'clouds.yaml'
    return _render_attachment(filename, template, context, request)


def download_kubeconfig_file(request):
    context = _get_context(request)
    template = 'identity/application_credentials/kubeconfig.template'
    filename = 'app-cred-%s-kubeconfig' % context['application_credential_name']
    response = _render_attachment(filename, template, context, request)
    return response


class DetailView(views.HorizonTemplateView):
    template_name = 'identity/application_credentials/detail.html'
    page_title = "{{ application_credential.name }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        app_cred = self.get_data()
        table = project_tables.ApplicationCredentialsTable(self.request)
        context["application_credential"] = app_cred
        context["url"] = reverse(INDEX_URL)
        context["actions"] = table.render_row_actions(app_cred)

        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            app_cred_id = self.kwargs['application_credential_id']
            app_cred = api.keystone.application_credential_get(self.request,
                                                               app_cred_id)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve application credential details.'),
                redirect=reverse(INDEX_URL))
        return app_cred
