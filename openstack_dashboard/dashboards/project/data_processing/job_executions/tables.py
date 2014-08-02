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

from django.core import urlresolvers
from django.utils import http
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project.data_processing. \
    jobs import tables as j_t

LOG = logging.getLogger(__name__)


class DeleteJobExecution(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("Job execution")
    data_type_plural = _("Job executions")
    classes = ('btn-danger', 'btn-terminate')

    def action(self, request, obj_id):
        saharaclient.job_execution_delete(request, obj_id)


class ReLaunchJobExistingCluster(j_t.ChoosePlugin):
    name = "relaunch-job-existing"
    verbose_name = _("Relaunch On Existing Cluster")
    action_present = _("Launch")
    action_past = _("Launched")
    data_type_singular = _("Job")
    data_type_plural = _("Jobs")
    url = "horizon:project:data_processing.jobs:launch-job"
    classes = ('ajax-modal', 'btn-launch')

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)

        params = http.urlencode({'job_id': datum.job_id,
                                 'job_execution_id': datum.id})
        return "?".join([base_url, params])


class ReLaunchJobNewCluster(ReLaunchJobExistingCluster):
    name = "relaunch-job-new"
    verbose_name = _("Relaunch On New Cluster")
    action_present = _("Launch")
    action_past = _("Launched")
    data_type_singular = _("Job")
    data_type_plural = _("Jobs")
    url = "horizon:project:data_processing.jobs:choose-plugin"
    classes = ('ajax-modal', 'btn-launch')


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, job_execution_id):
        job_execution = saharaclient.job_execution_get(request,
                                                       job_execution_id)
        return job_execution


class JobExecutionsTable(tables.DataTable):
    class StatusColumn(tables.Column):
        def get_raw_data(self, datum):
            return datum.info['status']

    STATUS_CHOICES = (
        ("DONEWITHERROR", False),
        ("FAILED", False),
        ("KILLED", False),
        ("SUCCEEDED", True),
    )

    name = tables.Column("id",
        verbose_name=_("ID"),
        display_choices=(("id", "ID"), ("name", "Name")),
        link=("horizon:project:data_processing.job_executions:details"))

    status = StatusColumn("info",
                          status=True,
                          status_choices=STATUS_CHOICES,
                          verbose_name=_("Status"))

    def get_object_display(self, datum):
        return datum.id

    class Meta:
        name = "job_executions"
        row_class = UpdateRow
        status_columns = ["status"]
        verbose_name = _("Job Executions")
        table_actions = [DeleteJobExecution]
        row_actions = [DeleteJobExecution,
                       ReLaunchJobExistingCluster,
                       ReLaunchJobNewCluster]
