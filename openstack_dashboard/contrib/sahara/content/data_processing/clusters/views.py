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

from datetime import datetime
import json
import logging

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.generic import base as django_base
import six

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon.utils.urlresolvers import reverse  # noqa
from horizon import workflows

from openstack_dashboard.contrib.sahara.api import sahara as saharaclient

import openstack_dashboard.contrib.sahara.content.data_processing.clusters. \
    tables as c_tables
import openstack_dashboard.contrib.sahara.content.data_processing.clusters. \
    tabs as _tabs
import openstack_dashboard.contrib.sahara.content.data_processing.clusters. \
    workflows.create as create_flow
import openstack_dashboard.contrib.sahara.content.data_processing.clusters. \
    workflows.scale as scale_flow
from saharaclient.api.base import APIException

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
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ cluster.name|default:cluster.id }}"

    @memoized.memoized_method
    def get_object(self):
        cl_id = self.kwargs["cluster_id"]
        try:
            return saharaclient.cluster_get(self.request, cl_id)
        except Exception:
            msg = _('Unable to retrieve details for cluster "%s".') % cl_id
            redirect = reverse(
                "horizon:project:data_processing.clusters:clusters")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ClusterDetailsView, self).get_context_data(**kwargs)
        context['cluster'] = self.get_object()
        return context


class ClusterEventsView(django_base.View):

    _date_format = "%Y-%m-%dT%H:%M:%S"

    @staticmethod
    def _created_at_key(obj):
        return datetime.strptime(obj["created_at"],
                                 ClusterEventsView._date_format)

    def get(self, request, *args, **kwargs):

        cluster_id = kwargs.get("cluster_id")

        try:
            cluster = saharaclient.cluster_get(request, cluster_id,
                                               show_progress=True)
            node_group_mapping = {}
            for node_group in cluster.node_groups:
                node_group_mapping[node_group["id"]] = node_group["name"]

            provision_steps = cluster.provision_progress

            # Sort by create time
            provision_steps = sorted(provision_steps,
                                     key=ClusterEventsView._created_at_key,
                                     reverse=True)

            for step in provision_steps:
                # Sort events of the steps also
                step["events"] = sorted(step["events"],
                                        key=ClusterEventsView._created_at_key,
                                        reverse=True)

                successful_events_count = 0

                for event in step["events"]:
                    if event["node_group_id"]:
                        event["node_group_name"] = node_group_mapping[
                            event["node_group_id"]]

                    event_result = _("Unknown")
                    if event["successful"] is True:
                        successful_events_count += 1
                        event_result = _("Completed Successfully")
                    elif event["successful"] is False:
                        event_result = _("Failed")

                    event["result"] = event_result

                    if not event["event_info"]:
                        event["event_info"] = _("No info available")

                start_time = datetime.strptime(step["created_at"],
                                               self._date_format)
                end_time = datetime.now()
                # Clear out microseconds. There is no need for that precision.
                end_time = end_time.replace(microsecond=0)
                if step["successful"] is not None:
                    updated_at = step["updated_at"]
                    end_time = datetime.strptime(updated_at,
                                                 self._date_format)
                step["duration"] = six.text_type(end_time - start_time)

                result = _("In progress")
                step["completed"] = successful_events_count

                if step["successful"] is True:
                    step["completed"] = step["total"]
                    result = _("Completed Successfully")
                elif step["successful"] is False:
                    result = _("Failed")

                step["result"] = result

            status = cluster.status.lower()
            need_update = status not in ("active", "error")
        except APIException:
            # Cluster is not available. Returning empty event log.
            need_update = False
            provision_steps = []

        context = {"provision_steps": provision_steps,
                   "need_update": need_update}

        return HttpResponse(json.dumps(context),
                            content_type='application/json')


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
