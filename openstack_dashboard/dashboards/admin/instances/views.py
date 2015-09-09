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

from collections import OrderedDict
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.instances \
    import forms as project_forms
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


# re-use rdp from project.instances.views to make reflection work
def rdp(args, **kvargs):
    return views.rdp(args, **kvargs)


class AdminUpdateView(views.UpdateView):
    workflow_class = update_instance.AdminUpdateInstance
    success_url = reverse_lazy("horizon:admin:instances:index")


class AdminIndexView(tables.DataTableView):
    table_class = project_tables.AdminInstancesTable
    template_name = 'admin/instances/index.html'
    page_title = _("Instances")

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        instances = []
        marker = self.request.GET.get(
            project_tables.AdminInstancesTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})
        # Gather our tenants to correlate against IDs
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve instance project information.')
            exceptions.handle(self.request, msg)

        if 'project' in search_opts:
            ten_filter_ids = [t.id for t in tenants
                              if t.name == search_opts['project']]
            del search_opts['project']
            if len(ten_filter_ids) > 0:
                search_opts['tenant_id'] = ten_filter_ids[0]
            else:
                self._more = False
                return []

        try:
            instances, self._more = api.nova.server_list(
                self.request,
                search_opts=search_opts,
                all_tenants=True)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        if instances:
            try:
                api.network.servers_update_addresses(self.request, instances,
                                                     all_tenants=True)
            except Exception:
                exceptions.handle(
                    self.request,
                    message=_('Unable to retrieve IP addresses from Neutron.'),
                    ignore=True)

            # Gather our flavors to correlate against IDs
            try:
                flavors = api.nova.flavor_list(self.request)
            except Exception:
                # If fails to retrieve flavor list, creates an empty list.
                flavors = []

            full_flavors = OrderedDict([(f.id, f) for f in flavors])
            tenant_dict = OrderedDict([(t.id, t) for t in tenants])
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

    def get_filters(self, filters):
        filter_field = self.table.get_filter_field()
        filter_action = self.table._meta._filter_action
        if filter_action.is_api_filter(filter_field):
            filter_string = self.table.get_filter_string()
            if filter_field and filter_string:
                filters[filter_field] = filter_string
        return filters


class LiveMigrateView(forms.ModalFormView):
    form_class = project_forms.LiveMigrateForm
    template_name = 'admin/instances/live_migrate.html'
    context_object_name = 'instance'
    success_url = reverse_lazy("horizon:admin:instances:index")
    page_title = _("Live Migrate")

    def get_context_data(self, **kwargs):
        context = super(LiveMigrateView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        return context

    @memoized.memoized_method
    def get_hosts(self, *args, **kwargs):
        try:
            return api.nova.host_list(self.request)
        except Exception:
            redirect = reverse("horizon:admin:instances:index")
            msg = _('Unable to retrieve host information.')
            exceptions.handle(self.request, msg, redirect=redirect)

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:admin:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(LiveMigrateView, self).get_initial()
        _object = self.get_object()
        if _object:
            current_host = getattr(_object, 'OS-EXT-SRV-ATTR:host', '')
            initial.update({'instance_id': self.kwargs['instance_id'],
                            'current_host': current_host,
                            'hosts': self.get_hosts()})
        return initial


class DetailView(views.DetailView):
    redirect_url = 'horizon:admin:instances:index'
    image_url = 'horizon:admin:images:detail'
    volume_url = 'horizon:admin:volumes:volumes:detail'

    def _get_actions(self, instance):
        table = project_tables.AdminInstancesTable(self.request)
        return table.render_row_actions(instance)
