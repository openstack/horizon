# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
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

import logging

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.instances.tables import \
        AdminInstancesTable
from openstack_dashboard.dashboards.project.instances.views import \
        console, DetailView, vnc, spice, UpdateView
from openstack_dashboard.dashboards.project.instances.workflows.\
        update_instance import AdminUpdateInstance

LOG = logging.getLogger(__name__)


class AdminUpdateView(UpdateView):
    workflow_class = AdminUpdateInstance


class AdminIndexView(tables.DataTableView):
    table_class = AdminInstancesTable
    template_name = 'admin/instances/index.html'

    def get_data(self):
        instances = []
        try:
            instances = api.nova.server_list(self.request, all_tenants=True)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        if instances:
            # Gather our flavors to correlate against IDs
            try:
                flavors = api.nova.flavor_list(self.request)
            except:
                # If fails to retrieve flavor list, creates an empty list.
                flavors = []

            # Gather our tenants to correlate against IDs
            try:
                tenants = api.keystone.tenant_list(self.request, admin=True)
            except:
                tenants = []
                msg = _('Unable to retrieve instance tenant information.')
                exceptions.handle(self.request, msg)

            full_flavors = SortedDict([(f.id, f) for f in flavors])
            tenant_dict = SortedDict([(t.id, t) for t in tenants])
            # Loop through instances to get flavor and tenant info.
            for inst in instances:
                flavor_id = inst.flavor["id"]
                try:
                    if flavor_id in full_flavors:
                        inst.full_flavor = full_flavors[flavor_id]
                    else:
                        # If the flavor_id is not in full_flavors list,
                        # gets it via nova api.
                        inst.full_flavor = api.nova.flavor_get(
                                            self.request, flavor_id)
                except:
                    msg = _('Unable to retrieve instance size information.')
                    exceptions.handle(self.request, msg)
                tenant = tenant_dict.get(inst.tenant_id, None)
                inst.tenant_name = getattr(tenant, "name", None)
        return instances
