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

from django.urls import reverse
from django.urls import reverse_lazy
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
from openstack_dashboard.utils import futurist_utils
from openstack_dashboard.utils import settings as setting_utils


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


# re-use mks from project.instances.views to make reflection work
def mks(args, **kvargs):
    return views.mks(args, **kvargs)


class AdminUpdateView(views.UpdateView):
    workflow_class = update_instance.AdminUpdateInstance
    success_url = reverse_lazy("horizon:admin:instances:index")


class AdminIndexView(tables.PagedTableMixin, tables.DataTableView):
    table_class = project_tables.AdminInstancesTable
    page_title = _("Instances")

    def has_prev_data(self, table):
        return getattr(self, "_prev", False)

    def has_more_data(self, table):
        return self._more

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def _get_tenants(self):
        # Gather our tenants to correlate against IDs
        try:
            tenants, __ = api.keystone.tenant_list(self.request)
            return dict((t.id, t) for t in tenants)
        except Exception:
            msg = _('Unable to retrieve instance project information.')
            exceptions.handle(self.request, msg)
            return {}

    def _get_images(self, instances=()):
        # Gather our images to correlate our instances to them
        try:
            # NOTE(aarefiev): request images, instances was booted from.
            img_ids = (instance.image.get('id') for instance in
                       instances if isinstance(instance.image, dict))
            real_img_ids = list(filter(None, img_ids))
            images = api.glance.image_list_detailed_by_ids(
                self.request, real_img_ids)
            image_map = dict((image.id, image) for image in images)
            return image_map
        except Exception:
            exceptions.handle(self.request, ignore=True)
            return {}

    def _get_flavors(self):
        # Gather our flavors to correlate against IDs
        try:
            flavors = api.nova.flavor_list(self.request)
            return dict((str(flavor.id), flavor) for flavor in flavors)
        except Exception:
            msg = _("Unable to retrieve flavor list.")
            exceptions.handle(self.request, msg)
            return {}

    def _get_instances(self, search_opts, sort_dir):
        try:
            instances, self._more, self._prev = api.nova.server_list_paged(
                self.request,
                search_opts=search_opts,
                sort_dir=sort_dir)
        except Exception:
            self._more = self._prev = False
            instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        return instances

    def get_data(self):
        marker, sort_dir = self._get_marker()
        default_search_opts = {'marker': marker,
                               'paginate': True,
                               'all_tenants': True}

        search_opts = self.get_filters(default_search_opts.copy())

        # If filter_first is set and if there are not other filters
        # selected, then search criteria must be provided and return an empty
        # list
        if (setting_utils.get_dict_config('FILTER_DATA_FIRST',
                                          'admin.instances') and
                len(search_opts) == len(default_search_opts)):
            self._needs_filter_first = True
            self._more = False
            return []

        self._needs_filter_first = False

        instances = self._get_instances(search_opts, sort_dir)
        results = futurist_utils.call_functions_parallel(
            (self._get_images, [tuple(instances)]),
            self._get_flavors,
            self._get_tenants)
        image_dict, flavor_dict, tenant_dict = results

        non_api_filter_info = (
            ('project', 'tenant_id', tenant_dict.values()),
            ('image_name', 'image', image_dict.values()),
            ('flavor_name', 'flavor', flavor_dict.values()),
        )
        if not views.process_non_api_filters(search_opts, non_api_filter_info):
            self._more = False
            return []

        # Loop through instances to get image, flavor and tenant info.
        for inst in instances:
            if hasattr(inst, 'image') and isinstance(inst.image, dict):
                image_id = inst.image.get('id')
                if image_id in image_dict:
                    inst.image = image_dict[image_id]
                # In case image not found in image_map, set name to empty
                # to avoid fallback API call to Glance in api/nova.py
                # until the call is deprecated in api itself
                else:
                    inst.image['name'] = _("-")

            flavor_id = inst.flavor["id"]
            try:
                if flavor_id in flavor_dict:
                    inst.full_flavor = flavor_dict[flavor_id]
                else:
                    # If the flavor_id is not in flavor_dict list,
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
            services = api.nova.service_list(self.request,
                                             binary='nova-compute')
            return [s.host for s in services]
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


class RescueView(views.RescueView):
    form_class = project_forms.RescueInstanceForm
    submit_url = "horizon:admin:instances:rescue"
    success_url = reverse_lazy('horizon:admin:instances:index')
    template_name = 'admin/instances/rescue.html'

    def get_initial(self):
        return {'instance_id': self.kwargs["instance_id"]}
