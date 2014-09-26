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

from django.http import Http404  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import messages
from horizon import tables

from openstack_dashboard.api import sahara as saharaclient

from saharaclient.api import base as api_base


LOG = logging.getLogger(__name__)


class CreateCluster(tables.LinkAction):
    name = "create"
    verbose_name = _("Launch Cluster")
    url = "horizon:project:data_processing.clusters:create-cluster"
    classes = ("ajax-modal",)
    icon = "plus"


class ScaleCluster(tables.LinkAction):
    name = "scale"
    verbose_name = _("Scale Cluster")
    url = "horizon:project:data_processing.clusters:scale"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, cluster=None):
        return cluster.status == "Active"


class DeleteCluster(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Cluster",
            u"Delete Clusters",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Cluster",
            u"Deleted Clusters",
            count
        )

    name = "delete"
    classes = ('btn-danger', 'btn-terminate')

    def action(self, request, obj_id):
        saharaclient.cluster_delete(request, obj_id)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        try:
            return saharaclient.cluster_get(request, instance_id)
        except api_base.APIException as e:
            if e.error_code == 404:
                raise Http404
            else:
                messages.error(request,
                               _("Unable to update row"))


def get_instances_count(cluster):
    return sum([len(ng["instances"])
                for ng in cluster.node_groups])


class ConfigureCluster(tables.LinkAction):
    name = "configure"
    verbose_name = _("Configure Cluster")
    url = "horizon:project:data_processing.clusters:configure-cluster"
    classes = ("ajax-modal", "configure-cluster-btn")
    icon = "plus"
    attrs = {"style": "display: none"}


class ClustersTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("error", False)
    )

    name = tables.Column("name",
        verbose_name=_("Name"),
        link=("horizon:project:data_processing.clusters:details"))
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)
    instances_count = tables.Column(get_instances_count,
                                    verbose_name=_("Instances Count"))

    class Meta:
        name = "clusters"
        verbose_name = _("Clusters")
        row_class = UpdateRow
        status_columns = ["status"]
        table_actions = (CreateCluster,
                         ConfigureCluster,
                         DeleteCluster)
        row_actions = (ScaleCluster,
                       DeleteCluster,)
