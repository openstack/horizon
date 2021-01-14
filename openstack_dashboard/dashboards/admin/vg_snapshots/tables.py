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

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.vg_snapshots  \
    import tables as project_tables


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, vg_snapshot_id):
        vg_snapshot = api.cinder.group_snapshot_get(request, vg_snapshot_id)
        vg_snapshot.group = api.cinder.group_get(request,
                                                 vg_snapshot.group_id)
        tenant_id = getattr(vg_snapshot.group, 'project_id')

        try:
            tenant = api.keystone.tenant_get(request, tenant_id)
            vg_snapshot.tenant_name = getattr(tenant, "name")
        except Exception:
            msg = _('Unable to retrieve group snapshot project information.')
            exceptions.handle(request, msg)

        return vg_snapshot


class GroupSnapshotsTable(project_tables.GroupSnapshotsTable):
    project = tables.Column("tenant_name", verbose_name=_("Project"))
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
        row_class = UpdateRow
        status_columns = ("status",)
        columns = ('project', 'name', 'description', 'status',
                   'group')
