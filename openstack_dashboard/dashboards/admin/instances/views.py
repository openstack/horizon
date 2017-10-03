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

import futurist

from django.conf import settings
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
from openstack_dashboard.dashboards.admin.instances import tabs
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


# re-use get_resource_id_by_name from project.instances.views
def swap_filter(resources, filters, fake_field, real_field):
    return views.swap_filter(resources, filters, fake_field, real_field)


class AdminUpdateView(views.UpdateView):
    workflow_class = update_instance.AdminUpdateInstance
    success_url = reverse_lazy("horizon:admin:instances:index")


class AdminIndexView(tables.DataTableView):
    table_class = project_tables.AdminInstancesTable
    page_title = _("Instances")

    def has_more_data(self, table):
        return self._more

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def get_data(self):
        instances = []
        tenants = []
        tenant_dict = {}
        images = []
        flavors = []
        full_flavors = {}

        marker = self.request.GET.get(
            project_tables.AdminInstancesTable._meta.pagination_param, None)
        default_search_opts = {'marker': marker,
                               'paginate': True,
                               'all_tenants': True}

        search_opts = self.get_filters(default_search_opts.copy())

        # If filter_first is set and if there are not other filters
        # selected, then search criteria must be provided and return an empty
        # list
        filter_first = getattr(settings, 'FILTER_DATA_FIRST', {})
        if filter_first.get('admin.instances', False) and \
                len(search_opts) == len(default_search_opts):
            self._needs_filter_first = True
            self._more = False
            return instances

        self._needs_filter_first = False

        def _task_get_tenants():
            # Gather our tenants to correlate against IDs
            try:
                tmp_tenants, __ = api.keystone.tenant_list(self.request)
                tenants.extend(tmp_tenants)
                tenant_dict.update([(t.id, t) for t in tenants])
            except Exception:
                msg = _('Unable to retrieve instance project information.')
                exceptions.handle(self.request, msg)

        def _task_get_images():
            # Gather our images to correlate againts IDs
            try:
                tmp_images = api.glance.image_list_detailed(self.request)[0]
                images.extend(tmp_images)
            except Exception:
                msg = _("Unable to retrieve image list.")
                exceptions.handle(self.request, msg)

        def _task_get_flavors():
            # Gather our flavors to correlate against IDs
            try:
                tmp_flavors = api.nova.flavor_list(self.request)
                flavors.extend(tmp_flavors)
                full_flavors.update([(str(flavor.id), flavor)
                                     for flavor in flavors])
            except Exception:
                msg = _("Unable to retrieve flavor list.")
                exceptions.handle(self.request, msg)

        def _task_get_instances():
            try:
                tmp_instances, self._more = api.nova.server_list(
                    self.request,
                    search_opts=search_opts)
                instances.extend(tmp_instances)
            except Exception:
                self._more = False
                exceptions.handle(self.request,
                                  _('Unable to retrieve instance list.'))
                # In case of exception when calling nova.server_list
                # don't call api.network
                return

            try:
                api.network.servers_update_addresses(self.request, instances,
                                                     all_tenants=True)
            except Exception:
                exceptions.handle(
                    self.request,
                    message=_('Unable to retrieve IP addresses from Neutron.'),
                    ignore=True)

        with futurist.ThreadPoolExecutor(max_workers=3) as e:
            e.submit(fn=_task_get_tenants)
            e.submit(fn=_task_get_images)
            e.submit(fn=_task_get_flavors)

        if 'project' in search_opts and \
                not swap_filter(tenants, search_opts, 'project', 'tenant_id'):
                self._more = False
                return instances
        elif 'image_name' in search_opts and \
                not swap_filter(images, search_opts, 'image_name', 'image'):
                self._more = False
                return instances
        elif "flavor_name" in search_opts and \
                not swap_filter(flavors, search_opts, 'flavor_name', 'flavor'):
                self._more = False
                return instances

        _task_get_instances()

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


class LiveMigrateView(forms.ModalFormView):
    form_class = project_forms.LiveMigrateForm
    template_name = 'admin/instances/live_migrate.html'
    context_object_name = 'instance'
    success_url = reverse_lazy("horizon:admin:instances:index")
    page_title = _("Live Migrate")
    success_label = page_title

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
    tab_group_class = tabs.AdminInstanceDetailTabs
    redirect_url = 'horizon:admin:instances:index'
    image_url = 'horizon:admin:images:detail'
    volume_url = 'horizon:admin:volumes:detail'

    def _get_actions(self, instance):
        table = project_tables.AdminInstancesTable(self.request)
        return table.render_row_actions(instance)
