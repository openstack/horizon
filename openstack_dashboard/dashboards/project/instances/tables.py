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

from django.conf import settings
from django.core import urlresolvers
from django import shortcuts
from django import template
from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import conf
from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security.floating_ips \
    import workflows
from openstack_dashboard.dashboards.project.instances import tabs


LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)
VOLUME_ATTACH_READY_STATES = ("ACTIVE", "SHUTOFF")
SNAPSHOT_READY_STATES = ("ACTIVE", "SHUTOFF", "PAUSED", "SUSPENDED")

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
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("compute", "compute:delete"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance=None):
        """Allow terminate action if instance not currently being deleted."""
        return not is_deleting(instance)

    def action(self, request, obj_id):
        api.nova.server_delete(request, obj_id)


class RebootInstance(tables.BatchAction):
    name = "reboot"
    action_present = _("Hard Reboot")
    action_past = _("Hard Rebooted")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('btn-danger', 'btn-reboot')
    policy_rules = (("compute", "compute:reboot"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance=None):
        if instance is not None:
            return ((instance.status in ACTIVE_STATES
                     or instance.status == 'SHUTOFF')
                    and not is_deleting(instance))
        else:
            return True

    def action(self, request, obj_id):
        api.nova.server_reboot(request, obj_id, soft_reboot=False)


class SoftRebootInstance(RebootInstance):
    name = "soft_reboot"
    action_present = _("Soft Reboot")
    action_past = _("Soft Rebooted")

    def action(self, request, obj_id):
        api.nova.server_reboot(request, obj_id, soft_reboot=True)


class TogglePause(tables.BatchAction):
    name = "pause"
    action_present = (_("Pause"), _("Resume"))
    action_past = (_("Paused"), _("Resumed"))
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ("btn-pause",)

    def allowed(self, request, instance=None):
        if not api.nova.extension_supported('AdminActions',
                                            request):
            return False
        self.paused = False
        if not instance:
            return self.paused
        self.paused = instance.status == "PAUSED"
        if self.paused:
            self.current_present_action = UNPAUSE
            policy = (("compute", "compute_extension:admin_actions:unpause"),)
        else:
            self.current_present_action = PAUSE
            policy = (("compute", "compute_extension:admin_actions:pause"),)

        has_permission = True
        policy_check = getattr(settings, "POLICY_CHECK_FUNCTION", None)
        if policy_check:
            has_permission = policy_check(policy, request,
                target={'project_id': getattr(instance, 'tenant_id', None)})

        return (has_permission
                and (instance.status in ACTIVE_STATES or self.paused)
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
        if not api.nova.extension_supported('AdminActions',
                                            request):
            return False
        self.suspended = False
        if not instance:
            self.suspended
        self.suspended = instance.status == "SUSPENDED"
        if self.suspended:
            self.current_present_action = RESUME
            policy = (("compute", "compute_extension:admin_actions:resume"),)
        else:
            self.current_present_action = SUSPEND
            policy = (("compute", "compute_extension:admin_actions:suspend"),)

        has_permission = True
        policy_check = getattr(settings, "POLICY_CHECK_FUNCTION", None)
        if policy_check:
            has_permission = policy_check(policy, request,
                target={'project_id': getattr(instance, 'tenant_id', None)})

        return (has_permission
                and (instance.status in ACTIVE_STATES or self.suspended)
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
    policy_rules = (("compute", "compute:create"),)

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
        except Exception:
            LOG.exception("Failed to retrieve quota information")
            # If we can't get the quota information, leave it to the
            # API to check when launching

        return True  # The action should always be displayed


class EditInstance(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Instance")
    url = "horizon:project:instances:update"
    classes = ("ajax-modal", "btn-edit")
    policy_rules = (("compute", "compute:update"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

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
    url = "horizon:project:images:snapshots:create"
    classes = ("ajax-modal", "btn-camera")
    policy_rules = (("compute", "compute:snapshot"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance=None):
        return instance.status in SNAPSHOT_READY_STATES \
            and not is_deleting(instance)


class ConsoleLink(tables.LinkAction):
    name = "console"
    verbose_name = _("Console")
    url = "horizon:project:instances:detail"
    classes = ("btn-console",)
    policy_rules = (("compute", "compute_extension:consoles"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES and not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = super(ConsoleLink, self).get_link_url(datum)
        tab_query_string = tabs.ConsoleTab(
            tabs.InstanceDetailTabs).get_query_string()
        return "?".join([base_url, tab_query_string])


class LogLink(tables.LinkAction):
    name = "log"
    verbose_name = _("View Log")
    url = "horizon:project:instances:detail"
    classes = ("btn-log",)
    policy_rules = (("compute", "compute_extension:console_output"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES and not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = super(LogLink, self).get_link_url(datum)
        tab_query_string = tabs.LogTab(
            tabs.InstanceDetailTabs).get_query_string()
        return "?".join([base_url, tab_query_string])


class ResizeLink(tables.LinkAction):
    name = "resize"
    verbose_name = _("Resize Instance")
    url = "horizon:project:instances:resize"
    classes = ("ajax-modal", "btn-resize")
    policy_rules = (("compute", "compute:resize"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def get_link_url(self, project):
        return self._get_link_url(project, 'flavor_choice')

    def _get_link_url(self, project, step_slug):
        base_url = urlresolvers.reverse(self.url, args=[project.id])
        param = urlencode({"step": step_slug})
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        return ((instance.status in ACTIVE_STATES
                 or instance.status == 'SHUTOFF')
                and not is_deleting(instance))


class ConfirmResize(tables.Action):
    name = "confirm"
    verbose_name = _("Confirm Resize/Migrate")
    classes = ("btn-confirm", "btn-action-required")
    policy_rules = (("compute", "compute:confirm_resize"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        return instance.status == 'VERIFY_RESIZE'

    def single(self, table, request, instance):
        api.nova.server_confirm_resize(request, instance)


class RevertResize(tables.Action):
    name = "revert"
    verbose_name = _("Revert Resize/Migrate")
    classes = ("btn-revert", "btn-action-required")
    policy_rules = (("compute", "compute:revert_resize"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        return instance.status == 'VERIFY_RESIZE'

    def single(self, table, request, instance):
        api.nova.server_revert_resize(request, instance)


class RebuildInstance(tables.LinkAction):
    name = "rebuild"
    verbose_name = _("Rebuild Instance")
    classes = ("btn-rebuild", "ajax-modal")
    url = "horizon:project:instances:rebuild"
    policy_rules = (("compute", "compute:rebuild"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        return ((instance.status in ACTIVE_STATES
                 or instance.status == 'SHUTOFF')
                and not is_deleting(instance))

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        return urlresolvers.reverse(self.url, args=[instance_id])


class DecryptInstancePassword(tables.LinkAction):
    name = "decryptpassword"
    verbose_name = _("Retrieve Password")
    classes = ("btn-decrypt", "ajax-modal")
    url = "horizon:project:instances:decryptpassword"

    def allowed(self, request, instance):
        enable = getattr(settings,
                         'OPENSTACK_ENABLE_PASSWORD_RETRIEVE',
                         False)
        return (enable
                and (instance.status in ACTIVE_STATES
                     or instance.status == 'SHUTOFF')
                and not is_deleting(instance)
                and get_keyname(instance) is not None)

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        keypair_name = get_keyname(datum)
        return urlresolvers.reverse(self.url, args=[instance_id,
                                                    keypair_name])


class AssociateIP(tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate Floating IP")
    url = "horizon:project:access_and_security:floating_ips:associate"
    classes = ("ajax-modal", "btn-associate")
    policy_rules = (("compute", "network:associate_floating_ip"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        if api.network.floating_ip_simple_associate_supported(request):
            return False
        return not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)
        next = urlresolvers.reverse("horizon:project:instances:index")
        params = {"instance_id": self.table.get_object_id(datum),
                  workflows.IPAssociationWorkflow.redirect_param_name: next}
        params = urlencode(params)
        return "?".join([base_url, params])


class SimpleAssociateIP(tables.Action):
    name = "associate-simple"
    verbose_name = _("Associate Floating IP")
    classes = ("btn-associate-simple",)
    policy_rules = (("compute", "network:associate_floating_ip"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        if not api.network.floating_ip_simple_associate_supported(request):
            return False
        return not is_deleting(instance)

    def single(self, table, request, instance_id):
        try:
            # target_id is port_id for Neutron and instance_id for Nova Network
            # (Neutron API wrapper returns a 'portid_fixedip' string)
            target_id = api.network.floating_ip_target_get_by_instance(
                request, instance_id).split('_')[0]

            fip = api.network.tenant_floating_ip_allocate(request)
            api.network.floating_ip_associate(request, fip.id, target_id)
            messages.success(request,
                             _("Successfully associated floating IP: %s")
                             % fip.ip)
        except Exception:
            exceptions.handle(request,
                              _("Unable to associate floating IP."))
        return shortcuts.redirect("horizon:project:instances:index")


class SimpleDisassociateIP(tables.Action):
    name = "disassociate"
    verbose_name = _("Disassociate Floating IP")
    classes = ("btn-danger", "btn-disassociate",)
    policy_rules = (("compute", "network:disassociate_floating_ip"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        if not conf.HORIZON_CONFIG["simple_ip_management"]:
            return False
        return not is_deleting(instance)

    def single(self, table, request, instance_id):
        try:
            # target_id is port_id for Neutron and instance_id for Nova Network
            # (Neutron API wrapper returns a 'portid_fixedip' string)
            targets = api.network.floating_ip_target_list_by_instance(
                request, instance_id)

            target_ids = [t.split('_')[0] for t in targets]

            fips = [fip for fip in api.network.tenant_floating_ip_list(request)
                    if fip.port_id in target_ids]
            # Removing multiple floating IPs at once doesn't work, so this pops
            # off the first one.
            if fips:
                fip = fips.pop()
                api.network.floating_ip_disassociate(request,
                                                     fip.id, fip.port_id)
                messages.success(request,
                                 _("Successfully disassociated "
                                   "floating IP: %s") % fip.ip)
            else:
                messages.info(request, _("No floating IPs to disassociate."))
        except Exception:
            exceptions.handle(request,
                              _("Unable to disassociate floating IP."))
        return shortcuts.redirect("horizon:project:instances:index")


def instance_fault_to_friendly_message(instance):
    fault = getattr(instance, 'fault', {})
    message = fault.get('message', _("Unknown"))
    default_message = _("Please try again later [Error: %s].") % message
    fault_map = {
        'NoValidHost': _("There is not enough capacity for this "
                         "flavor in the selected availability zone. "
                         "Try again later or select a different availability "
                         "zone.")
    }
    return fault_map.get(message, default_message)


def get_instance_error(instance):
    if instance.status.lower() != 'error':
        return None
    message = instance_fault_to_friendly_message(instance)
    preamble = _('Failed to launch instance "%s"'
                 ) % instance.name or instance.id
    message = string_concat(preamble, ': ', message)
    return message


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        instance = api.nova.server_get(request, instance_id)
        instance.full_flavor = api.nova.flavor_get(request,
                                                   instance.flavor["id"])
        error = get_instance_error(instance)
        if error:
            messages.error(request, error)
        return instance


class StartInstance(tables.BatchAction):
    name = "start"
    action_present = _("Start")
    action_past = _("Started")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    policy_rules = (("compute", "compute:start"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        return instance.status in ("SHUTDOWN", "SHUTOFF", "CRASHED")

    def action(self, request, obj_id):
        api.nova.server_start(request, obj_id)


class StopInstance(tables.BatchAction):
    name = "stop"
    action_present = _("Shut Off")
    action_past = _("Shut Off")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('btn-danger',)
    policy_rules = (("compute", "compute:stop"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, 'tenant_id', None)
        return {"project_id": project_id}

    def allowed(self, request, instance):
        return ((get_power_state(instance)
                in ("RUNNING", "PAUSED", "SUSPENDED"))
                and not is_deleting(instance))

    def action(self, request, obj_id):
        api.nova.server_stop(request, obj_id)


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
    ("deleted", _("Deleted")),
    ("active", _("Active")),
    ("shutoff", _("Shutoff")),
    ("suspended", _("Suspended")),
    ("paused", _("Paused")),
    ("error", _("Error")),
    ("resize", _("Resize/Migrate")),
    ("verify_resize", _("Confirm or Revert Resize/Migrate")),
    ("revert_resize", _("Revert Resize/Migrate")),
    ("reboot", _("Reboot")),
    ("hard_reboot", _("Hard Reboot")),
    ("password", _("Password")),
    ("rebuild", _("Rebuild")),
    ("migrating", _("Migrating")),
    ("build", _("Build")),
    ("rescue", _("Rescue")),
    ("deleted", _("Deleted")),
    ("soft_deleted", _("Soft Deleted")),
    ("shelved", _("Shelved")),
    ("shelved_offloaded", _("Shelved Offloaded")),
)


TASK_DISPLAY_CHOICES = (
    ("scheduling", _("Scheduling")),
    ("block_device_mapping", _("Block Device Mapping")),
    ("networking", _("Networking")),
    ("spawning", _("Spawning")),
    ("image_snapshot", _("Snapshotting")),
    ("image_snapshot_pending", _("Image Snapshot Pending")),
    ("image_pending_upload", _("Image Pending Upload")),
    ("image_uploading", _("Image Uploading")),
    ("image_backup", _("Image Backup")),
    ("updating_password", _("Updating Password")),
    ("resize_prep", _("Preparing Resize or Migrate")),
    ("resize_migrating", _("Resizing or Migrating")),
    ("resize_migrated", _("Resized or Migrated")),
    ("resize_finish", _("Finishing Resize or Migrate")),
    ("resize_reverting", _("Reverting Resize or Migrate")),
    ("resize_confirming", _("Confirming Resize or Migrate")),
    ("rebooting", _("Rebooting")),
    ("rebooting_hard", _("Rebooting Hard")),
    ("pausing", _("Pausing")),
    ("unpausing", _("Resuming")),
    ("suspending", _("Suspending")),
    ("resuming", _("Resuming")),
    ("powering-off", _("Powering Off")),
    ("powering-on", _("Powering On")),
    ("rescuing", _("Rescuing")),
    ("unrescuing", _("Unrescuing")),
    ("rebuilding", _("Rebuilding")),
    ("rebuild_block_device_mapping", _("Rebuild Block Device Mapping")),
    ("rebuild_spawning", _("Rebuild Spawning")),
    ("migrating", _("Migrating")),
    ("deleting", _("Deleting")),
    ("soft-deleting", _("Soft Deleting")),
    ("restoring", _("Restoring")),
    ("shelving", _("Shelving")),
    ("shelving_image_pending_upload", _("Shelving Image Pending Upload")),
    ("shelving_image_uploading", _("Shelving Image Uploading")),
    ("shelving_offloading", _("Shelving Offloading")),
    ("unshelving", _("Unshelving")),
)

POWER_DISPLAY_CHOICES = (
    ("NO STATE", _("No State")),
    ("RUNNING", _("Running")),
    ("BLOCKED", _("Blocked")),
    ("PAUSED", _("Paused")),
    ("SHUTDOWN", _("Shut Down")),
    ("SHUTOFF", _("Shut Off")),
    ("CRASHED", _("Crashed")),
    ("SUSPENDED", _("Suspended")),
    ("FAILED", _("Failed")),
    ("BUILDING", _("Building")),
)


class InstancesFilterAction(tables.FilterAction):

    def filter(self, table, instances, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [instance for instance in instances
                if q in instance.name.lower()]


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
    image_name = tables.Column("image_name",
                               verbose_name=_("Image Name"))
    ip = tables.Column(get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    keypair = tables.Column(get_keyname, verbose_name=_("Key Pair"))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    az = tables.Column("availability_zone",
                       verbose_name=_("Availability Zone"))
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         filters=(title, filters.replace_underscores),
                         status=True,
                         status_choices=TASK_STATUS_CHOICES,
                         display_choices=TASK_DISPLAY_CHOICES)
    state = tables.Column(get_power_state,
                          filters=(title, filters.replace_underscores),
                          verbose_name=_("Power State"),
                          display_choices=POWER_DISPLAY_CHOICES)
    created = tables.Column("created",
                            verbose_name=_("Uptime"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["status", "task"]
        row_class = UpdateRow
        table_actions = (LaunchLink, SoftRebootInstance, TerminateInstance,
                         InstancesFilterAction)
        row_actions = (StartInstance, ConfirmResize, RevertResize,
                       CreateSnapshot, SimpleAssociateIP, AssociateIP,
                       SimpleDisassociateIP, EditInstance,
                       DecryptInstancePassword, EditInstanceSecurityGroups,
                       ConsoleLink, LogLink, TogglePause, ToggleSuspend,
                       ResizeLink, SoftRebootInstance, RebootInstance,
                       StopInstance, RebuildInstance, TerminateInstance)
