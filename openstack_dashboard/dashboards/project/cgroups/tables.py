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

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard.api import cinder
from openstack_dashboard import policy


class CreateVolumeCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Create Consistency Group")
    url = "horizon:project:cgroups:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "consistencygroup:create"),)


class DeleteVolumeCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "deletecg"
    verbose_name = _("Delete Consistency Group")
    url = "horizon:project:cgroups:delete"
    classes = ("ajax-modal", "btn-danger")
    policy_rules = (("volume", "consistencygroup:delete"), )


class RemoveAllVolumes(policy.PolicyTargetMixin, tables.LinkAction):
    name = "remove_vols"
    verbose_name = _("Remove Volumes from Consistency Group")
    url = "horizon:project:cgroups:remove_volumes"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:update"), )


class EditVolumeCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Consistency Group")
    url = "horizon:project:cgroups:update"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:update"),)


class ManageVolumes(policy.PolicyTargetMixin, tables.LinkAction):
    name = "manage"
    verbose_name = _("Manage Volumes")
    url = "horizon:project:cgroups:manage"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:update"),)

    def allowed(self, request, cgroup=None):
        if hasattr(cgroup, 'status'):
            return cgroup.status != 'error'
        else:
            return False


class CreateSnapshot(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create_snapshot"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:cgroups:create_snapshot"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:create_cgsnapshot"),)

    def allowed(self, request, cgroup=None):
        if hasattr(cgroup, 'status'):
            return cgroup.status != 'error'
        else:
            return False


class CloneCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "clone_cgroup"
    verbose_name = _("Clone Consistency Group")
    url = "horizon:project:cgroups:clone_cgroup"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:create"),)

    def allowed(self, request, cgroup=None):
        if hasattr(cgroup, 'status'):
            return cgroup.status != 'error'
        else:
            return False


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, cgroup_id):
        try:
            cgroup = cinder.volume_cgroup_get_with_vol_type_names(request,
                                                                  cgroup_id)
        except Exception:
            exceptions.handle(request, _('Unable to display '
                                         'consistency group.'))
        return cgroup


class VolumeCGroupsFilterAction(tables.FilterAction):

    def filter(self, table, cgroups, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [cgroup for cgroup in cgroups
                if query in cgroup.name.lower()]


def get_volume_types(cgroup):
    vtypes_str = ''
    if hasattr(cgroup, 'volume_type_names'):
        vtypes_str = ",".join(cgroup.volume_type_names)
    return vtypes_str


class VolumeCGroupsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available",
         pgettext_lazy("Current status of Consistency Group", u"Available")),
        ("in-use",
         pgettext_lazy("Current status of Consistency Group", u"In-use")),
        ("error",
         pgettext_lazy("Current status of Consistency Group", u"Error")),
    )

    name = tables.WrappingColumn("name",
                                 verbose_name=_("Name"),
                                 link="horizon:project:cgroups:detail")
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

    def get_object_id(self, cgroup):
        return cgroup.id

    class Meta(object):
        name = "volume_cgroups"
        verbose_name = _("Volume Consistency Groups")
        table_actions = (CreateVolumeCGroup,
                         VolumeCGroupsFilterAction)
        row_actions = (ManageVolumes,
                       EditVolumeCGroup,
                       CreateSnapshot,
                       CloneCGroup,
                       RemoveAllVolumes,
                       DeleteVolumeCGroup)
        row_class = UpdateRow
        status_columns = ("status",)
        permissions = ['openstack.services.volume']
