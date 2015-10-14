# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.flavors \
    import tables as project_tables
from openstack_dashboard.dashboards.admin.flavors \
    import workflows as flavor_workflows


INDEX_URL = "horizon:admin:flavors:index"


class IndexView(tables.DataTableView):
    table_class = project_tables.FlavorsTable
    template_name = 'admin/flavors/index.html'
    page_title = _("Flavors")

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET.get(
            project_tables.FlavorsTable._meta.pagination_param, None)
        request = self.request
        flavors = []
        try:
            # Removing the pagination params and adding "is_public=None"
            # will return all flavors.
            flavors, self._more = api.nova.flavor_list_paged(request, None,
                                                             marker=marker,
                                                             paginate=True)
        except Exception:
            self._more = False
            exceptions.handle(request,
                              _('Unable to retrieve flavor list.'))
        # Sort flavors by size
        flavors.sort(key=lambda f: (f.vcpus, f.ram, f.disk))
        return flavors


class CreateView(workflows.WorkflowView):
    workflow_class = flavor_workflows.CreateFlavor
    template_name = 'admin/flavors/create.html'
    page_title = _("Create Flavor")


class UpdateView(workflows.WorkflowView):
    workflow_class = flavor_workflows.UpdateFlavor
    template_name = 'admin/flavors/update.html'
    page_title = _("Edit Flavor")

    def get_initial(self):
        flavor_id = self.kwargs['id']

        try:
            # Get initial flavor information
            flavor = api.nova.flavor_get(self.request, flavor_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve flavor details.'),
                              redirect=reverse_lazy(INDEX_URL))
        return {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': flavor.vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'swap_mb': flavor.swap or 0,
                'rxtx_factor': flavor.rxtx_factor or 1,
                'eph_gb': getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral', None)}
