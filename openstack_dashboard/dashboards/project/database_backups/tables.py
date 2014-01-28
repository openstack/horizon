# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Rackspace Hosting
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

from django.core.urlresolvers import reverse
from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters

from openstack_dashboard import api


STATUS_CHOICES = (
    ("BUILDING", None),
    ("COMPLETED", True),
    ("DELETE_FAILED", False),
    ("FAILED", False),
    ("NEW", None),
    ("SAVING", None),
)


class LaunchLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Backup")
    url = "horizon:project:database_backups:create"
    classes = ("btn-launch", "ajax-modal")


class RestoreLink(tables.LinkAction):
    name = "restore"
    verbose_name = _("Restore Backup")
    url = "horizon:project:databases:launch"
    classes = ("btn-launch", "ajax-modal")

    def allowed(self, request, backup=None):
        return backup.status == 'COMPLETED'

    def get_link_url(self, datum):
        url = reverse(self.url)
        return url + '?backup=%s' % datum.id


class DownloadBackup(tables.LinkAction):
    name = "download"
    verbose_name = _("Download Backup")
    url = 'horizon:project:containers:object_download'
    classes = ("btn-launch",)

    def get_link_url(self, datum):
        ref = datum.locationRef.split('/')
        container_name = ref[5]
        object_path = '/'.join(ref[6:])
        return reverse(self.url,
                       kwargs={'container_name': container_name,
                               'object_path': object_path})

    def allowed(self, request, datum):
        return datum.status == 'COMPLETED'


class DeleteBackup(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("Backup")
    data_type_plural = _("Backups")
    classes = ('btn-danger', 'btn-terminate')

    def action(self, request, obj_id):
        api.trove.backup_delete(request, obj_id)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, backup_id):
        backup = api.trove.backup_get(request, backup_id)
        try:
            backup.instance = api.trove.instance_get(request,
                                                     backup.instance_id)
        except Exception:
            pass
        return backup


def db_link(obj):
    if not hasattr(obj, 'instance'):
        return
    if hasattr(obj.instance, 'name'):
        return reverse(
            'horizon:project:databases:detail',
            kwargs={'instance_id': obj.instance_id})


def db_name(obj):
    if hasattr(obj.instance, 'name'):
        return obj.instance.name
    return obj.instance_id


class BackupsTable(tables.DataTable):
    name = tables.Column("name",
                         link=("horizon:project:database_backups:detail"),
                         verbose_name=_("Name"))
    created = tables.Column("created", verbose_name=_("Created At"),
                            filters=[filters.parse_isotime])
    instance = tables.Column(db_name, link=db_link,
                             verbose_name=_("Database"))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

    class Meta:
        name = "backups"
        verbose_name = _("Backups")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (LaunchLink, DeleteBackup)
        row_actions = (RestoreLink, DownloadBackup, DeleteBackup)
