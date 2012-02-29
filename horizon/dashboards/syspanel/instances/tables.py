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

from django import template
from django.template.defaultfilters import title
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _

from horizon import api
from horizon import tables
from horizon.dashboards.nova.instances_and_volumes.instances.tables import \
         (LaunchLink, TerminateInstance, EditInstance, ConsoleLink, LogLink,
          SnapshotLink, TogglePause, ToggleSuspend, RebootInstance, get_size,
          TerminateInstance, UpdateRow, get_ips, get_power_state)
from horizon.templatetags import sizeformat

LOG = logging.getLogger(__name__)


class SyspanelInstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )
    tenant = tables.Column("tenant_name", verbose_name=_("Tenant"))
    user = tables.Column("user_id", verbose_name=_("User"))
    internal_id = tables.Column("internal_identifier",
                                  verbose_name=_("Instance ID"))
    host = tables.Column("OS-EXT-SRV-ATTR:host", verbose_name=_("Host"))
    name = tables.Column("name", link="horizon:nova:instances_and_volumes:" \
                                      "instances:detail")
    ip = tables.Column(get_ips, verbose_name=_("IP Address"))
    size = tables.Column(get_size, verbose_name=_("Size"))
    status = tables.Column("status", filters=(title,))
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
        status_column = "task"
        table_actions = (LaunchLink, TerminateInstance)
        row_actions = (EditInstance, ConsoleLink, LogLink, SnapshotLink,
                       TogglePause, ToggleSuspend, RebootInstance,
                       TerminateInstance, UpdateRow)
