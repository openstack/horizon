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
        return {"template": template, "flavor": flavor}


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
