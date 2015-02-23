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

"""
Views for managing keypairs.
"""
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.template.defaultfilters import slugify  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View  # noqa

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import views

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.access_and_security.keypairs \
    import forms as project_forms


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateKeypair
    form_id = "create_keypair_form"
    modal_header = _("Create Key Pair")
    template_name = 'project/access_and_security/keypairs/create.html'
    submit_label = _("Create Key Pair")
    submit_url = reverse_lazy(
        "horizon:project:access_and_security:keypairs:create")
    success_url = 'horizon:project:access_and_security:keypairs:download'
    page_title = _("Create Key Pair")

    def get_success_url(self):
        return reverse(self.success_url,
                       kwargs={"keypair_name": self.request.POST['name']})


class ImportView(forms.ModalFormView):
    form_class = project_forms.ImportKeypair
    form_id = "import_keypair_form"
    modal_header = _("Import Key Pair")
    template_name = 'project/access_and_security/keypairs/import.html'
    submit_label = _("Import Key Pair")
    submit_url = reverse_lazy(
        "horizon:project:access_and_security:keypairs:import")
    success_url = reverse_lazy('horizon:project:access_and_security:index')
    page_title = _("Import Key Pair")

    def get_object_id(self, keypair):
        return keypair.name


class DetailView(views.HorizonTemplateView):
    template_name = 'project/access_and_security/keypairs/detail.html'
    page_title = _("Key Pair Details")

    @memoized.memoized_method
    def _get_data(self):
        try:
            keypair = api.nova.keypair_get(self.request,
                                           self.kwargs['keypair_name'])
        except Exception:
            redirect = reverse('horizon:project:access_and_security:index')
            msg = _('Unable to retrieve details for keypair "%s".')\
                % (self.kwargs['keypair_name'])
            exceptions.handle(self.request, msg,
                              redirect=redirect)
        return keypair

    def get_context_data(self, **kwargs):
        """Gets the context data for keypair."""
        context = super(DetailView, self).get_context_data(**kwargs)
        context['keypair'] = self._get_data()
        return context


class DownloadView(views.HorizonTemplateView):
    template_name = 'project/access_and_security/keypairs/download.html'
    page_title = _("Download Key Pair")

    def get_context_data(self, keypair_name=None):
        return {'keypair_name': keypair_name}


class GenerateView(View):
    def get(self, request, keypair_name=None, optional=None):
        try:
            if optional == "regenerate":
                api.nova.keypair_delete(request, keypair_name)

            keypair = api.nova.keypair_create(request, keypair_name)
        except Exception:
            redirect = reverse('horizon:project:access_and_security:index')
            exceptions.handle(self.request,
                              _('Unable to create key pair: %(exc)s'),
                              redirect=redirect)

        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = ('attachment; filename=%s.pem'
                                           % slugify(keypair.name))
        response.write(keypair.private_key)
        response['Content-Length'] = str(len(response.content))
        return response
