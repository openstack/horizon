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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon import workflows

from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates import forms as cluster_forms
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.tables as ct_tables
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.tabs as _tabs
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.workflows.copy as copy_flow
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class ClusterTemplatesView(tables.DataTableView):
    table_class = ct_tables.ClusterTemplatesTable
    template_name = (
        'project/data_processing.cluster_templates/cluster_templates.html')
    page_title = _("Cluster Templates")

    def get_data(self):
        try:
            search_opts = {}
            filter = self.get_server_filter_info(self.request)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            cluster_templates = saharaclient.cluster_template_list(
                self.request, search_opts)
        except Exception:
            cluster_templates = []
            exceptions.handle(self.request,
                              _("Unable to fetch cluster template list"))
        return cluster_templates


class ClusterTemplateDetailsView(tabs.TabView):
    tab_group_class = _tabs.ClusterTemplateDetailsTabs
    template_name = 'project/data_processing.cluster_templates/details.html'
    page_title = _("Cluster Template Details")

    def get_context_data(self, **kwargs):
        context = super(ClusterTemplateDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class UploadFileView(forms.ModalFormView):
    form_class = cluster_forms.UploadFileForm
    template_name = (
        'project/data_processing.cluster_templates/upload_file.html')
    success_url = reverse_lazy(
        'horizon:project:data_processing.cluster_templates:index')
    page_title = _("Upload Template")


class CreateClusterTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.CreateClusterTemplate
    success_url = ("horizon:project:data_processing.cluster_templates"
                   ":create-cluster-template")
    classes = ("ajax-modal",)
    template_name = "project/data_processing.cluster_templates/create.html"
    page_title = _("Create Cluster Template")


class ConfigureClusterTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureClusterTemplate
    success_url = "horizon:project:data_processing.cluster_templates"
    template_name = "project/data_processing.cluster_templates/configure.html"
    page_title = _("Configure Cluster Template")


class CopyClusterTemplateView(workflows.WorkflowView):
    workflow_class = copy_flow.CopyClusterTemplate
    success_url = "horizon:project:data_processing.cluster_templates"
    template_name = "project/data_processing.cluster_templates/configure.html"
    page_title = _("Copy Cluster Template")

    def get_context_data(self, **kwargs):
        context = super(CopyClusterTemplateView, self)\
            .get_context_data(**kwargs)

        context["template_id"] = kwargs["template_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['template_id']
            try:
                template = saharaclient.cluster_template_get(self.request,
                                                             template_id)
            except Exception:
                template = {}
                exceptions.handle(self.request,
                                  _("Unable to fetch cluster template."))
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(CopyClusterTemplateView, self).get_initial()
        initial['template_id'] = self.kwargs['template_id']
        return initial
