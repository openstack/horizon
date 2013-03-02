# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django import shortcuts
from django import template
from django.core import urlresolvers
from django.template.defaultfilters import title
from django.utils.http import urlencode
from django.utils.translation import string_concat, ugettext_lazy as _

from horizon.conf import HORIZON_CONFIG
from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils.filters import replace_underscores

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security \
        .floating_ips.workflows import IPAssociationWorkflow
from .tabs import InstanceDetailTabs, LogTab, ConsoleTab


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

PAUSE = 0
UNPAUSE = 1
SUSPEND = 0
RESUME = 1


def is_deleting(instance):
    task_state = getattr(instance, "OS-EXT-STS:task_state", None)
    if not task_state:
        return False
    return task_state.lower() == "deleting"


class TerminateInstance(tables.BatchAction):
    name = "terminate"
    action_present = _("Terminate")
    action_past = _("Scheduled termination of")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('btn-danger', 'btn-terminate')

    def allowed(self, request, instance=None):
        return True

    def action(self, request, obj_id):
        api.nova.server_delete(request, obj_id)


class RebootInstance(tables.BatchAction):
    name = "reboot"
    action_present = _("Hard Reboot")
    action_past = _("Hard Rebooted")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('btn-danger', 'btn-reboot')

    def allowed(self, request, instance=None):
        return ((instance.status in ACTIVE_STATES
                 or instance.status == 'SHUTOFF')
                and not is_deleting(instance))

    def action(self, request, obj_id):
        api.nova.server_reboot(request, obj_id, api.nova.REBOOT_HARD)


class SoftRebootInstance(RebootInstance):
    name = "soft_reboot"
    action_present = _("Soft Reboot")
    action_past = _("Soft Rebooted")

    def action(self, request, obj_id):
        api.nova.server_reboot(request, obj_id, api.nova.REBOOT_SOFT)


class TogglePause(tables.BatchAction):
    name = "pause"
    action_present = (_("Pause"), _("Resume"))
    action_past = (_("Paused"), _("Resumed"))
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ("btn-pause",)

    def allowed(self, request, instance=None):
        self.paused = False
        if not instance:
            return self.paused
        self.paused = instance.status == "PAUSED"
        if self.paused:
            self.current_present_action = UNPAUSE
        else:
            self.current_present_action = PAUSE
        return ((instance.status in ACTIVE_STATES or self.paused)
                and not is_deleting(instance))

    def action(self, request, obj_id):
        if self.paused:
            api.nova.server_unpause(request, obj_id)
            self.current_past_action = UNPAUSE
        else:
            api.nova.server_pause(request, obj_id)
            self.current_past_action = PAUSE


class ToggleSuspend(tables.BatchAction):
    name = "suspend"
    action_present = (_("Suspend"), _("Resume"))
    action_past = (_("Suspended"), _("Resumed"))
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ("btn-suspend",)

    def allowed(self, request, instance=None):
        self.suspended = False
        if not instance:
            self.suspended
        self.suspended = instance.status == "SUSPENDED"
        if self.suspended:
            self.current_present_action = RESUME
        else:
            self.current_present_action = SUSPEND
        return ((instance.status in ACTIVE_STATES or self.suspended)
                and not is_deleting(instance))

    def action(self, request, obj_id):
        if self.suspended:
            api.nova.server_resume(request, obj_id)
            self.current_past_action = RESUME
        else:
            api.nova.server_suspend(request, obj_id)
            self.current_past_action = SUSPEND


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:project:instances:launch"
    classes = ("btn-launch", "ajax-modal")

    def allowed(self, request, datum):
        try:
            limits = api.nova.tenant_absolute_limits(request, reserved=True)

            instances_available = limits['maxTotalInstances'] \
                - limits['totalInstancesUsed']
            cores_available = limits['maxTotalCores'] \
                - limits['totalCoresUsed']
            ram_available = limits['maxTotalRAMSize'] - limits['totalRAMUsed']

            if instances_available <= 0 or cores_available <= 0 \
                    or ram_available <= 0:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
                    self.verbose_name = string_concat(self.verbose_name, ' ',
                                                      _("(Quota exceeded)"))
            else:
                self.verbose_name = _("Launch Instance")
                classes = [c for c in self.classes if c != "disabled"]
                self.classes = classes
        except:
            LOG.exception("Failed to retrieve quota information")
            # If we can't get the quota information, leave it to the
            # API to check when launching

        return True  # The action should always be displayed


