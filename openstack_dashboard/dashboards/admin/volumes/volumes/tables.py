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

from horizon import exceptions
from horizon import tables

from openstack_dashboard.dashboards.project.volumes \
    .volumes import tables as volumes_tables


class VolumesFilterAction(tables.FilterAction):

    def filter(self, table, volumes, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [volume for volume in volumes
                if q in volume.name.lower()]


class ManageVolumeAction(tables.LinkAction):
    name = "manage"
    verbose_name = _("Manage Volume")
    url = "horizon:admin:volumes:volumes:manage"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:volume_manage"),)
    ajax = True


class UnmanageVolumeAction(tables.LinkAction):
    name = "unmanage"
    verbose_name = _("Unmanage Volume")
    url = "horizon:admin:volumes:volumes:unmanage"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:volume_unmanage"),)

    def allowed(self, request, volume=None):
        # don't allow unmanage if volume is attached to instance or
        # volume has snapshots
        if volume:
            if volume.attachments:
                return False

            try:
                return (volume.status in volumes_tables.DELETABLE_STATES and
                        not getattr(volume, 'has_snapshot', False))
            except Exception:
                exceptions.handle(request,
                                  _("Unable to retrieve snapshot data."))
                return False

        return False


class MigrateVolume(tables.LinkAction):
    name = "migrate"
    verbose_name = _("Migrate Volume")
    url = "horizon:admin:volumes:volumes:migrate"
    classes = ("ajax-modal", "btn-migrate")
    policy_rules = (
        ("volume", "volume_extension:volume_admin_actions:migrate_volume"),)

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


class UpdateVolumeStatusAction(tables.LinkAction):
    name = "update_status"
    verbose_name = _("Update Volume Status")
    url = "horizon:admin:volumes:volumes:update_status"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume",
                     "volume_extension:volume_admin_actions:reset_status"),)


class VolumesTable(volumes_tables.VolumesTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:admin:volumes:volumes:detail")
    host = tables.Column("os-vol-host-attr:host", verbose_name=_("Host"))
    tenant = tables.Column(lambda obj: getattr(obj, 'tenant_name', None),
                           verbose_name=_("Project"))

    class Meta(object):
        name = "volumes"
        verbose_name = _("Volumes")
        status_columns = ["status"]
        row_class = volumes_tables.UpdateRow
        table_actions = (ManageVolumeAction,
                         volumes_tables.DeleteVolume,
                         VolumesFilterAction)
        row_actions = (volumes_tables.DeleteVolume,
                       UpdateVolumeStatusAction,
                       UnmanageVolumeAction,
                       MigrateVolume)
        columns = ('tenant', 'host', 'name', 'size', 'status', 'volume_type',
                   'attachments', 'bootable', 'encryption',)
