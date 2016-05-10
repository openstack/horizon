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

from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.project.stacks.template_versions \
    import tables as project_tables


class TemplateFunctionsTab(tabs.Tab):
    name = _("Template Functions")
    slug = "template_functions"
    template_name = "project/stacks.template_versions/_details.html"
    preload = False

    def allowed(self, request):
        return policy.check(
            (("orchestration", "stacks:list_template_functions"),),
            request)

    def get_context_data(self, request):
        template_version = self.tab_group.kwargs['template_version']
        try:
            template_functions = api.heat.template_function_list(
                self.request, template_version)
        except Exception:
            template_functions = []
            messages.error(request, _('Unable to get functions for template '
                                      'version "%s".') % template_version)
        return {"table": project_tables.TemplateFunctionsTable(
            request, data=template_functions), }


class TemplateVersionDetailsTabs(tabs.TabGroup):
    slug = "template_version_details"
    tabs = (TemplateFunctionsTab,)