class EditInstance(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Instance")
    url = "horizon:project:instances:update"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, project):
        return self._get_link_url(project, 'instance_info')

    def _get_link_url(self, project, step_slug):
        base_url = urlresolvers.reverse(self.url, args=[project.id])
        param = urlencode({"step": step_slug})
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        return not is_deleting(instance)


class EditInstanceSecurityGroups(EditInstance):
    name = "edit_secgroups"
    verbose_name = _("Edit Security Groups")

    def get_link_url(self, project):
        return self._get_link_url(project, 'update_security_groups')

    def allowed(self, request, instance=None):
        return (instance.status in ACTIVE_STATES and
                not is_deleting(instance) and
                request.user.tenant_id == instance.tenant_id)


class CreateSnapshot(tables.LinkAction):
    name = "snapshot"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:images_and_snapshots:snapshots:create"
    classes = ("ajax-modal", "btn-camera")

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES and not is_deleting(instance)


class ConsoleLink(tables.LinkAction):
    name = "console"
    verbose_name = _("Console")
    url = "horizon:project:instances:detail"
    classes = ("btn-console",)

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES and not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = super(ConsoleLink, self).get_link_url(datum)
        tab_query_string = ConsoleTab(InstanceDetailTabs).get_query_string()
        return "?".join([base_url, tab_query_string])


class LogLink(tables.LinkAction):
    name = "log"
    verbose_name = _("View Log")
    url = "horizon:project:instances:detail"
    classes = ("btn-log",)

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES and not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = super(LogLink, self).get_link_url(datum)
        tab_query_string = LogTab(InstanceDetailTabs).get_query_string()
        return "?".join([base_url, tab_query_string])


class ConfirmResize(tables.Action):
    name = "confirm"
    verbose_name = _("Confirm Resize/Migrate")
    classes = ("btn-confirm", "btn-action-required")

    def allowed(self, request, instance):
        return instance.status == 'VERIFY_RESIZE'

    def single(self, table, request, instance):
        api.nova.server_confirm_resize(request, instance)


class RevertResize(tables.Action):
    name = "revert"
    verbose_name = _("Revert Resize/Migrate")
    classes = ("btn-revert", "btn-action-required")

    def allowed(self, request, instance):
        return instance.status == 'VERIFY_RESIZE'

    def single(self, table, request, instance):
        api.nova.server_revert_resize(request, instance)


class AssociateIP(tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate Floating IP")
    url = "horizon:project:access_and_security:floating_ips:associate"
    classes = ("ajax-modal", "btn-associate")

    def allowed(self, request, instance):
        fip = api.network.NetworkClient(request).floating_ips
        if fip.is_simple_associate_supported():
            return False
        return not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)
        next = urlresolvers.reverse("horizon:project:instances:index")
        params = {"instance_id": self.table.get_object_id(datum),
                  IPAssociationWorkflow.redirect_param_name: next}
        params = urlencode(params)
        return "?".join([base_url, params])


class SimpleAssociateIP(tables.Action):
    name = "associate-simple"
    verbose_name = _("Associate Floating IP")
    classes = ("btn-associate-simple",)

    def allowed(self, request, instance):
        fip = api.network.NetworkClient(request).floating_ips
        if not fip.is_simple_associate_supported():
            return False
        return not is_deleting(instance)

    def single(self, table, request, instance):
        try:
            fip = api.network.tenant_floating_ip_allocate(request)
            api.network.floating_ip_associate(request, fip.id, instance)
            messages.success(request,
                             _("Successfully associated floating IP: %s")
                             % fip.ip)
        except:
            exceptions.handle(request,
                              _("Unable to associate floating IP."))
        return shortcuts.redirect("horizon:project:instances:index")


