# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone

from openstack_dashboard.dashboards.admin.snapshots \
    import forms as vol_snapshot_forms
from openstack_dashboard.dashboards.admin.snapshots \
    import tables as vol_snapshot_tables
from openstack_dashboard.dashboards.admin.snapshots \
    import tabs as vol_snapshot_tabs
from openstack_dashboard.dashboards.project.snapshots \
    import views


class SnapshotsView(tables.PagedTableMixin, tables.DataTableView):
    table_class = vol_snapshot_tables.VolumeSnapshotsTable
    page_title = _("Volume Snapshots")

    def get_data(self):
        needs_gs = False
        if cinder.is_volume_service_enabled(self.request):
            try:
                marker, sort_dir = self._get_marker()
                snapshots, self._has_more_data, self._has_prev_data = \
                    cinder.volume_snapshot_list_paged(
                        self.request, paginate=True, marker=marker,
                        sort_dir=sort_dir, search_opts={'all_tenants': True})
                volumes = cinder.volume_list(
                    self.request,
                    search_opts={'all_tenants': True})
                volumes = dict((v.id, v) for v in volumes)
            except Exception:
                snapshots = []
                volumes = {}
                exceptions.handle(self.request, _("Unable to retrieve "
                                                  "volume snapshots."))

            needs_gs = any(getattr(snapshot, 'group_snapshot_id', None)
                           for snapshot in snapshots)
            if needs_gs:
                try:
                    group_snapshots = cinder.group_snapshot_list(
                        self.request, search_opts={'all_tenants': True})
                    group_snapshots = dict((gs.id, gs) for gs
                                           in group_snapshots)
                except Exception:
                    group_snapshots = {}
                    exceptions.handle(self.request,
                                      _("Unable to retrieve group snapshots."))
            # Gather our tenants to correlate against volume IDs
            try:
                tenants, has_more = keystone.tenant_list(self.request)
            except Exception:
                tenants = []
                msg = _('Unable to retrieve project '
                        'information of volume snapshots.')
                exceptions.handle(self.request, msg)

            tenant_dict = dict((t.id, t) for t in tenants)
            for snapshot in snapshots:
                volume = volumes.get(snapshot.volume_id)
                if needs_gs:
                    group_snapshot = group_snapshots.get(
                        snapshot.group_snapshot_id)
                    snapshot.group_snapshot = group_snapshot
                else:
                    snapshot.group_snapshot = None
                tenant_id = snapshot.project_id
                tenant = tenant_dict.get(tenant_id, None)
                snapshot._volume = volume
                snapshot.tenant_name = getattr(tenant, "name", None)
                snapshot.host_name = getattr(
                    volume, 'os-vol-host-attr:host', None)

        else:
            snapshots = []
        return snapshots


class UpdateStatusView(forms.ModalFormView):
    form_class = vol_snapshot_forms.UpdateStatus
    modal_id = "update_volume_snapshot_status"
    template_name = 'admin/snapshots/update_status.html'
    submit_label = _("Update Status")
    submit_url = "horizon:admin:snapshots:update_status"
    success_url = reverse_lazy("horizon:admin:snapshots:index")
    page_title = _("Update Volume Snapshot Status")

    @memoized.memoized_method
    def get_object(self):
        snap_id = self.kwargs['snapshot_id']
        try:
            self._object = cinder.volume_snapshot_get(self.request,
                                                      snap_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume snapshot.'),
                              redirect=self.success_url)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateStatusView, self).get_context_data(**kwargs)
        context['snapshot_id'] = self.kwargs["snapshot_id"]
        args = (self.kwargs['snapshot_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        snapshot = self.get_object()
        return {'snapshot_id': self.kwargs["snapshot_id"],
                'status': snapshot.status}


class DetailView(views.DetailView):
    tab_group_class = vol_snapshot_tabs.SnapshotDetailsTabs
    volume_url = 'horizon:admin:volumes:detail'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        snapshot = self.get_data()
        snapshot.volume_url = reverse(self.volume_url,
                                      args=(snapshot.volume_id,))
        table = vol_snapshot_tables.VolumeSnapshotsTable(self.request)
        context["snapshot"] = snapshot
        context["actions"] = table.render_row_actions(snapshot)
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:admin:snapshots:index')
