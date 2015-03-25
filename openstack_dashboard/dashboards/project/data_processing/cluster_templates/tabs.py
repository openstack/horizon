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
from horizon import tabs

from openstack_dashboard.api import nova
from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project. \
    data_processing.utils import workflow_helpers as helpers


LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "cluster_template_details_tab"
    template_name = (
        "project/data_processing.cluster_templates/_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.cluster_template_get(request, template_id)
        except Exception:
            template = {}
            exceptions.handle(request,
                              _("Unable to fetch cluster template details."))
        return {"template": template}


class NodeGroupsTab(tabs.Tab):
    name = _("Node Groups")
    slug = "cluster_template_nodegroups_tab"
    template_name = (
        "project/data_processing.cluster_templates/_nodegroups_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.cluster_template_get(request, template_id)
            for ng in template.node_groups:
                if not ng["flavor_id"]:
                    continue
                ng["flavor_name"] = (
                    nova.flavor_get(request, ng["flavor_id"]).name)
                ng["node_group_template"] = saharaclient.safe_call(
                    saharaclient.nodegroup_template_get,
                    request, ng.get("node_group_template_id", None))
                ng["security_groups_full"] = helpers.get_security_groups(
                    request, ng.get("security_groups"))
        except Exception:
            template = {}
            exceptions.handle(request,
                              _("Unable to fetch node group details."))
        return {"template": template}


class ClusterTemplateDetailsTabs(tabs.TabGroup):
    slug = "cluster_template_details"
    tabs = (GeneralTab, NodeGroupsTab, )
    sticky = True
