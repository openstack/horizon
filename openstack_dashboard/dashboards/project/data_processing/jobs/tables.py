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
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class JobsFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('name', _("Name"), True),
                      ('description', _("Description"), True))


class CreateJob(tables.LinkAction):
    name = "create job"
    verbose_name = _("Create Job Template")
    url = "horizon:project:data_processing.jobs:create-job"
    classes = ("ajax-modal", "create_job_class")
    icon = "plus"


class DeleteJob(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Job Template",
            u"Delete Job Templates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Job Template",
            u"Deleted Jobs Templates",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.job_delete(request, obj_id)


class LaunchJobExistingCluster(tables.LinkAction):
    name = "launch-job-existing"
    verbose_name = _("Launch On Existing Cluster")
    url = "horizon:project:data_processing.jobs:launch-job"
    classes = ('ajax-modal', 'btn-launch')

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)

        params = http.urlencode({"job_id": datum.id})
        return "?".join([base_url, params])


class LaunchJobNewCluster(tables.LinkAction):
    name = "launch-job-new"
    verbose_name = _("Launch On New Cluster")
    url = "horizon:project:data_processing.jobs:launch-job-new-cluster"
    classes = ('ajax-modal', 'btn-launch')

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)

        params = http.urlencode({"job_id": datum.id})
        return "?".join([base_url, params])


class ChoosePlugin(tables.LinkAction):
    name = "launch-job-new"
    verbose_name = _("Launch On New Cluster")
    url = "horizon:project:data_processing.jobs:choose-plugin"
    classes = ('ajax-modal', 'btn-launch')

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)

        params = http.urlencode({"job_id": datum.id})
        return "?".join([base_url, params])


class JobsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:data_processing.jobs:details")
    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "jobs"
        verbose_name = _("Job Templates")
        table_actions = (CreateJob, DeleteJob, JobsFilterAction,)
        row_actions = (LaunchJobExistingCluster, ChoosePlugin, DeleteJob,)
