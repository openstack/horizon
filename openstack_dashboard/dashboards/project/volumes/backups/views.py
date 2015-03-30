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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.volumes.backups \
    import forms as backup_forms
from openstack_dashboard.dashboards.project.volumes.backups \
    import tables as backup_tables
from openstack_dashboard.dashboards.project.volumes.backups \
    import tabs as backup_tabs


class CreateBackupView(forms.ModalFormView):
    form_class = backup_forms.CreateBackupForm
    modal_header = _("Create Volume Backup")
    template_name = 'project/volumes/backups/create_backup.html'
    submit_label = _("Create Volume Backup")
    submit_url = "horizon:project:volumes:volumes:create_backup"
    success_url = reverse_lazy("horizon:project:volumes:backups_tab")
    page_title = _("Create a Volume Backup")

    def get_context_data(self, **kwargs):
        context = super(CreateBackupView, self).get_context_data(**kwargs)
        context['volume_id'] = self.kwargs['volume_id']
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        return {"volume_id": self.kwargs["volume_id"]}


class BackupDetailView(tabs.TabView):
    tab_group_class = backup_tabs.BackupDetailTabs
    template_name = 'project/volumes/backups/detail.html'
    page_title = _("Volume Backup Details: {{ backup.name }}")

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
        return reverse('horizon:project:volumes:index')


class RestoreBackupView(forms.ModalFormView):
    form_class = backup_forms.RestoreBackupForm
    modal_header = _("Restore Volume Backup")
    template_name = 'project/volumes/backups/restore_backup.html'
    submit_label = _("Restore Backup to Volume")
    submit_url = "horizon:project:volumes:volumes:create_backup"
    success_url = reverse_lazy('horizon:project:volumes:index')
    page_title = _("Restore a Volume Backup")

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
