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
from django.template.defaultfilters import title  # noqa
from django.utils import html
from django.utils import http
from django.utils import safestring
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

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


class DeleteBackup(tables.DeleteAction):
    policy_rules = (("volume", "backup:delete"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Volume Backup",
            u"Delete Volume Backups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Volume Backup",
            u"Scheduled deletion of Volume Backups",
            count
        )

    def delete(self, request, obj_id):
        api.cinder.volume_backup_delete(request, obj_id)

    def allowed(self, request, volume=None):
        if volume:
            return volume.status in DELETABLE_STATES
        return True


class RestoreBackup(tables.LinkAction):
    name = "restore"
    verbose_name = _("Restore Backup")
    classes = ("ajax-modal",)
    policy_rules = (("volume", "backup:restore"),)

    def allowed(self, request, volume=None):
        return volume.status == "available"

    def get_link_url(self, datum):
        backup_id = datum.id
        backup_name = datum.name
        volume_id = getattr(datum, 'volume_id', None)
        url = reverse("horizon:project:volumes:backups:restore",
                      args=(backup_id,))
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
                                    u"Available")),
        ("error", pgettext_lazy("Current status of a Volume Backup",
                                u"Error")),
        ("creating", pgettext_lazy("Current status of a Volume Backup",
                                   u"Creating")),
        ("restoring", pgettext_lazy("Current status of a Volume Backup",
                                    u"Restoring")),
        ("deleting", pgettext_lazy("Current status of a Volume Backup",
                                   u"Deleting")),
        ("error_restoring", pgettext_lazy("Current status of a Volume Backup",
                                          u"Error Restoring")),
    )
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:volumes:backups:detail")
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
                                         link="horizon:project"
                                              ":volumes:volumes:detail")

    class Meta(object):
        name = "volume_backups"
        verbose_name = _("Volume Backups")
        pagination_param = 'backup_marker'
        prev_pagination_param = 'prev_backup_marker'
        status_columns = ("status",)
        row_class = UpdateRow
        table_actions = (DeleteBackup,)
        row_actions = (RestoreBackup, DeleteBackup)
