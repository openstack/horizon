# Copyright 2019 NEC Corporation
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

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.project.vg_snapshots  \
    import tables as project_tables


class GroupSnapshotsTable(project_tables.GroupSnapshotsTable):
    # TODO(vishalmanchanda): Add Project Info.column in table
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:admin:vg_snapshots:detail")
    group = project_tables.GroupNameColumn(
        "name", verbose_name=_("Group"),
        link="horizon:admin:volume_groups:detail")

    class Meta(object):
        name = "volume_vg_snapshots"
        verbose_name = _("Group Snapshots")
        table_actions = (
            project_tables.GroupSnapshotsFilterAction,
            project_tables.DeleteGroupSnapshot,
        )
        row_actions = (
            project_tables.DeleteGroupSnapshot,
        )
        row_class = project_tables.UpdateRow
        status_columns = ("status",)
