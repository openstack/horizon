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

import base64
import json
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard.api import sahara as saharaclient
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.workflows.create as create_flow
import openstack_dashboard.dashboards.project.data_processing.utils. \
    workflow_helpers as wf_helpers

LOG = logging.getLogger(__name__)


class CopyClusterTemplate(create_flow.ConfigureClusterTemplate):
    success_message = _("Cluster Template copy %s created")
    entry_point = "generalconfigaction"

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        template_id = context_seed["template_id"]
        try:
            template = saharaclient.cluster_template_get(request, template_id)
            self._set_configs_to_copy(template.cluster_configs)

            request.GET = request.GET.copy()
            request.GET.update({"plugin_name": template.plugin_name,
                                "hadoop_version": template.hadoop_version,
                                "aa_groups": template.anti_affinity})

            super(CopyClusterTemplate, self).__init__(request, context_seed,
                                                      entry_point, *args,
                                                      **kwargs)
            # Initialize node groups.
            # TODO(rdopieralski) The same (or very similar) code appears
            # multiple times in this dashboard. It should be refactored to
            # a function.
            for step in self.steps:
                if isinstance(step, create_flow.ConfigureNodegroups):
                    ng_action = step.action
                    template_ngs = template.node_groups

                    if 'forms_ids' in request.POST:
                        continue
                    ng_action.groups = []
                    for i, templ_ng in enumerate(template_ngs):
                        group_name = "group_name_%d" % i
                        template_id = "template_id_%d" % i
                        count = "count_%d" % i
                        serialized = "serialized_%d" % i

                        # save the original node group with all its fields in
                        # case the template id is missing
                        serialized_val = base64.urlsafe_b64encode(
                            json.dumps(wf_helpers.clean_node_group(templ_ng)))

                        ng = {
                            "name": templ_ng["name"],
                            "count": templ_ng["count"],
                            "id": i,
                            "deletable": "true",
                            "serialized": serialized_val
                        }
                        if "node_group_template_id" in templ_ng:
                            ng["template_id"] = templ_ng[
                                "node_group_template_id"]
                        ng_action.groups.append(ng)

                        wf_helpers.build_node_group_fields(
                            ng_action, group_name, template_id, count,
                            serialized)

                elif isinstance(step, create_flow.GeneralConfig):
                    fields = step.action.fields
                    fields["cluster_template_name"].initial = (
                        template.name + "-copy")

                    fields["description"].initial = template.description
        except Exception:
            exceptions.handle(request,
                              _("Unable to fetch template to copy."))
