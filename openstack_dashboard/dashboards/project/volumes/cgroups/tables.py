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
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard.api import cinder
from openstack_dashboard import policy


class CreateVolumeCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Create Consistency Group")
    url = "horizon:project:volumes:cgroups:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "consistencygroup:create"),)


class DeleteVolumeCGroup(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletecg"
    policy_rules = (("volume", "consistencygroup:delete"), )

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Consistency Group",
            u"Delete Consistency Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Consistency Group",
            u"Scheduled deletion of Consistency Groups",
            count
        )

    def delete(self, request, cgroup_id):
        try:
            cinder.volume_cgroup_delete(request,
                                        cgroup_id,
                                        force=False)
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to delete consistency group.'),
                              redirect=redirect)


class EditVolumeCGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Consistency Group")
    url = "horizon:project:volumes:cgroups:update"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:update"),)


class ManageVolumes(policy.PolicyTargetMixin, tables.LinkAction):
    name = "manage"
    verbose_name = _("Manage Volumes")
    url = "horizon:project:volumes:cgroups:manage"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "consistencygroup:update"),)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, cgroup_id):
        cgroup = cinder.volume_cgroup_get(request, cgroup_id)
        return cgroup


class VolumeCGroupsFilterAction(tables.FilterAction):

    def filter(self, table, cgroups, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [cgroup for cgroup in cgroups
                if query in cgroup.name.lower()]


def get_volume_types(cgroup):
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

    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:volumes:cgroups:detail")
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
                       DeleteVolumeCGroup)
        row_class = UpdateRow
        status_columns = ("status",)
        permissions = ['openstack.services.volume']
