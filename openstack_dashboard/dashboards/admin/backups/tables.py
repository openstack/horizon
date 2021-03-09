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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.backups \
    import tables as project_tables
from openstack_dashboard import policy


FORCE_DELETABLE_STATES = ("error_deleting", "restoring", "creating")


class AdminSnapshotColumn(project_tables.SnapshotColumn):
    url = "horizon:admin:snapshots:detail"


class AdminDeleteBackup(project_tables.DeleteBackup):
    pass


class ForceDeleteBackup(policy.PolicyTargetMixin, tables.DeleteAction):
    help_text = _("Deleted volume backups are not recoverable.")
    name = "delete_force"
    policy_rules = (("volume",
                     "volume_extension:backup_admin_actions:force_delete"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Force Volume Backup",
            u"Delete Force Volume Backups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled force deletion of Volume Backup",
            u"Scheduled force deletion of Volume Backups",
            count
        )

    def delete(self, request, obj_id):
        api.cinder.volume_backup_delete(request, obj_id, force=True)

    def allowed(self, request, backup=None):
        if backup:
            return backup.status in FORCE_DELETABLE_STATES
        return True


class UpdateRow(project_tables.UpdateRow):
    ajax = True

    def get_data(self, request, backup_id):
        backup = super().get_data(request, backup_id)
        tenant_id = getattr(backup, 'project_id')
        try:
            tenant = api.keystone.tenant_get(request, tenant_id)
            backup.tenant_name = getattr(tenant, "name")
        except Exception:
            msg = _('Unable to retrieve volume backup project information.')
            exceptions.handle(request, msg)

        return backup


class AdminRestoreBackup(project_tables.RestoreBackup):
    url = "horizon:admin:backups:restore"


class UpdateVolumeBackupStatusAction(tables.LinkAction):
    name = "update_status"
    verbose_name = _("Update Volume backup Status")
    url = "horizon:admin:backups:update_status"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume",
                     "volume_extension:backup_admin_actions:reset_status"),)


class AdminBackupsTable(project_tables.BackupsTable):
    project = tables.Column("tenant_name", verbose_name=_("Project"))
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:admin:backups:detail")
    volume_name = project_tables.BackupVolumeNameColumn(
        "name", verbose_name=_("Volume Name"),
        link="horizon:admin:volumes:detail")
    snapshot = AdminSnapshotColumn("snapshot",
                                   verbose_name=_("Snapshot"),
                                   link="horizon:admin:snapshots:detail")

    class Meta(object):
        name = "volume_backups"
        verbose_name = _("Volume Backups")
        pagination_param = 'page'
        status_columns = ("status",)
        row_class = UpdateRow
        table_actions = (AdminDeleteBackup,)
        row_actions = (AdminRestoreBackup, ForceDeleteBackup,
                       AdminDeleteBackup, UpdateVolumeBackupStatusAction,)
        columns = ('project', 'name', 'description', 'size', 'status',
                   'volume_name', 'snapshot',)
