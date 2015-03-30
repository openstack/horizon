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
import json
import logging

from django import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon import workflows

from openstack_dashboard.api import sahara as saharaclient

import openstack_dashboard.dashboards.project.data_processing.jobs.tables \
    as _tables
import openstack_dashboard.dashboards.project.data_processing.jobs.tabs \
    as _tabs
import openstack_dashboard.dashboards.project.data_processing.jobs. \
    workflows.create as create_flow
import openstack_dashboard.dashboards.project.data_processing.jobs. \
    workflows.launch as launch_flow

LOG = logging.getLogger(__name__)


class JobsView(tables.DataTableView):
    table_class = _tables.JobsTable
    template_name = 'project/data_processing.jobs/jobs.html'
    page_title = _("Job Templates")

    def get_data(self):
        try:
            search_opts = {}
            filter = self.get_server_filter_info(self.request)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            jobs = saharaclient.job_list(self.request, search_opts)
        except Exception:
            jobs = []
            exceptions.handle(self.request,
                              _("Unable to fetch jobs."))
        return jobs


class CreateJobView(workflows.WorkflowView):
    workflow_class = create_flow.CreateJob
    success_url = "horizon:project:data_processing.jobs:create-job"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.jobs/create.html"
    page_title = _("Create Job Template")


class JobDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobDetailsTabs
    template_name = 'project/data_processing.jobs/details.html'
    page_title = _("Job Template Details")

    def get_context_data(self, **kwargs):
        context = super(JobDetailsView, self).get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class LaunchJobView(workflows.WorkflowView):
    workflow_class = launch_flow.LaunchJob
    success_url = "horizon:project:data_processing.jobs"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.jobs/launch.html"
    page_title = _("Launch Job")

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            if request.REQUEST.get("json", None):
                job_id = request.REQUEST.get("job_id")
                job_type = saharaclient.job_get(request, job_id).type
                return http.HttpResponse(json.dumps({"job_type": job_type}),
                                         content_type='application/json')
        return super(LaunchJobView, self).get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super(LaunchJobView, self).get_context_data(**kwargs)
        return context


class LaunchJobNewClusterView(workflows.WorkflowView):
    workflow_class = launch_flow.LaunchJobNewCluster
    success_url = "horizon:project:data_processing.jobs"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.jobs/launch.html"
    page_title = _("Launch Job")

    def get_context_data(self, **kwargs):
        context = super(LaunchJobNewClusterView, self).\
            get_context_data(**kwargs)
        return context


class ChoosePluginView(workflows.WorkflowView):
    workflow_class = launch_flow.ChosePluginVersion
    success_url = "horizon:project:data_processing.jobs"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.jobs/launch.html"
    page_title = _("Launch Job")

    def get_context_data(self, **kwargs):
        context = super(ChoosePluginView, self).get_context_data(**kwargs)
        return context
