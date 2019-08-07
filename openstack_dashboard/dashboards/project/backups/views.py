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
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.backups \
    import forms as backup_forms
from openstack_dashboard.dashboards.project.backups \
    import tables as backup_tables
from openstack_dashboard.dashboards.project.backups \
    import tabs as backup_tabs
from openstack_dashboard.dashboards.project.volumes \
    import views as volume_views


class BackupsView(tables.DataTableView, tables.PagedTableMixin,
                  volume_views.VolumeTableMixIn):
    table_class = backup_tables.BackupsTable
    page_title = _("Volume Backups")

    def allowed(self, request):
        return api.cinder.volume_backup_supported(self.request)

    def get_data(self):
        try:
            marker, sort_dir = self._get_marker()
            backups, self._has_more_data, self._has_prev_data = \
                api.cinder.volume_backup_list_paged(
                    self.request, marker=marker, sort_dir=sort_dir,
                    paginate=True)
            volumes = api.cinder.volume_list(self.request)
            volumes = dict((v.id, v) for v in volumes)
            snapshots = api.cinder.volume_snapshot_list(self.request)
            snapshots = dict((s.id, s) for s in snapshots)
            for backup in backups:
                backup.volume = volumes.get(backup.volume_id)
                backup.snapshot = snapshots.get(backup.snapshot_id)
        except Exception:
            backups = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume backups."))
        return backups


class CreateBackupView(forms.ModalFormView):
    form_class = backup_forms.CreateBackupForm
    template_name = 'project/backups/create_backup.html'
    submit_label = _("Create Volume Backup")
    submit_url = "horizon:project:volumes:create_backup"
    success_url = reverse_lazy("horizon:project:backups:index")
    page_title = _("Create Volume Backup")

    def get_context_data(self, **kwargs):
        context = super(CreateBackupView, self).get_context_data(**kwargs)
        context['volume_id'] = self.kwargs['volume_id']
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        if self.kwargs.get('snapshot_id'):
            return {"volume_id": self.kwargs["volume_id"],
                    "snapshot_id": self.kwargs["snapshot_id"]}
        return {"volume_id": self.kwargs["volume_id"]}


class BackupDetailView(tabs.TabView):
    tab_group_class = backup_tabs.BackupDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ backup.name|default:backup.id }}"

    def get_context_data(self, **kwargs):
        context = super(BackupDetailView, self).get_context_data(**kwargs)
        backup = self.get_data()
        table = backup_tables.BackupsTable(self.request)
        context["backup"] = backup
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(backup)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            backup_id = self.kwargs['backup_id']
            backup = api.cinder.volume_backup_get(self.request,
                                                  backup_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve backup details.'),
                              redirect=self.get_redirect_url())
        return backup

    def get_tabs(self, request, *args, **kwargs):
        backup = self.get_data()
        return self.tab_group_class(request, backup=backup, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:backups:index')


class RestoreBackupView(forms.ModalFormView):
    form_class = backup_forms.RestoreBackupForm
    template_name = 'project/backups/restore_backup.html'
    submit_label = _("Restore Backup to Volume")
    submit_url = "horizon:project:backups:restore"
    success_url = reverse_lazy('horizon:project:volumes:index')
    page_title = _("Restore Volume Backup")

    def get_context_data(self, **kwargs):
        context = super(RestoreBackupView, self).get_context_data(**kwargs)
        context['backup_id'] = self.kwargs['backup_id']
        args = (self.kwargs['backup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        backup_id = self.kwargs['backup_id']
        backup_name = self.request.GET.get('backup_name')
        volume_id = self.request.GET.get('volume_id')
        return {
            'backup_id': backup_id,
            'backup_name': backup_name,
            'volume_id': volume_id,
        }
