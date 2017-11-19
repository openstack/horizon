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

"""
Admin views for managing volumes and snapshots.
"""
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.dashboards.admin.volumes \
    import forms as volumes_forms
from openstack_dashboard.dashboards.admin.volumes \
    import tables as volumes_tables
from openstack_dashboard.dashboards.admin.volumes \
    import tabs as volumes_tabs
from openstack_dashboard.dashboards.project.volumes \
    import views as volumes_views


class VolumesView(tables.PagedTableMixin, volumes_views.VolumeTableMixIn,
                  tables.DataTableView):
    table_class = volumes_tables.VolumesTable
    page_title = _("Volumes")

    FILTERS_MAPPING = {'bootable': {_('yes'): 'true', _('no'): 'false'},
                       'encrypted': {_('yes'): True, _('no'): False}}

    def get_data(self):
        default_filters = {'all_tenants': True}

        filters = self.get_filters(default_filters.copy())
        filter_first = getattr(settings, 'FILTER_DATA_FIRST', {})
        volumes = []

        self.table.needs_filter_first = False

        if filter_first.get('admin.volumes', False) and \
                len(filters) == len(default_filters):
            self.table.needs_filter_first = True
            return volumes

        if 'project' in filters:
            # Keystone returns a tuple ([],false) where the first element is
            # tenant list that's why the 0 is hardcoded below
            tenants = keystone.tenant_list(self.request)[0]
            tenant_ids = [t.id for t in tenants
                          if t.name == filters['project']]
            if not tenant_ids:
                return []
            del filters['project']
            for id in tenant_ids:
                filters['project_id'] = id
                volumes += self._get_volumes(search_opts=filters)
        else:
            volumes = self._get_volumes(search_opts=filters)

        attached_instance_ids = self._get_attached_instance_ids(volumes)
        instances = self._get_instances(search_opts={'all_tenants': True},
                                        instance_ids=attached_instance_ids)
        volume_ids_with_snapshots = self._get_volumes_ids_with_snapshots(
            search_opts={'all_tenants': True})
        self._set_volume_attributes(
            volumes, instances, volume_ids_with_snapshots)

        # Gather our tenants to correlate against IDs
        try:
            tenants, has_more = keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve volume project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = OrderedDict([(t.id, t) for t in tenants])
        for volume in volumes:
            tenant_id = getattr(volume, "os-vol-tenant-attr:tenant_id", None)
            tenant = tenant_dict.get(tenant_id, None)
            volume.tenant_name = getattr(tenant, "name", None)

        return volumes

    def get_filters(self, filters):
        self.table = self._tables['volumes']
        self.handle_server_filter(self.request, table=self.table)
        self.update_server_filter_action(self.request, table=self.table)
        filters = super(VolumesView, self).get_filters(filters,
                                                       self.FILTERS_MAPPING)
        return filters


class DetailView(volumes_views.DetailView):
    tab_group_class = volumes_tabs.VolumeDetailTabs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = volumes_tables.VolumesTable(self.request)
        context["actions"] = table.render_row_actions(context["volume"])
        return context

    def get_redirect_url(self):
        return reverse('horizon:admin:volumes:index')


class ManageVolumeView(forms.ModalFormView):
    form_class = volumes_forms.ManageVolume
    template_name = 'admin/volumes/manage_volume.html'
    form_id = "manage_volume_modal"
    submit_label = _("Manage")
    success_url = reverse_lazy('horizon:admin:volumes:index')
    submit_url = reverse_lazy('horizon:admin:volumes:manage')
    cancel_url = reverse_lazy("horizon:admin:volumes:index")
    page_title = _("Manage Volume")

    def get_context_data(self, **kwargs):
        context = super(ManageVolumeView, self).get_context_data(**kwargs)
        return context


class UnmanageVolumeView(forms.ModalFormView):
    form_class = volumes_forms.UnmanageVolume
    template_name = 'admin/volumes/unmanage_volume.html'
    form_id = "unmanage_volume_modal"
    submit_label = _("Unmanage")
    success_url = reverse_lazy('horizon:admin:volumes:index')
    submit_url = 'horizon:admin:volumes:unmanage'
    cancel_url = reverse_lazy("horizon:admin:volumes:index")
    page_title = _("Unmanage Volume")

    def get_context_data(self, **kwargs):
        context = super(UnmanageVolumeView, self).get_context_data(**kwargs)
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=self.success_url)
        return volume

    def get_initial(self):
        volume = self.get_data()
        return {'volume_id': self.kwargs["volume_id"],
                'name': volume.name,
                'host': getattr(volume, "os-vol-host-attr:host")}


class MigrateVolumeView(forms.ModalFormView):
    form_class = volumes_forms.MigrateVolume
    template_name = 'admin/volumes/migrate_volume.html'
    form_id = "migrate_volume_modal"
    submit_label = _("Migrate")
    success_url = reverse_lazy('horizon:admin:volumes:index')
    submit_url = 'horizon:admin:volumes:migrate'
    cancel_url = reverse_lazy("horizon:admin:volumes:index")
    page_title = _("Migrate Volume")

    def get_context_data(self, **kwargs):
        context = super(MigrateVolumeView, self).get_context_data(**kwargs)
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=self.success_url)
        return volume

    @memoized.memoized_method
    def get_hosts(self):
        try:
            return cinder.pool_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve pools information.'),
                              redirect=self.success_url)

    def get_initial(self):
        volume = self.get_data()
        return {'volume_id': self.kwargs["volume_id"],
                'name': volume.name,
                'current_host': getattr(volume, "os-vol-host-attr:host"),
                'hosts': self.get_hosts()}


class UpdateStatusView(forms.ModalFormView):
    form_class = volumes_forms.UpdateStatus
    modal_id = "update_volume_status_modal"
    template_name = 'admin/volumes/update_status.html'
    submit_label = _("Update Status")
    submit_url = "horizon:admin:volumes:update_status"
    success_url = reverse_lazy('horizon:admin:volumes:index')
    page_title = _("Update Volume Status")

    def get_context_data(self, **kwargs):
        context = super(UpdateStatusView, self).get_context_data(**kwargs)
        context["volume_id"] = self.kwargs['volume_id']
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=self.success_url)
        return volume

    def get_initial(self):
        volume = self.get_data()
        return {'volume_id': self.kwargs["volume_id"],
                'status': volume.status}
