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

from horizon import exceptions
from horizon import tables

from openstack_dashboard.api import keystone
from openstack_dashboard.dashboards.project.volume_groups \
    import tables as project_tables


class DeleteGroup(project_tables.DeleteGroup):
    url = "horizon:admin:volume_groups:delete"


class RemoveAllVolumes(project_tables.RemoveAllVolumes):
    url = "horizon:admin:volume_groups:remove_volumes"


class UpdateRow(project_tables.UpdateRow):
    ajax = True

    def get_data(self, request, group_id):
        group = super(UpdateRow, self).get_data(request, group_id)
        tenant_id = getattr(group, 'project_id')
        try:
            tenant = keystone.tenant_get(request, tenant_id)
            group.tenant_name = getattr(tenant, "name")
        except Exception:
            msg = _('Unable to retrieve volume group project information.')
            exceptions.handle(request, msg)

        return group


class ManageVolumes(project_tables.ManageVolumes):
    url = "horizon:admin:volume_groups:manage"


class GroupsTable(project_tables.GroupsTable):
    name = tables.WrappingColumn("name_or_id",
                                 verbose_name=_("Name"),
                                 link="horizon:admin:volume_groups:detail")
    project = tables.Column("tenant_name", verbose_name=_("Project"))

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
        row_class = UpdateRow
        status_columns = ("status",)
        columns = ('project', 'name', 'description', 'status',
                   'availability_zone', 'volume_type', 'has_snapshots',)
