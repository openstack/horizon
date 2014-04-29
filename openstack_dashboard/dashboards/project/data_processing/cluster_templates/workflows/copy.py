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

from openstack_dashboard.api import sahara as saharaclient
import openstack_dashboard.dashboards.project.data_processing. \
    cluster_templates.workflows.create as create_flow
import openstack_dashboard.dashboards.project.data_processing.utils. \
    workflow_helpers as wf_helpers

LOG = logging.getLogger(__name__)


class CopyClusterTemplate(create_flow.ConfigureClusterTemplate):
    success_message = _("Cluster Template copy %s created")

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
            #init Node Groups
            for step in self.steps:
                if isinstance(step, create_flow.ConfigureNodegroups):
                    ng_action = step.action
                    template_ngs = template.node_groups

                    if 'forms_ids' not in request.POST:
                        ng_action.groups = []
                        for id in range(0, len(template_ngs), 1):
                            group_name = "group_name_" + str(id)
                            template_id = "template_id_" + str(id)
                            count = "count_" + str(id)
                            templ_ng = template_ngs[id]
                            ng_action.groups.append(
                                {"name": templ_ng["name"],
                                 "template_id":
                                     templ_ng["node_group_template_id"],
                                 "count": templ_ng["count"],
                                 "id": id,
                                 "deletable": "true"})

                            wf_helpers.build_node_group_fields(ng_action,
                                                               group_name,
                                                               template_id,
                                                               count)

                elif isinstance(step, create_flow.GeneralConfig):
                    fields = step.action.fields
                    fields["cluster_template_name"].initial = \
                        template.name + "-copy"

                    fields["description"].initial = template.description
        except Exception:
            exceptions.handle(request,
                              _("Unable to fetch template to copy."))
