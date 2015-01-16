# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.utils.translation import ugettext_lazy as _
import django.views

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs

from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project.data_processing.utils \
    import helpers

import openstack_dashboard.dashboards.project.data_processing. \
    job_binaries.forms as job_binary_forms
from openstack_dashboard.dashboards.project.data_processing.job_binaries \
    import tables as jb_tables
import openstack_dashboard.dashboards.project.data_processing.job_binaries. \
    tabs as _tabs


LOG = logging.getLogger(__name__)


class JobBinariesView(tables.DataTableView):
    table_class = jb_tables.JobBinariesTable
    template_name = 'project/data_processing.job_binaries/job_binaries.html'
    page_title = _("Job Binaries")

    def get_data(self):
        try:
            job_binaries = saharaclient.job_binary_list(self.request)
        except Exception:
            job_binaries = []
            exceptions.handle(self.request,
                              _("Unable to fetch job binary list."))
        return job_binaries


class CreateJobBinaryView(forms.ModalFormView):
    form_class = job_binary_forms.JobBinaryCreateForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.job_binaries:index')
    classes = ("ajax-modal",)
    template_name = "project/data_processing.job_binaries/create.html"
    page_title = _("Create Job Binary")

    def get_success_url(self):
        hlps = helpers.Helpers(self.request)
        if hlps.is_from_guide():
            self.success_url = reverse_lazy(
                "horizon:project:data_processing.wizard:jobex_guide")
        return self.success_url


class JobBinaryDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobBinaryDetailsTabs
    template_name = 'project/data_processing.job_binaries/details.html'
    page_title = _("Job Binary Details")

    def get_context_data(self, **kwargs):
        context = super(JobBinaryDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class DownloadJobBinaryView(django.views.generic.View):
    def get(self, request, job_binary_id=None):
        try:
            jb = saharaclient.job_binary_get(request, job_binary_id)
            data = saharaclient.job_binary_get_file(request, job_binary_id)
        except Exception:
            redirect = reverse(
                'horizon:project:data_processing.job_binaries:index')
            exceptions.handle(self.request,
                              _('Unable to fetch job binary: %(exc)s'),
                              redirect=redirect)
        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = (
            'attachment; filename="%s"' % jb.name)
        response.write(data)
        response['Content-Length'] = str(len(data))
        return response
