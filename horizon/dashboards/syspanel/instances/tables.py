# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
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

import logging

from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables
from horizon.dashboards.nova.instances_and_volumes.instances.tables import (
        TerminateInstance, EditInstance, ConsoleLink, LogLink, SnapshotLink,
        TogglePause, ToggleSuspend, RebootInstance, get_size, UpdateRow,
        get_ips, get_power_state)


LOG = logging.getLogger(__name__)


class AdminUpdateRow(UpdateRow):
    def get_data(self, request, instance_id):
        instance = super(AdminUpdateRow, self).get_data(request, instance_id)
        tenant = api.keystone.tenant_get(request,
                                         instance.tenant_id,
                                         admin=True)
        instance.tenant_name = getattr(tenant, "name", None)
        return instance


class SyspanelInstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )
    STATUS_CHOICES = (
        ("active", True),
        ("error", False),
    )
    tenant = tables.Column("tenant_name", verbose_name=_("Tenant"))
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    #user = tables.Column("user_id", verbose_name=_("User"))
    host = tables.Column("OS-EXT-SRV-ATTR:host",
                         verbose_name=_("Host"),
                         classes=('nowrap-col',))
    name = tables.Column("name", link="horizon:nova:instances_and_volumes:" \
                                      "instances:detail",
                         verbose_name=_("Instance Name"))
    ip = tables.Column(get_ips, verbose_name=_("IP Address"))
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         classes=('nowrap-col',))
    status = tables.Column("status",
                           filters=(title,),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         filters=(title,),
                         status=True,
                         status_choices=TASK_STATUS_CHOICES)
    state = tables.Column(get_power_state,
                          filters=(title,),
                          verbose_name=_("Power State"))

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["status", "task"]
        table_actions = (TerminateInstance,)
        row_class = AdminUpdateRow
        row_actions = (EditInstance, ConsoleLink, LogLink, SnapshotLink,
                       TogglePause, ToggleSuspend, RebootInstance,
                       TerminateInstance)
