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

import openstack_dashboard.dashboards.project.data_processing.data_sources. \
    tables as ds_tables
import openstack_dashboard.dashboards.project.data_processing.data_sources. \
    tabs as _tabs
import openstack_dashboard.dashboards.project.data_processing.data_sources. \
    workflows.create as create_flow

LOG = logging.getLogger(__name__)


class DataSourcesView(tables.DataTableView):
    table_class = ds_tables.DataSourcesTable
    template_name = 'project/data_processing.data_sources/data_sources.html'
    page_title = _("Data Sources")

    def get_data(self):
        try:
            data_sources = saharaclient.data_source_list(self.request)
        except Exception:
            data_sources = []
            exceptions.handle(self.request,
                              _("Unable to fetch data sources."))
        return data_sources


class CreateDataSourceView(workflows.WorkflowView):
    workflow_class = create_flow.CreateDataSource
    success_url = \
        "horizon:project:data_processing.data-sources:create-data-source"
    classes = ("ajax-modal",)
    template_name = "project/data_processing.data_sources/create.html"
    page_title = _("Create Data Source")


class DataSourceDetailsView(tabs.TabView):
    tab_group_class = _tabs.DataSourceDetailsTabs
    template_name = 'project/data_processing.data_sources/details.html'
    page_title = _("Data Source Details")
