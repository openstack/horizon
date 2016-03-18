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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs

from openstack_dashboard import api
import openstack_dashboard.dashboards.project.stacks.template_versions.tables \
    as project_tables
import openstack_dashboard.dashboards.project.stacks.template_versions.tabs \
    as project_tabs


class TemplateVersionsView(tables.DataTableView):
    table_class = project_tables.TemplateVersionsTable
    template_name = 'project/stacks.template_versions/index.html'
    page_title = _("Template Versions")

    def get_data(self):
        try:
            template_versions = sorted(
                api.heat.template_version_list(self.request),
                key=lambda template_version: template_version.version)
        except Exception:
            template_versions = []
            msg = _('Unable to retrieve template versions.')
            exceptions.handle(self.request, msg)
        return template_versions


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.TemplateVersionDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ template_version }}"

    def get_template_version(self, request, **kwargs):
        try:
            template_functions = api.heat.template_function_list(
                request, kwargs['template_version'])
            return template_functions
        except Exception:
            msg = _('Unable to retrieve template functions.')
            exceptions.handle(request, msg, redirect=self.get_redirect_url())

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:stacks.template_versions:index')