class SimpleDisassociateIP(tables.Action):
    name = "disassociate"
    verbose_name = _("Disassociate Floating IP")
    classes = ("btn-danger", "btn-disassociate",)

    def allowed(self, request, instance):
        if not HORIZON_CONFIG["simple_ip_management"]:
            return False
        return not is_deleting(instance)

    def single(self, table, request, instance_id):
        try:
            fips = [fip for fip in api.network.tenant_floating_ip_list(request)
                    if fip.port_id == instance_id]
            # Removing multiple floating IPs at once doesn't work, so this pops
            # off the first one.
            if fips:
                fip = fips.pop()
                api.network.floating_ip_disassociate(request,
                                                     fip.id, instance_id)
                api.network.tenant_floating_ip_release(request, fip.id)
                messages.success(request,
                                 _("Successfully disassociated "
                                   "floating IP: %s") % fip.ip)
            else:
                messages.info(request, _("No floating IPs to disassociate."))
        except:
            exceptions.handle(request,
                              _("Unable to disassociate floating IP."))
        return shortcuts.redirect("horizon:project:instances:index")


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        instance = api.nova.server_get(request, instance_id)
        instance.full_flavor = api.nova.flavor_get(request,
                                                   instance.flavor["id"])
        return instance


def get_ips(instance):
    template_name = 'project/instances/_instance_ips.html'
    context = {"instance": instance}
    return template.loader.render_to_string(template_name, context)


def get_size(instance):
    if hasattr(instance, "full_flavor"):
        size_string = _("%(name)s | %(RAM)s RAM | %(VCPU)s VCPU "
                        "| %(disk)s Disk")
        vals = {'name': instance.full_flavor.name,
                'RAM': sizeformat.mbformat(instance.full_flavor.ram),
                'VCPU': instance.full_flavor.vcpus,
                'disk': sizeformat.diskgbformat(instance.full_flavor.disk)}
        return size_string % vals
    return _("Not available")


def get_keyname(instance):
    if hasattr(instance, "key_name"):
        keyname = instance.key_name
        return keyname
    return _("Not available")


def get_power_state(instance):
    return POWER_STATES.get(getattr(instance, "OS-EXT-STS:power_state", 0), '')


STATUS_DISPLAY_CHOICES = (
    ("resize", "Resize/Migrate"),
    ("verify_resize", "Confirm or Revert Resize/Migrate"),
    ("revert_resize", "Revert Resize/Migrate"),
)


TASK_DISPLAY_CHOICES = (
    ("image_snapshot", "Snapshotting"),
    ("resize_prep", "Preparing Resize or Migrate"),
    ("resize_migrating", "Resizing or Migrating"),
    ("resize_migrated", "Resized or Migrated"),
    ("resize_finish", "Finishing Resize or Migrate"),
    ("resize_confirming", "Confirming Resize or Nigrate"),
    ("resize_reverting", "Reverting Resize or Migrate"),
    ("unpausing", "Resuming"),
)


class InstancesTable(tables.DataTable):
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
    name = tables.Column("name",
                         link=("horizon:project:instances:detail"),
                         verbose_name=_("Instance Name"))
    ip = tables.Column(get_ips, verbose_name=_("IP Address"))
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    keypair = tables.Column(get_keyname, verbose_name=_("Keypair"))
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
        row_class = UpdateRow
        table_actions = (LaunchLink, TerminateInstance)
        row_actions = (ConfirmResize, RevertResize, CreateSnapshot,
                       SimpleAssociateIP, AssociateIP,
                       SimpleDisassociateIP, EditInstance,
                       EditInstanceSecurityGroups, ConsoleLink, LogLink,
                       TogglePause, ToggleSuspend, SoftRebootInstance,
                       RebootInstance, TerminateInstance)
