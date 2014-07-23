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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard.api import sahara as saharaclient
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.workflows.create as clt_create_flow
import openstack_dashboard.dashboards.project.data_processing. \
    clusters.workflows.create as cl_create_flow
import openstack_dashboard.dashboards.project.data_processing. \
    utils.workflow_helpers as whelpers

from saharaclient.api import base as api_base

LOG = logging.getLogger(__name__)


class NodeGroupsStep(clt_create_flow.ConfigureNodegroups):
    pass


class ScaleCluster(cl_create_flow.ConfigureCluster,
                   whelpers.StatusFormatMixin):
    slug = "scale_cluster"
    name = _("Scale Cluster")
    finalize_button_name = _("Scale")
    success_url = "horizon:project:data_processing.clusters:index"
    default_steps = (NodeGroupsStep, )

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        ScaleCluster._cls_registry = set([])

        self.success_message = _("Scaled cluster successfully started.")

        cluster_id = context_seed["cluster_id"]
        try:
            cluster = saharaclient.cluster_get(request, cluster_id)
            plugin = cluster.plugin_name
            hadoop_version = cluster.hadoop_version

            #init deletable nodegroups
            deletable = dict()
            for group in cluster.node_groups:
                deletable[group["name"]] = "false"
            request.GET = request.GET.copy()
            request.GET.update({
                "cluster_id": cluster_id,
                "plugin_name": plugin,
                "hadoop_version": hadoop_version,
                "deletable": deletable
            })

            super(ScaleCluster, self).__init__(request, context_seed,
                                           entry_point, *args,
                                           **kwargs)

            #init Node Groups

            for step in self.steps:
                if isinstance(step, clt_create_flow.ConfigureNodegroups):
                    ng_action = step.action
                    template_ngs = cluster.node_groups

                    if 'forms_ids' not in request.POST:
                        ng_action.groups = []
                        for id in range(0, len(template_ngs), 1):
                            group_name = "group_name_" + str(id)
                            template_id = "template_id_" + str(id)
                            count = "count_" + str(id)
                            templ_ng = template_ngs[id]
                            ng_action.groups.append(
                                {"name": templ_ng["name"],
                                 "template_id": templ_ng["node_group_template_id"],
                                 "count": templ_ng["count"],
                                 "id": id,
                                 "deletable": "false"})

                            whelpers.build_node_group_fields(ng_action,
                                                             group_name,
                                                             template_id,
                                                             count)
        except Exception:
            exceptions.handle(request,
                              _("Unable to fetch cluster to scale"))

    def format_status_message(self, message):
        # Scaling form requires special handling because it has no Cluster name
        # in it's context

        error_description = getattr(self, 'error_description', None)
        if error_description:
            return error_description
        else:
            return self.success_message

    def handle(self, request, context):
        cluster_id = request.GET["cluster_id"]
        try:
            cluster = saharaclient.cluster_get(request, cluster_id)
            existing_node_groups = set([])
            for ng in cluster.node_groups:
                existing_node_groups.add(ng["name"])

            scale_object = dict()

            ids = json.loads(context["ng_forms_ids"])

            for _id in ids:
                name = context["ng_group_name_%s" % _id]
                template_id = context["ng_template_id_%s" % _id]
                count = context["ng_count_%s" % _id]

                if name not in existing_node_groups:
                    if "add_node_groups" not in scale_object:
                        scale_object["add_node_groups"] = []

                    scale_object["add_node_groups"].append(
                        {"name": name,
                         "node_group_template_id": template_id,
                         "count": int(count)})
                else:
                    old_count = None
                    for ng in cluster.node_groups:
                        if name == ng["name"]:
                            old_count = ng["count"]
                            break

                    if old_count != count:
                        if "resize_node_groups" not in scale_object:
                            scale_object["resize_node_groups"] = []

                        scale_object["resize_node_groups"].append(
                            {"name": name,
                             "count": int(count)}
                        )
        except Exception:
            scale_object = {}
            exceptions.handle(request,
                              _("Unable to fetch cluster to scale."))

        try:
            saharaclient.cluster_scale(request, cluster_id, scale_object)
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request,
                              _("Scale cluster operation failed"))
            return False
