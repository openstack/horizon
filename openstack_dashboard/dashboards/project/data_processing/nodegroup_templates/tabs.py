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

from openstack_dashboard.api import network
from openstack_dashboard.api import nova
from openstack_dashboard.api import sahara as saharaclient


from openstack_dashboard.dashboards.project. \
    data_processing.utils import workflow_helpers as helpers

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "nodegroup_template_details_tab"
    template_name = (
        "project/data_processing.nodegroup_templates/_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.nodegroup_template_get(
                request, template_id)
        except Exception:
            template = {}
            exceptions.handle(request,
                              _("Unable to fetch node group template."))
        try:
            flavor = nova.flavor_get(request, template.flavor_id)
        except Exception:
            flavor = {}
            exceptions.handle(request,
                              _("Unable to fetch flavor for template."))

        floating_ip_pool_name = None
        if template.floating_ip_pool:
            try:
                floating_ip_pool_name = self._get_floating_ip_pool_name(
                    request, template.floating_ip_pool)
            except Exception:
                exceptions.handle(request,
                                  _("Unable to fetch floating ip pools."))

        security_groups = helpers.get_security_groups(
            request, template.security_groups)

        return {"template": template, "flavor": flavor,
                "floating_ip_pool_name": floating_ip_pool_name,
                "security_groups": security_groups}

    def _get_floating_ip_pool_name(self, request, pool_id):
        pools = [pool for pool in network.floating_ip_pools_list(
            request) if pool.id == pool_id]

        return pools[0].name if pools else pool_id


class ConfigsTab(tabs.Tab):
    name = _("Service Configurations")
    slug = "nodegroup_template_service_configs_tab"
    template_name = (
        "project/data_processing.nodegroup_templates/_service_confs.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.nodegroup_template_get(
                request, template_id)
        except Exception:
            template = {}
            exceptions.handle(request,
                              _("Unable to fetch node group template."))
        return {"template": template}


class NodegroupTemplateDetailsTabs(tabs.TabGroup):
    slug = "nodegroup_template_details"
    tabs = (GeneralTab, ConfigsTab, )
    sticky = True
