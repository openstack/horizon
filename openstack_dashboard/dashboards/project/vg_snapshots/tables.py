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

from django.urls import reverse
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard.api import cinder
from openstack_dashboard import policy


class CreateGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create_group"
    verbose_name = _("Create Group")
    url = "horizon:project:vg_snapshots:create_group"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "group:create"),)


class DeleteGroupSnapshot(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "delete_vg_snapshot"
    policy_rules = (("volume", "group:delete_group_snapshot"),)

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
        cinder.group_snapshot_delete(request, obj_id)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, vg_snapshot_id):
        vg_snapshot = cinder.group_snapshot_get(request, vg_snapshot_id)
        if getattr(vg_snapshot, 'group_id', None):
            try:
                vg_snapshot.group = cinder.group_get(request,
                                                     vg_snapshot.group_id)
            except Exception:
                exceptions.handle(request, _("Unable to retrieve group"))
                vg_snapshot.group = None
        return vg_snapshot


class GroupNameColumn(tables.WrappingColumn):
    def get_raw_data(self, snapshot):
        group = snapshot.group
        return group.name_or_id if group else _("-")

    def get_link_url(self, snapshot):
        group = snapshot.group
        if group:
            return reverse(self.link, args=(group.id,))


class GroupSnapshotsFilterAction(tables.FilterAction):

    def filter(self, table, vg_snapshots, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [vg_snapshot for vg_snapshot in vg_snapshots
                if query in vg_snapshot.name.lower()]


class GroupSnapshotsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available",
         pgettext_lazy("Current status of Volume Group Snapshot",
                       u"Available")),
        ("in-use",
         pgettext_lazy("Current status of Volume Group Snapshot",
                       u"In-use")),
        ("error",
         pgettext_lazy("Current status of Volume Group Snapshot",
                       u"Error")),
    )

    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:vg_snapshots:detail")
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                truncate=40)
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    group = GroupNameColumn(
        "name",
        verbose_name=_("Group"),
        link="horizon:project:volume_groups:detail")

    def get_object_id(self, vg_snapshot):
        return vg_snapshot.id

    class Meta(object):
        name = "volume_vg_snapshots"
        verbose_name = _("Group Snapshots")
        table_actions = (GroupSnapshotsFilterAction,
                         DeleteGroupSnapshot)
        row_actions = (CreateGroup,
                       DeleteGroupSnapshot,)
        row_class = UpdateRow
        status_columns = ("status",)
