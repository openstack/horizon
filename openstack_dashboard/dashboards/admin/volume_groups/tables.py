# Copyright 2019 NEC Corporation
#
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

from horizon import tables
from openstack_dashboard.dashboards.project.volume_groups \
    import tables as project_tables


class DeleteGroup(project_tables.DeleteGroup):
    url = "horizon:admin:volume_groups:delete"


class RemoveAllVolumes(project_tables.RemoveAllVolumes):
    url = "horizon:admin:volume_groups:remove_volumes"


class ManageVolumes(project_tables.ManageVolumes):
    url = "horizon:admin:volume_groups:manage"


class GroupsTable(project_tables.GroupsTable):
    # TODO(vishalmanchanda): Add Project Info.column in table
    name = tables.WrappingColumn("name_or_id",
                                 verbose_name=_("Name"),
                                 link="horizon:admin:volume_groups:detail")

    class Meta(object):
        name = "volume_groups"
        verbose_name = _("Volume Groups")
        table_actions = (
            project_tables.GroupsFilterAction,
        )
        row_actions = (
            ManageVolumes,
            RemoveAllVolumes,
            DeleteGroup,
        )
        row_class = project_tables.UpdateRow
        status_columns = ("status",)
