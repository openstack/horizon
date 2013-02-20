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

from horizon import tables
from horizon.utils.filters import replace_underscores

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances.tables import (
        TerminateInstance, EditInstance, ConsoleLink, LogLink, CreateSnapshot,
        TogglePause, ToggleSuspend, RebootInstance, SoftRebootInstance,
        ConfirmResize, RevertResize, get_size, UpdateRow, get_ips,
        get_power_state, is_deleting, ACTIVE_STATES, STATUS_DISPLAY_CHOICES,
        TASK_DISPLAY_CHOICES)

LOG = logging.getLogger(__name__)


class AdminEditInstance(EditInstance):
    url = "horizon:admin:instances:update"


class MigrateInstance(tables.BatchAction):
    name = "migrate"
    action_present = _("Migrate")
    action_past = _("Scheduled migration (pending confirmation) of")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ("btn-migrate", "btn-danger")

    def allowed(self, request, instance):
        return ((instance.status in ACTIVE_STATES
                 or instance.status == 'SHUTOFF')
                and not is_deleting(instance))

    def action(self, request, obj_id):
        api.nova.server_migrate(request, obj_id)


class AdminUpdateRow(UpdateRow):
    def get_data(self, request, instance_id):
        instance = super(AdminUpdateRow, self).get_data(request, instance_id)
        tenant = api.keystone.tenant_get(request,
                                         instance.tenant_id,
                                         admin=True)
        instance.tenant_name = getattr(tenant, "name", None)
        return instance


class AdminInstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )
    STATUS_CHOICES = (
        ("active", True),
        ("shutoff", True),
        ("suspended", True),
        ("paused", True),
        ("error", False),
    )
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    #user = tables.Column("user_id", verbose_name=_("User"))
    host = tables.Column("OS-EXT-SRV-ATTR:host",
                         verbose_name=_("Host"),
                         classes=('nowrap-col',))
    name = tables.Column("name",
                         link=("horizon:admin:instances:detail"),
                         verbose_name=_("Name"))
    ip = tables.Column(get_ips, verbose_name=_("IP Address"))
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         classes=('nowrap-col',),
                         attrs={'data-type': 'size'})
    status = tables.Column("status",
                           filters=(title, replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         filters=(title, replace_underscores),
                         status=True,
                         status_choices=TASK_STATUS_CHOICES,
                         display_choices=TASK_DISPLAY_CHOICES)
    state = tables.Column(get_power_state,
                          filters=(title, replace_underscores),
                          verbose_name=_("Power State"))

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["status", "task"]
        table_actions = (TerminateInstance,)
        row_class = AdminUpdateRow
        row_actions = (ConfirmResize, RevertResize, AdminEditInstance,
                       ConsoleLink, LogLink, CreateSnapshot, TogglePause,
                       ToggleSuspend, MigrateInstance, SoftRebootInstance,
                       RebootInstance, TerminateInstance)
