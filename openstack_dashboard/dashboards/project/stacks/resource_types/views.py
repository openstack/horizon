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

import yaml

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs

from openstack_dashboard import api
import openstack_dashboard.dashboards.project.stacks.resource_types.tables \
    as project_tables
import openstack_dashboard.dashboards.project.stacks.resource_types.tabs \
    as project_tabs


class ResourceTypesView(tables.DataTableView):
    table_class = project_tables.ResourceTypesTable
    page_title = _("Resource Types")

    def get_data(self):
        try:
            filters = self.get_filters()
            if 'name' in filters:
                filters['name'] = '.*' + filters['name']
            r_types = sorted(api.heat.resource_types_list(self.request,
                                                          filters=filters),
                             key=lambda resource: resource.resource_type)
        except Exception:
            r_types = []
            msg = _('Unable to retrieve stack resource types.')
            exceptions.handle(self.request, msg)
        return r_types


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.ResourceTypeDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ resource_type }}"

    def get_resource_type(self, request, **kwargs):
        try:
            resource_type_overview = api.heat.resource_type_get(
                request,
                kwargs['resource_type'])
            return resource_type_overview
        except Exception:
            msg = _('Unable to retrieve resource type details.')
            exceptions.handle(request, msg, redirect=self.get_redirect_url())

    def get_tabs(self, request, **kwargs):
        resource_type_overview = self.get_resource_type(request, **kwargs)
        r_type = resource_type_overview['resource_type']
        r_type_attributes = resource_type_overview['attributes']
        r_type_properties = resource_type_overview['properties']
        return self.tab_group_class(
            request,
            rt=r_type,
            rt_attributes=yaml.safe_dump(r_type_attributes, indent=2),
            rt_properties=yaml.safe_dump(r_type_properties, indent=2),
            **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:stacks.resources:index')
