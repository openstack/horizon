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

import logging

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.admin.backups \
    import forms as admin_forms
from openstack_dashboard.dashboards.admin.backups \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.backups \
    import tabs as admin_tabs
from openstack_dashboard.dashboards.project.backups \
    import views as project_views
from openstack_dashboard.dashboards.project.volumes \
    import views as volumes_views

LOG = logging.getLogger(__name__)


class AdminBackupsView(tables.PagedTableWithPageMenu, tables.DataTableView,
                       volumes_views.VolumeTableMixIn):
    table_class = admin_tables.AdminBackupsTable
    page_title = _("Volume Backups")

    def allowed(self, request):
        return api.cinder.volume_backup_supported(self.request)

    def get_data(self):
        try:
            search_opts = {'all_tenants': 1}
            self._current_page = self._get_page_number()
            (backups, self._page_size, self._total_of_entries,
             self._number_of_pages) = \
                api.cinder.volume_backup_list_paged_with_page_menu(
                    self.request, page_number=self._current_page,
                    all_tenants=True)
        except Exception as e:
            LOG.exception(e)
            backups = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume backups."))
        if not backups:
            return backups
        volumes = api.cinder.volume_list(self.request, search_opts=search_opts)
        volumes = dict((v.id, v) for v in volumes)
        snapshots = api.cinder.volume_snapshot_list(self.request,
                                                    search_opts=search_opts)
        snapshots = dict((s.id, s) for s in snapshots)

        # Gather our tenants to correlate against Backup IDs
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve volume backup project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = dict((t.id, t) for t in tenants)
        for backup in backups:
            backup.volume = volumes.get(backup.volume_id)
            backup.snapshot = snapshots.get(backup.snapshot_id)
            tenant_id = getattr(backup, "project_id", None)
            tenant = tenant_dict.get(tenant_id)
            backup.tenant_name = getattr(tenant, "name", None)
        return backups


class UpdateStatusView(forms.ModalFormView):
    form_class = admin_forms.UpdateStatus
    modal_id = "update_backup_status_modal"
    template_name = 'admin/backups/update_status.html'
    submit_label = _("Update Status")
    submit_url = "horizon:admin:backups:update_status"
    success_url = reverse_lazy('horizon:admin:backups:index')
    page_title = _("Update Volume backup Status")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["backup_id"] = self.kwargs['backup_id']
        args = (self.kwargs['backup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            backup_id = self.kwargs['backup_id']
            backup = cinder.volume_backup_get(self.request, backup_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume backup details.'),
                              redirect=self.success_url)
        return backup

    def get_initial(self):
        backup = self.get_data()
        return {'backup_id': self.kwargs["backup_id"],
                'status': backup.status}


class AdminBackupDetailView(project_views.BackupDetailView):
    tab_group_class = admin_tabs.AdminBackupDetailTabs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = admin_tables.AdminBackupsTable(self.request)
        context["actions"] = table.render_row_actions(context["backup"])
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:admin:backups:index')


class AdminRestoreBackupView(project_views.RestoreBackupView):
    form_class = admin_forms.AdminRestoreBackupForm
    submit_url = "horizon:admin:backups:restore"
    success_url = reverse_lazy('horizon:admin:volumes:index')
