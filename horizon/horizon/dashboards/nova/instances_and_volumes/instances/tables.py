# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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
from django.utils.translation import ugettext as _

from horizon import api
from horizon import tables
from horizon.templatetags import sizeformat


LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)

POWER_STATES = {
    0: "NO STATE",
    1: "RUNNING",
    2: "BLOCKED",
    3: "PAUSED",
    4: "SHUTDOWN",
    5: "SHUTOFF",
    6: "CRASHED",
    7: "SUSPENDED",
    8: "FAILED",
    9: "BUILDING",
}


class TerminateInstance(tables.BatchAction):
    name = "terminate"
    action_present = _("Terminate")
    action_past = _("Terminated")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('danger',)

    def action(self, request, obj_id):
        api.server_delete(request, obj_id)


class RebootInstance(tables.BatchAction):
    name = "reboot"
    action_present = _("Reboot")
    action_past = _("Rebooted")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('danger',)

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES

    def action(self, request, obj_id):
        api.server_reboot(request, obj_id)


class TogglePause(tables.BatchAction):
    name = "pause"
    action_present = _("Pause")
    action_past = _("Paused")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")

    def allowed(self, request, instance=None):
        if not instance:
            return True
        self.paused = instance.status == "PAUSED"
        if self.paused:
            self.action_present = _("Unpause")
            self.action_past = _("Unpaused")
        return instance.status in ACTIVE_STATES

    def action(self, request, obj_id):
        if getattr(self, 'paused', False):
            api.server_pause(request, obj_id)
        else:
            api.server_unpause(request, obj_id)


class ToggleSuspend(tables.BatchAction):
    name = "suspend"
    action_present = _("Suspend")
    action_past = _("Suspended")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")

    def allowed(self, request, instance=None):
        if not instance:
            return True
        self.suspended = instance.status == "SUSPENDED"
        if self.suspended:
            self.action_present = _("Resume")
            self.action_past = _("Resumed")
        return instance.status in ACTIVE_STATES

    def action(self, request, obj_id):
        if getattr(self, 'suspended', False):
            api.server_suspend(request, obj_id)
        else:
            api.server_resume(request, obj_id)


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:nova:images_and_snapshots:index"
    attrs = {"class": "btn small"}


class EditInstance(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Instance")
    url = "horizon:nova:instances_and_volumes:instances:update"
    attrs = {"class": "ajax-modal"}


class SnapshotLink(tables.LinkAction):
    name = "snapshot"
    verbose_name = _("Snapshot")
    url = "horizon:nova:images_and_snapshots:snapshots:create"
    attrs = {"class": "ajax-modal"}

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES


class ConsoleLink(tables.LinkAction):
    name = "console"
    verbose_name = _("VNC Console")
    url = "horizon:nova:instances_and_volumes:instances:vnc"

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES


class LogLink(tables.LinkAction):
    name = "log"
    verbose_name = _("View Log")
    url = "horizon:nova:instances_and_volumes:instances:console"

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES


def get_ips(instance):
    template_name = 'nova/instances_and_volumes/instances/_instance_ips.html'
    context = {"instance": instance}
    return template.loader.render_to_string(template_name, context)


def get_size(instance):
    if hasattr(instance, "full_flavor"):
        size_string = _("%(RAM)s RAM | %(VCPU)s VCPU | %(disk)s Disk")
        vals = {'RAM': sizeformat.mbformat(instance.full_flavor.ram),
                'VCPU': instance.full_flavor.vcpus,
                'disk': sizeformat.diskgbformat(instance.full_flavor.disk)}
        return size_string % vals
    return _("Not available")


def get_power_state(instance):
    return POWER_STATES.get(getattr(instance, "OS-EXT-STS:power_state", 0), '')


class InstancesTable(tables.DataTable):
    name = tables.Column("name", link="horizon:nova:instances_and_volumes:" \
                                      "instances:detail")
    ip = tables.Column(get_ips, verbose_name=_("IP Address"))
    size = tables.Column(get_size, verbose_name=_("Size"))
    status = tables.Column("status", filters=(title,))
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         filters=(title,))
    state = tables.Column(get_power_state,
                          filters=(title,),
                          verbose_name=_("Power State"))

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        table_actions = (LaunchLink, TerminateInstance)
        row_actions = (EditInstance, ConsoleLink, LogLink, SnapshotLink,
                       TogglePause, ToggleSuspend, RebootInstance,
                       TerminateInstance)
