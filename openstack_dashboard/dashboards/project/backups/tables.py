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
from django.utils import html
from django.utils import http
from django.utils import safestring
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.utils.translation import pgettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.api import cinder


DELETABLE_STATES = ("available", "error",)


class BackupVolumeNameColumn(tables.Column):
    def get_raw_data(self, backup):
        volume = backup.volume
        if volume:
            volume_name = volume.name
            volume_name = html.escape(volume_name)
        else:
            volume_name = _("Unknown")
        return safestring.mark_safe(volume_name)

    def get_link_url(self, backup):
        volume = backup.volume
        if volume:
            volume_id = volume.id
            return reverse(self.link, args=(volume_id,))


class SnapshotColumn(tables.Column):
    url = "horizon:project:snapshots:detail"

    def get_raw_data(self, backup):
        snapshot = backup.snapshot
        if snapshot:
            snapshot_name = snapshot.name
            snapshot_name = html.escape(snapshot_name)
        elif backup.snapshot_id:
            snapshot_name = _("Unknown")
        else:
            return None
        return safestring.mark_safe(snapshot_name)

    def get_link_url(self, backup):
        if backup.snapshot:
            return reverse(self.url,
                           args=(backup.snapshot_id,))


class DeleteBackup(tables.DeleteAction):
    help_text = _("Deleted volume backups are not recoverable.")
    policy_rules = (("volume", "backup:delete"),)

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Delete Volume Backup",
            "Delete Volume Backups",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Scheduled deletion of Volume Backup",
            "Scheduled deletion of Volume Backups",
            count
        )

    def delete(self, request, obj_id):
        api.cinder.volume_backup_delete(request, obj_id)

    def allowed(self, request, backup=None):
        if backup:
            return backup.status in DELETABLE_STATES
        return True


class RestoreBackup(tables.LinkAction):
    name = "restore"
    verbose_name = _("Restore Backup")
    url = "horizon:project:backups:restore"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "backup:restore"),)

    def allowed(self, request, backup=None):
        return backup.status == "available"

    def get_link_url(self, datum):
        backup_id = datum.id
        backup_name = datum.name
        volume_id = getattr(datum, 'volume_id', None)
        url = reverse(self.url, args=(backup_id,))
        url += '?%s' % http.urlencode({'backup_name': backup_name,
                                       'volume_id': volume_id})
        return url


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, backup_id):
        backup = cinder.volume_backup_get(request, backup_id)
        try:
            backup.volume = cinder.volume_get(request,
                                              backup.volume_id)
        except Exception:
            pass
        if backup.snapshot_id is not None:
            try:
                backup.snapshot = cinder.volume_snapshot_get(
                    request, backup.snapshot_id)
            except Exception:
                pass
        else:
            backup.snapshot = None
        return backup


def get_size(backup):
    return _("%sGB") % backup.size


class BackupsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("available", True),
        ("creating", None),
        ("restoring", None),
        ("error", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available", pgettext_lazy("Current status of a Volume Backup",
                                    "Available")),
        ("error", pgettext_lazy("Current status of a Volume Backup",
                                "Error")),
        ("creating", pgettext_lazy("Current status of a Volume Backup",
                                   "Creating")),
        ("restoring", pgettext_lazy("Current status of a Volume Backup",
                                    "Restoring")),
        ("deleting", pgettext_lazy("Current status of a Volume Backup",
                                   "Deleting")),
        ("error_restoring", pgettext_lazy("Current status of a Volume Backup",
                                          "Error Restoring")),
    )
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:backups:detail")
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                truncate=40)
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    volume_name = BackupVolumeNameColumn("name",
                                         verbose_name=_("Volume Name"),
                                         link="horizon:project:volumes:detail")
    snapshot = SnapshotColumn("snapshot",
                              verbose_name=_("Snapshot"),
                              link="horizon:project:snapshots:detail")

    def current_page(self):
        return self._meta.current_page()

    def number_of_pages(self):
        return self._meta.number_of_pages()

    def get_pagination_string(self):
        return '?%s=' % self._meta.pagination_param

    class Meta(object):
        name = "volume_backups"
        verbose_name = _("Volume Backups")
        pagination_param = 'page'
        status_columns = ("status",)
        row_class = UpdateRow
        table_actions = (DeleteBackup,)
        row_actions = (RestoreBackup, DeleteBackup)


class BackupMessagesTable(tables.DataTable):
    message_id = tables.Column("id", verbose_name=_("ID"))
    message_level = tables.Column("message_level",
                                  verbose_name=_("Message Level"))
    event_id = tables.Column("event_id",
                             verbose_name=_("Event Id"))
    user_message = tables.Column("user_message",
                                 verbose_name=_("User Message"))
    created_at = tables.Column("created_at",
                               verbose_name=_("Created At"))
    guaranteed_until = tables.Column("guaranteed_until",
                                     verbose_name=_("Guaranteed Until"))

    class Meta(object):
        name = "backup_messages"
        verbose_name = _("Messages")
