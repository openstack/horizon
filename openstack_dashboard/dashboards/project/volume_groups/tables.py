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

from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard.api import cinder
from openstack_dashboard import policy


class CreateGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Create Group")
    url = "horizon:project:volume_groups:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "group:create"),)


class DeleteGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "deletecg"
    verbose_name = _("Delete Group")
    url = "horizon:project:volume_groups:delete"
    classes = ("ajax-modal", "btn-danger")
    policy_rules = (("volume", "group:delete"), )

    def allowed(self, request, datum=None):
        if datum and datum.has_snapshots:
            return False
        return True


class RemoveAllVolumes(policy.PolicyTargetMixin, tables.LinkAction):
    name = "remove_vols"
    verbose_name = _("Remove Volumes from Group")
    url = "horizon:project:volume_groups:remove_volumes"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "group:update"), )


class EditGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Group")
    url = "horizon:project:volume_groups:update"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "group:update"),)


class ManageVolumes(policy.PolicyTargetMixin, tables.LinkAction):
    name = "manage"
    verbose_name = _("Manage Volumes")
    url = "horizon:project:volume_groups:manage"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "group:update"),)

    def allowed(self, request, group=None):
        if hasattr(group, 'status'):
            return group.status != 'error'
        else:
            return False


class CreateSnapshot(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create_snapshot"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:volume_groups:create_snapshot"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "group:create_group_snapshot"),)

    def allowed(self, request, group=None):
        if hasattr(group, 'status'):
            return group.status != 'error'
        else:
            return False


class CloneGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "clone_group"
    verbose_name = _("Clone Group")
    url = "horizon:project:volume_groups:clone_group"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "group:create"),)

    def allowed(self, request, group=None):
        if hasattr(group, 'status'):
            return group.status != 'error'
        else:
            return False


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, group_id):
        group = cinder.group_get_with_vol_type_names(request, group_id)
        search_opts = {'group_id': group_id}
        try:
            group_snapshots = cinder.group_snapshot_list(
                request, search_opts=search_opts)
            group.has_snapshots = bool(group_snapshots)
        except Exception:
            exceptions.handle(request, _('Unable to retrieve group details.'))
            group.has_snapshots = False
        return group


class GroupsFilterAction(tables.FilterAction):

    def filter(self, table, groups, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [group for group in groups
                if query in group.name.lower()]


def get_volume_types(group):
    vtypes_str = ''
    if hasattr(group, 'volume_type_names'):
        vtypes_str = ",".join(group.volume_type_names)
    return vtypes_str


class GroupsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available",
         pgettext_lazy("Current status of Volume Group", u"Available")),
        ("in-use",
         pgettext_lazy("Current status of Volume Group", u"In-use")),
        ("error",
         pgettext_lazy("Current status of Volume Group", u"Error")),
        ("updating",
         pgettext_lazy("Current status of Volume Group", u"Updating")),
        ("deleting",
         pgettext_lazy("Current status of Volume Group", u"Deleting")),
    )

    name = tables.WrappingColumn("name_or_id",
                                 verbose_name=_("Name"),
                                 link="horizon:project:volume_groups:detail")
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                truncate=40)
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    availability_zone = tables.Column("availability_zone",
                                      verbose_name=_("Availability Zone"))
    volume_type = tables.Column(get_volume_types,
                                verbose_name=_("Volume Type(s)"))
    has_snapshots = tables.Column("has_snapshots",
                                  verbose_name=_("Has Snapshots"),
                                  filters=(filters.yesno,))

    def get_object_id(self, group):
        return group.id

    class Meta(object):
        name = "volume_groups"
        verbose_name = _("Volume Groups")
        table_actions = (
            CreateGroup,
            GroupsFilterAction,
        )
        row_actions = (
            CreateSnapshot,
            ManageVolumes,
            EditGroup,
            CloneGroup,
            RemoveAllVolumes,
            DeleteGroup,
        )
        row_class = UpdateRow
        status_columns = ("status",)
