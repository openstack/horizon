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
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.api import sahara as saharaclient

from saharaclient.api import base as api_base


LOG = logging.getLogger(__name__)


class CreateJobBinary(tables.LinkAction):
    name = "create job binary"
    verbose_name = _("Create Job Binary")
    url = "horizon:project:data_processing.job_binaries:create-job-binary"
    classes = ("ajax-modal",)
    icon = "plus"


class DeleteJobBinary(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Job Binary",
            u"Delete Job Binaries",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Job Binary",
            u"Deleted Job Binaries",
            count
        )

    def delete(self, request, obj_id):
        jb = saharaclient.job_binary_get(request, obj_id)
        (jb_type, jb_internal_id) = jb.url.split("://")
        if jb_type == "internal-db":
            try:
                saharaclient.job_binary_internal_delete(request,
                                                        jb_internal_id)
            except api_base.APIException:
                # nothing to do for job-binary-internal if
                # it does not exist.
                pass

        saharaclient.job_binary_delete(request, obj_id)


class DownloadJobBinary(tables.LinkAction):
    name = "download job binary"
    verbose_name = _("Download Job Binary")
    url = "horizon:project:data_processing.job_binaries:download"
    classes = ("btn-edit",)


class JobBinariesTable(tables.DataTable):
    name = tables.Column(
        "name",
        verbose_name=_("Name"),
        link="horizon:project:data_processing.job_binaries:details")
    type = tables.Column("url",
                         verbose_name=_("Url"))
    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "job_binaries"
        verbose_name = _("Job Binaries")
        table_actions = (CreateJobBinary,
                         DeleteJobBinary)
        row_actions = (DeleteJobBinary, DownloadJobBinary)
