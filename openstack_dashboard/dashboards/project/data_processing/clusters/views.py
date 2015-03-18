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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon import workflows

from openstack_dashboard.api import sahara as saharaclient

import openstack_dashboard.dashboards.project.data_processing.clusters. \
    tables as c_tables
import openstack_dashboard.dashboards.project.data_processing.clusters.tabs \
    as _tabs
import openstack_dashboard.dashboards.project.data_processing.clusters. \
    workflows.create as create_flow
import openstack_dashboard.dashboards.project.data_processing.clusters. \
    workflows.scale as scale_flow

LOG = logging.getLogger(__name__)


class ClustersView(tables.DataTableView):
    table_class = c_tables.ClustersTable
    template_name = 'project/data_processing.clusters/clusters.html'
    page_title = _("Clusters")

    def get_data(self):
        try:
            search_opts = {}
            filter = self.get_server_filter_info(self.request)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            clusters = saharaclient.cluster_list(self.request, search_opts)
        except Exception:
            clusters = []
            exceptions.handle(self.request,
                              _("Unable to fetch cluster list"))
        return clusters


class ClusterDetailsView(tabs.TabView):
    tab_group_class = _tabs.ClusterDetailsTabs
    template_name = 'project/data_processing.clusters/details.html'
    page_title = _("Cluster Details")

    def get_context_data(self, **kwargs):
        context = super(ClusterDetailsView, self)\
            .get_context_data(**kwargs)
        return context


class CreateClusterView(workflows.WorkflowView):
    workflow_class = create_flow.CreateCluster
    success_url = \
        "horizon:project:data_processing.clusters:create-cluster"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.clusters/create.html"
    page_title = _("Launch Cluster")


class ConfigureClusterView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureCluster
    success_url = "horizon:project:data_processing.clusters"
    template_name = "project/data_processing.clusters/configure.html"
    page_title = _("Configure Cluster")

    def get_initial(self):
        initial = super(ConfigureClusterView, self).get_initial()
        initial.update(self.kwargs)
        return initial


class ScaleClusterView(workflows.WorkflowView):
    workflow_class = scale_flow.ScaleCluster
    success_url = "horizon:project:data_processing.clusters"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.clusters/scale.html"
    page_title = _("Scale Cluster")

    def get_context_data(self, **kwargs):
        context = super(ScaleClusterView, self)\
            .get_context_data(**kwargs)

        context["cluster_id"] = kwargs["cluster_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['cluster_id']
            try:
                template = saharaclient.cluster_template_get(self.request,
                                                             template_id)
            except Exception:
                template = None
                exceptions.handle(self.request,
                                  _("Unable to fetch cluster template."))
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(ScaleClusterView, self).get_initial()
        initial.update({'cluster_id': self.kwargs['cluster_id']})
        return initial
