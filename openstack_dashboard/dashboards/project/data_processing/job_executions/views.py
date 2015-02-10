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

from openstack_dashboard.api import sahara as saharaclient

from openstack_dashboard.dashboards.project.data_processing.job_executions \
    import tables as je_tables
import openstack_dashboard.dashboards.project.data_processing. \
    job_executions.tabs as _tabs

LOG = logging.getLogger(__name__)


class JobExecutionsView(tables.DataTableView):
    SEARCH_MAPPING = {"cluster": "cluster.name",
                      "job": "job.name"}

    table_class = je_tables.JobExecutionsTable
    template_name = (
        'project/data_processing.job_executions/job_executions.html')
    page_title = _("Job Executions")

    def get_data(self):
        try:
            search_opts = {}
            filter = self.get_server_filter_info(self.request)
            if filter['value'] and filter['field']:
                if filter['field'] in self.SEARCH_MAPPING:
                    # Handle special cases for cluster and job
                    # since they are in different database tables.
                    search_opts = {
                        self.SEARCH_MAPPING[filter['field']]: filter['value']}
                else:
                    search_opts = {filter['field']: filter['value']}
            jobs = saharaclient.job_execution_list(self.request, search_opts)
        except Exception:
            jobs = []
            exceptions.handle(self.request,
                              _("Unable to fetch job executions."))
        return jobs


class JobExecutionDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobExecutionDetailsTabs
    template_name = 'project/data_processing.job_executions/details.html'
    page_title = _("Job Execution Details")
