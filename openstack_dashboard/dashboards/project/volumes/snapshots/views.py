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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.volumes \
    .snapshots import forms as vol_snapshot_forms
from openstack_dashboard.dashboards.project.volumes \
    .snapshots import tables as vol_snapshot_tables
from openstack_dashboard.dashboards.project.volumes \
    .snapshots import tabs as vol_snapshot_tabs


class UpdateView(forms.ModalFormView):
    form_class = vol_snapshot_forms.UpdateForm
    form_id = "update_snapshot_form"
    modal_header = _("Edit Snapshot")
    template_name = 'project/volumes/snapshots/update.html'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:volumes:snapshots:update"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Edit Snapshot")

    @memoized.memoized_method
    def get_object(self):
        snap_id = self.kwargs['snapshot_id']
        try:
            self._object = api.cinder.volume_snapshot_get(self.request,
                                                          snap_id)
        except Exception:
            msg = _('Unable to retrieve volume snapshot.')
            url = reverse('horizon:project:volumes:index')
            exceptions.handle(self.request, msg, redirect=url)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['snapshot'] = self.get_object()
        args = (self.kwargs['snapshot_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        snapshot = self.get_object()
        return {'snapshot_id': self.kwargs["snapshot_id"],
                'name': snapshot.name,
                'description': snapshot.description}


class DetailView(tabs.TabView):
    tab_group_class = vol_snapshot_tabs.SnapshotDetailTabs
    template_name = 'project/volumes/snapshots/detail.html'
    page_title = _("Volume Snapshot Details: {{ snapshot.name }}")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        snapshot = self.get_data()
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
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve snapshot details.'),
                              redirect=redirect)
        return snapshot

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:volumes:index')

    def get_tabs(self, request, *args, **kwargs):
        snapshot = self.get_data()
        return self.tab_group_class(request, snapshot=snapshot, **kwargs)
