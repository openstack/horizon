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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.snapshots \
    import forms as vol_snapshot_forms
from openstack_dashboard.dashboards.project.snapshots \
    import tables as vol_snapshot_tables
from openstack_dashboard.dashboards.project.snapshots \
    import tabs as vol_snapshot_tabs


class SnapshotsView(tables.PagedTableMixin, tables.DataTableView):
    table_class = vol_snapshot_tables.VolumeSnapshotsTable
    page_title = _("Volume Snapshots")

    def get_data(self):
        snapshots = []
        volumes = {}
        if api.base.is_service_enabled(self.request, 'volumev2'):
            try:
                marker, sort_dir = self._get_marker()
                snapshots, self._has_more_data, self._has_prev_data = \
                    api.cinder.volume_snapshot_list_paged(
                        self.request, paginate=True, marker=marker,
                        sort_dir=sort_dir)
                volumes = api.cinder.volume_list(self.request)
                volumes = dict((v.id, v) for v in volumes)
            except Exception:
                exceptions.handle(self.request, _("Unable to retrieve "
                                                  "volume snapshots."))

        for snapshot in snapshots:
            volume = volumes.get(snapshot.volume_id)
            setattr(snapshot, '_volume', volume)

        return snapshots


class UpdateView(forms.ModalFormView):
    form_class = vol_snapshot_forms.UpdateForm
    form_id = "update_snapshot_form"
    template_name = 'project/snapshots/update.html'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:snapshots:update"
    success_url = reverse_lazy("horizon:project:snapshots:index")
    page_title = _("Edit Snapshot")

    @memoized.memoized_method
    def get_object(self):
        snap_id = self.kwargs['snapshot_id']
        try:
            self._object = api.cinder.volume_snapshot_get(self.request,
                                                          snap_id)
        except Exception:
            msg = _('Unable to retrieve volume snapshot.')
            url = reverse('horizon:project:snapshots:index')
            exceptions.handle(self.request, msg, redirect=url)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['snapshot'] = self.get_object()
        success_url = self.request.GET.get('success_url', "")
        args = (self.kwargs['snapshot_id'],)
        params = urlencode({"success_url": success_url})
        context['submit_url'] = "?".join([reverse(self.submit_url, args=args),
                                          params])
        return context

    def get_initial(self):
        snapshot = self.get_object()
        return {'snapshot_id': self.kwargs["snapshot_id"],
                'name': snapshot.name,
                'description': snapshot.description}

    def get_success_url(self):
        success_url = self.request.GET.get(
            "success_url",
            reverse_lazy("horizon:project:snapshots:index"))
        return success_url


class DetailView(tabs.TabView):
    tab_group_class = vol_snapshot_tabs.SnapshotDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ snapshot.name|default:snapshot.id }}"
    volume_url = 'horizon:project:volumes:detail'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        snapshot = self.get_data()
        snapshot.volume_url = reverse(self.volume_url,
                                      args=(snapshot.volume_id,))
        table = vol_snapshot_tables.VolumeSnapshotsTable(self.request)
        context["snapshot"] = snapshot
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(snapshot)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            snapshot_id = self.kwargs['snapshot_id']
            snapshot = api.cinder.volume_snapshot_get(self.request,
                                                      snapshot_id)
            snapshot._volume = api.cinder.volume_get(self.request,
                                                     snapshot.volume_id)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve snapshot details.'),
                              redirect=redirect)
        return snapshot

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:snapshots:index')

    def get_tabs(self, request, *args, **kwargs):
        snapshot = self.get_data()
        return self.tab_group_class(request, snapshot=snapshot, **kwargs)
