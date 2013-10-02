# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
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

from django.utils.datastructures import SortedDict  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.project.instances import views
from openstack_dashboard.dashboards.project.instances.workflows \
    import update_instance


# re-use console from project.instances.views to make reflection work
def console(args, **kvargs):
    return views.console(args, **kvargs)


# re-use vnc from project.instances.views to make reflection work
def vnc(args, **kvargs):
    return views.vnc(args, **kvargs)


# re-use spice from project.instances.views to make reflection work
def spice(args, **kvargs):
    return views.spice(args, **kvargs)


class AdminUpdateView(views.UpdateView):
    workflow_class = update_instance.AdminUpdateInstance


class AdminIndexView(tables.DataTableView):
    table_class = project_tables.AdminInstancesTable
    template_name = 'admin/instances/index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        instances = []
        marker = self.request.GET.get(
            project_tables.AdminInstancesTable._meta.pagination_param, None)
        try:
            instances, self._more = api.nova.server_list(
                self.request,
                search_opts={'marker': marker,
                             'paginate': True},
                all_tenants=True)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        if instances:
            # Gather our flavors to correlate against IDs
            try:
                flavors = api.nova.flavor_list(self.request)
            except Exception:
                # If fails to retrieve flavor list, creates an empty list.
                flavors = []

            # Gather our tenants to correlate against IDs
            try:
                tenants, has_more = api.keystone.tenant_list(self.request)
            except Exception:
                tenants = []
                msg = _('Unable to retrieve instance project information.')
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
                except Exception:
                    msg = _('Unable to retrieve instance size information.')
                    exceptions.handle(self.request, msg)
                tenant = tenant_dict.get(inst.tenant_id, None)
                inst.tenant_name = getattr(tenant, "name", None)
        return instances
