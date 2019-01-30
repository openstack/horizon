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

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.api import cinder
from openstack_dashboard import policy


class CreateVolumeCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create_cgroup"
    verbose_name = _("Create Consistency Group")
    url = "horizon:project:cg_snapshots:create_cgroup"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:create"),)


class DeleteVolumeCGSnapshot(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "delete_cg_snapshot"
    policy_rules = (("volume", "consistencygroup:delete_cgsnapshot"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Snapshot",
            u"Delete Snapshots",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Snapshot",
            u"Scheduled deletion of Snapshots",
            count
        )

    def delete(self, request, obj_id):
        cinder.volume_cg_snapshot_delete(request, obj_id)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, cg_snapshot_id):
        cg_snapshot = cinder.volume_cg_snapshot_get(request, cg_snapshot_id)
        return cg_snapshot


class VolumeCGSnapshotsFilterAction(tables.FilterAction):

    def filter(self, table, cg_snapshots, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [cg_snapshot for cg_snapshot in cg_snapshots
                if query in cg_snapshot.name.lower()]


class CGSnapshotsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available",
         pgettext_lazy("Current status of Consistency Group Snapshot",
                       u"Available")),
        ("in-use",
         pgettext_lazy("Current status of Consistency Group Snapshot",
                       u"In-use")),
        ("error",
         pgettext_lazy("Current status of Consistency Group Snapshot",
                       u"Error")),
    )

    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:"
                              "cg_snapshots:cg_snapshot_detail")
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                truncate=40)
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    def get_object_id(self, cg_snapshot):
        return cg_snapshot.id

    class Meta(object):
        name = "volume_cg_snapshots"
        verbose_name = _("Consistency Group Snapshots")
        table_actions = (VolumeCGSnapshotsFilterAction,
                         DeleteVolumeCGSnapshot)
        row_actions = (CreateVolumeCGroup,
                       DeleteVolumeCGSnapshot,)
        row_class = UpdateRow
        status_columns = ("status",)
        permissions = [
            ('openstack.services.volume', 'openstack.services.volumev2')
        ]
