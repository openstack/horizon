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
from django.http import HttpResponse
from django import template
from django.template.defaultfilters import title
from django import urls
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import npgettext_lazy
from django.utils.translation import pgettext_lazy
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.floating_ips import workflows
from openstack_dashboard.dashboards.project.instances import tabs
from openstack_dashboard.dashboards.project.instances.workflows \
    import resize_instance
from openstack_dashboard.dashboards.project.instances.workflows \
    import update_instance
from openstack_dashboard import policy
from openstack_dashboard.views import get_url_with_pagination

LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)
VOLUME_ATTACH_READY_STATES = ("ACTIVE", "SHUTOFF")
SNAPSHOT_READY_STATES = ("ACTIVE", "SHUTOFF", "PAUSED", "SUSPENDED")
SHELVE_READY_STATES = ("ACTIVE", "SHUTOFF", "PAUSED", "SUSPENDED")

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
SHELVE = 0
UNSHELVE = 1


def is_deleting(instance):
    task_state = getattr(instance, "OS-EXT-STS:task_state", None)
    if not task_state:
        return False
    return task_state.lower() == "deleting"


class DeleteInstance(policy.PolicyTargetMixin, tables.DeleteAction):
    policy_rules = (("compute", "os_compute_api:servers:delete"),)
    help_text = _("Deleted instances are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Instance",
            u"Delete Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Instance",
            u"Scheduled deletion of Instances",
            count
        )

    def allowed(self, request, instance=None):
        error_state = False
        if instance:
            error_state = (instance.status == 'ERROR')
        return error_state or not is_deleting(instance)

    def action(self, request, obj_id):
        api.nova.server_delete(request, obj_id)


class RebootInstance(policy.PolicyTargetMixin, tables.BatchAction):
    name = "reboot"
    classes = ('btn-reboot',)
    policy_rules = (("compute", "os_compute_api:servers:reboot"),)
    help_text = _("Restarted instances will lose any data"
                  " not saved in persistent storage.")
    action_type = "danger"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Hard Reboot Instance",
            u"Hard Reboot Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Hard Rebooted Instance",
            u"Hard Rebooted Instances",
            count
        )

    def allowed(self, request, instance=None):
        if instance is not None:
            return ((instance.status in ACTIVE_STATES or
                     instance.status == 'SHUTOFF') and
                    not is_deleting(instance))
        else:
            return True

    def action(self, request, obj_id):
        api.nova.server_reboot(request, obj_id, soft_reboot=False)


class SoftRebootInstance(RebootInstance):
    name = "soft_reboot"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Soft Reboot Instance",
            u"Soft Reboot Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Soft Rebooted Instance",
            u"Soft Rebooted Instances",
            count
        )

    def action(self, request, obj_id):
        api.nova.server_reboot(request, obj_id, soft_reboot=True)

    def allowed(self, request, instance=None):
        if instance is not None:
            return instance.status in ACTIVE_STATES
        else:
            return True


class TogglePause(tables.BatchAction):
    name = "pause"
    icon = "pause"

    @staticmethod
    def action_present(count):
        return (
            ungettext_lazy(
                u"Pause Instance",
                u"Pause Instances",
                count
            ),
            ungettext_lazy(
                u"Resume Instance",
                u"Resume Instances",
                count
            ),
        )

    @staticmethod
    def action_past(count):
        return (
            ungettext_lazy(
                u"Paused Instance",
                u"Paused Instances",
                count
            ),
            ungettext_lazy(
                u"Resumed Instance",
                u"Resumed Instances",
                count
            ),
        )

    def allowed(self, request, instance=None):
        if not api.nova.extension_supported('AdminActions',
                                            request):
            return False
        if not instance:
            return False
        self.paused = instance.status == "PAUSED"
        if self.paused:
            self.current_present_action = UNPAUSE
            policy_rules = (
                ("compute", "os_compute_api:os-pause-server:unpause"),)
        else:
            self.current_present_action = PAUSE
            policy_rules = (
                ("compute", "os_compute_api:os-pause-server:pause"),)

        has_permission = policy.check(
            policy_rules, request,
            target={'project_id': getattr(instance, 'tenant_id', None)})

        return (has_permission and
                (instance.status in ACTIVE_STATES or self.paused) and
                not is_deleting(instance))

    def action(self, request, obj_id):
        if self.paused:
            api.nova.server_unpause(request, obj_id)
            self.current_past_action = UNPAUSE
        else:
            api.nova.server_pause(request, obj_id)
            self.current_past_action = PAUSE


class ToggleSuspend(tables.BatchAction):
    name = "suspend"
    classes = ("btn-suspend",)

    @staticmethod
    def action_present(count):
        return (
            ungettext_lazy(
                u"Suspend Instance",
                u"Suspend Instances",
                count
            ),
            ungettext_lazy(
                u"Resume Instance",
                u"Resume Instances",
                count
            ),
        )

    @staticmethod
    def action_past(count):
        return (
            ungettext_lazy(
                u"Suspended Instance",
                u"Suspended Instances",
                count
            ),
            ungettext_lazy(
                u"Resumed Instance",
                u"Resumed Instances",
                count
            ),
        )

    def allowed(self, request, instance=None):
        if not api.nova.extension_supported('AdminActions',
                                            request):
            return False
        if not instance:
            return False
        self.suspended = instance.status == "SUSPENDED"
        if self.suspended:
            self.current_present_action = RESUME
            policy_rules = (
                ("compute", "os_compute_api:os-rescue"),)
        else:
            self.current_present_action = SUSPEND
            policy_rules = (
                ("compute", "os_compute_api:os-suspend-server:suspend"),)

        has_permission = policy.check(
            policy_rules, request,
            target={'project_id': getattr(instance, 'tenant_id', None)})

        return (has_permission and
                (instance.status in ACTIVE_STATES or self.suspended) and
                not is_deleting(instance))

    def action(self, request, obj_id):
        if self.suspended:
            api.nova.server_resume(request, obj_id)
            self.current_past_action = RESUME
        else:
            api.nova.server_suspend(request, obj_id)
            self.current_past_action = SUSPEND


class ToggleShelve(tables.BatchAction):
    name = "shelve"
    icon = "shelve"

    @staticmethod
    def action_present(count):
        return (
            ungettext_lazy(
                u"Shelve Instance",
                u"Shelve Instances",
                count
            ),
            ungettext_lazy(
                u"Unshelve Instance",
                u"Unshelve Instances",
                count
            ),
        )

    @staticmethod
    def action_past(count):
        return (
            ungettext_lazy(
                u"Shelved Instance",
                u"Shelved Instances",
                count
            ),
            ungettext_lazy(
                u"Unshelved Instance",
                u"Unshelved Instances",
                count
            ),
        )

    def allowed(self, request, instance=None):
        if not api.nova.extension_supported('Shelve', request):
            return False
        if not instance:
            return False
        if not request.user.is_superuser and getattr(
                instance, 'locked', False):
            return False

        self.shelved = instance.status == "SHELVED_OFFLOADED"
        if self.shelved:
            self.current_present_action = UNSHELVE
            policy_rules = (("compute", "os_compute_api:os-shelve:unshelve"),)
        else:
            self.current_present_action = SHELVE
            policy_rules = (("compute", "os_compute_api:os-shelve:shelve"),)

        has_permission = policy.check(
            policy_rules, request,
            target={'project_id': getattr(instance, 'tenant_id', None)})

        return (has_permission and
                (instance.status in SHELVE_READY_STATES or self.shelved) and
                not is_deleting(instance))

    def action(self, request, obj_id):
        if self.shelved:
            api.nova.server_unshelve(request, obj_id)
            self.current_past_action = UNSHELVE
        else:
            api.nova.server_shelve(request, obj_id)
            self.current_past_action = SHELVE


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:project:instances:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    policy_rules = (("compute", "os_compute_api:servers:create"),)
    ajax = True

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(LaunchLink, self).__init__(attrs, **kwargs)

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

    def single(self, table, request, object_id=None):
        self.allowed(request, None)
        return HttpResponse(self.render(is_table_action=True))


class LaunchLinkNG(LaunchLink):
    name = "launch-ng"
    url = "horizon:project:instances:index"
    ajax = False
    classes = ("btn-launch", )

    def get_default_attrs(self):
        url = urls.reverse(self.url)
        ngclick = "modal.openLaunchInstanceWizard(" \
            "{ successUrl: '%s' })" % url
        self.attrs.update({
            'ng-controller': 'LaunchInstanceModalController as modal',
            'ng-click': ngclick
        })
        return super(LaunchLinkNG, self).get_default_attrs()

    def get_link_url(self, datum=None):
        return "javascript:void(0);"


class EditInstance(policy.PolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Instance")
    url = "horizon:project:instances:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("compute", "os_compute_api:servers:update"),)

    def get_link_url(self, project):
        return self._get_link_url(project, 'instance_info')

    def _get_link_url(self, project, step_slug):
        base_url = urls.reverse(self.url, args=[project.id])
        next_url = self.table.get_full_url()
        params = {"step": step_slug,
                  update_instance.UpdateInstance.redirect_param_name: next_url}
        param = urlencode(params)
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        return not is_deleting(instance)


class EditInstanceSecurityGroups(EditInstance):
    name = "edit_secgroups"
    verbose_name = _("Edit Security Groups")

    def get_link_url(self, project):
        return self._get_link_url(project, 'update_security_groups')

    def allowed(self, request, instance=None):
        if not api.base.is_service_enabled(request, 'network'):
            return False
        return (instance.status in ACTIVE_STATES and
                not is_deleting(instance) and
                request.user.tenant_id == instance.tenant_id)


class EditPortSecurityGroups(tables.LinkAction):
    name = "edit_port_secgroups"
    verbose_name = _("Edit Port Security Groups")
    url = "horizon:project:instances:detail"
    icon = "pencil"

    def get_link_url(self, instance):
        base_url = urls.reverse(self.url, args=[instance.id])
        return '%s?tab=%s__%s' % (base_url, 'instance_details', 'interfaces')


class CreateSnapshot(policy.PolicyTargetMixin, tables.LinkAction):
    name = "snapshot"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:images:snapshots:create"
    classes = ("ajax-modal",)
    icon = "camera"
    policy_rules = (("compute", "os_compute_api:snapshot"),)

    def allowed(self, request, instance=None):
        return instance.status in SNAPSHOT_READY_STATES \
            and not is_deleting(instance)


class ConsoleLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "console"
    verbose_name = _("Console")
    url = "horizon:project:instances:detail"
    classes = ("btn-console",)
    policy_rules = (("compute", "os_compute_api:os-consoles:index"),)

    def allowed(self, request, instance=None):
        # We check if ConsoleLink is allowed only if settings.CONSOLE_TYPE is
        # not set at all, or if it's set to any value other than None or False.
        return bool(getattr(settings, 'CONSOLE_TYPE', True)) and \
            instance.status in ACTIVE_STATES and not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = super(ConsoleLink, self).get_link_url(datum)
        tab_query_string = tabs.ConsoleTab(
            tabs.InstanceDetailTabs).get_query_string()
        return "?".join([base_url, tab_query_string])


class LogLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "log"
    verbose_name = _("View Log")
    url = "horizon:project:instances:detail"
    classes = ("btn-log",)
    policy_rules = (("compute", "os_compute_api:os-console-output"),)

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES and not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = super(LogLink, self).get_link_url(datum)
        tab_query_string = tabs.LogTab(
            tabs.InstanceDetailTabs).get_query_string()
        return "?".join([base_url, tab_query_string])


class ResizeLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "resize"
    verbose_name = _("Resize Instance")
    url = "horizon:project:instances:resize"
    classes = ("ajax-modal", "btn-resize")
    policy_rules = (("compute", "os_compute_api:servers:resize"),)
    action_type = "danger"

    def get_link_url(self, project):
        return self._get_link_url(project, 'flavor_choice')

    def _get_link_url(self, project, step_slug):
        base_url = urls.reverse(self.url, args=[project.id])
        next_url = self.table.get_full_url()
        params = {"step": step_slug,
                  resize_instance.ResizeInstance.redirect_param_name: next_url}
        param = urlencode(params)
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        return ((instance.status in ACTIVE_STATES or
                 instance.status == 'SHUTOFF') and
                not is_deleting(instance))


class ConfirmResize(policy.PolicyTargetMixin, tables.Action):
    name = "confirm"
    verbose_name = _("Confirm Resize/Migrate")
    classes = ("btn-confirm", "btn-action-required")
    policy_rules = (("compute", "os_compute_api:servers:confirm_resize"),)

    def allowed(self, request, instance):
        return instance.status == 'VERIFY_RESIZE'

    def single(self, table, request, instance):
        api.nova.server_confirm_resize(request, instance)


class RevertResize(policy.PolicyTargetMixin, tables.Action):
    name = "revert"
    verbose_name = _("Revert Resize/Migrate")
    classes = ("btn-revert", "btn-action-required")
    policy_rules = (("compute", "os_compute_api:servers:revert_resize"),)

    def allowed(self, request, instance):
        return instance.status == 'VERIFY_RESIZE'

    def single(self, table, request, instance):
        api.nova.server_revert_resize(request, instance)


class RebuildInstance(policy.PolicyTargetMixin, tables.LinkAction):
    name = "rebuild"
    verbose_name = _("Rebuild Instance")
    classes = ("btn-rebuild", "ajax-modal")
    url = "horizon:project:instances:rebuild"
    policy_rules = (("compute", "os_compute_api:servers:rebuild"),)
    action_type = "danger"

    def allowed(self, request, instance):
        return ((instance.status in ACTIVE_STATES or
                 instance.status == 'SHUTOFF') and
                not is_deleting(instance))

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        return urls.reverse(self.url, args=[instance_id])


class DecryptInstancePassword(tables.LinkAction):
    name = "decryptpassword"
    verbose_name = _("Retrieve Password")
    classes = ("btn-decrypt", "ajax-modal")
    url = "horizon:project:instances:decryptpassword"

    def allowed(self, request, instance):
        enable = getattr(settings,
                         'OPENSTACK_ENABLE_PASSWORD_RETRIEVE',
                         False)
        return (enable and
                (instance.status in ACTIVE_STATES or
                 instance.status == 'SHUTOFF') and
                not is_deleting(instance) and
                get_keyname(instance) is not None)

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        keypair_name = get_keyname(datum)
        return urls.reverse(self.url, args=[instance_id,
                                            keypair_name])


class AssociateIP(policy.PolicyTargetMixin, tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate Floating IP")
    url = "horizon:project:floating_ips:associate"
    classes = ("ajax-modal",)
    icon = "link"
    policy_rules = (("network", "update_floatingip"),)

    def allowed(self, request, instance):
        if not api.base.is_service_enabled(request, 'network'):
            return False
        if not api.neutron.floating_ip_supported(request):
            return False
        if api.neutron.floating_ip_simple_associate_supported(request):
            return False
        if instance.status == "ERROR":
            return False
        for addresses in instance.addresses.values():
            for address in addresses:
                if address.get('OS-EXT-IPS:type') == "floating":
                    return False
        return not is_deleting(instance)

    def get_link_url(self, datum):
        base_url = urls.reverse(self.url)
        next_url = self.table.get_full_url()
        params = {
            "instance_id": self.table.get_object_id(datum),
            workflows.IPAssociationWorkflow.redirect_param_name: next_url}
        params = urlencode(params)
        return "?".join([base_url, params])


class DisassociateIP(tables.LinkAction):
    name = "disassociate"
    verbose_name = _("Disassociate Floating IP")
    url = "horizon:project:instances:disassociate"
    classes = ("btn-disassociate", 'ajax-modal')
    policy_rules = (("network", "update_floatingip"),)
    action_type = "danger"

    def allowed(self, request, instance):
        if not api.base.is_service_enabled(request, 'network'):
            return False
        if not api.neutron.floating_ip_supported(request):
            return False
        for addresses in instance.addresses.values():
            for address in addresses:
                if address.get('OS-EXT-IPS:type') == "floating":
                    return not is_deleting(instance)
        return False


class UpdateMetadata(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update_metadata"
    verbose_name = _("Update Metadata")
    ajax = False
    icon = "pencil"
    attrs = {"ng-controller": "MetadataModalHelperController as modal"}
    policy_rules = (("compute", "os_compute_api:server-metadata:update"),)

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(UpdateMetadata, self).__init__(attrs, **kwargs)

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        self.attrs['ng-click'] = (
            "modal.openMetadataModal('instance', '%s', true, 'metadata')"
            % instance_id)
        return "javascript:void(0);"

    def allowed(self, request, instance=None):
        return (instance and
                instance.status.lower() != 'error')


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
    preamble = _('Failed to perform requested operation on instance "%s", the '
                 'instance has an error status') % instance.name or instance.id
    message = string_concat(preamble, ': ', message)
    return message


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        instance = api.nova.server_get(request, instance_id)
        try:
            instance.full_flavor = api.nova.flavor_get(request,
                                                       instance.flavor["id"])
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve flavor information '
                                'for instance "%s".') % instance_id,
                              ignore=True)
        try:
            api.network.servers_update_addresses(request, [instance])
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve Network information '
                                'for instance "%s".') % instance_id,
                              ignore=True)
        error = get_instance_error(instance)
        if error:
            messages.error(request, error)
        return instance


class StartInstance(policy.PolicyTargetMixin, tables.BatchAction):
    name = "start"
    classes = ('btn-confirm',)
    policy_rules = (("compute", "os_compute_api:servers:start"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Start Instance",
            u"Start Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Started Instance",
            u"Started Instances",
            count
        )

    def allowed(self, request, instance):
        return ((instance is None) or
                (instance.status in ("SHUTDOWN", "SHUTOFF", "CRASHED")))

    def action(self, request, obj_id):
        api.nova.server_start(request, obj_id)


class StopInstance(policy.PolicyTargetMixin, tables.BatchAction):
    name = "stop"
    policy_rules = (("compute", "os_compute_api:servers:stop"),)
    help_text = _("The instance(s) will be shut off.")
    action_type = "danger"

    @staticmethod
    def action_present(count):
        return npgettext_lazy(
            "Action to perform (the instance is currently running)",
            u"Shut Off Instance",
            u"Shut Off Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return npgettext_lazy(
            "Past action (the instance is currently already Shut Off)",
            u"Shut Off Instance",
            u"Shut Off Instances",
            count
        )

    def allowed(self, request, instance):
        return (instance is None or
                (get_power_state(instance) in ("RUNNING", "SUSPENDED") and
                 not is_deleting(instance)))

    def action(self, request, obj_id):
        api.nova.server_stop(request, obj_id)


class LockInstance(policy.PolicyTargetMixin, tables.BatchAction):
    name = "lock"
    policy_rules = (("compute", "os_compute_api:os-lock-server:lock"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Lock Instance",
            u"Lock Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Locked Instance",
            u"Locked Instances",
            count
        )

    # to only allow unlocked instances to be locked
    def allowed(self, request, instance):
        if getattr(instance, 'locked', False):
            return False
        if not api.nova.extension_supported('AdminActions', request):
            return False
        if not api.nova.is_feature_available(request, "locked_attribute"):
            return False
        return True

    def action(self, request, obj_id):
        api.nova.server_lock(request, obj_id)


class UnlockInstance(policy.PolicyTargetMixin, tables.BatchAction):
    name = "unlock"
    policy_rules = (("compute", "os_compute_api:os-lock-server:unlock"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Unlock Instance",
            u"Unlock Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Unlocked Instance",
            u"Unlocked Instances",
            count
        )

    # to only allow locked instances to be unlocked
    def allowed(self, request, instance):
        if not getattr(instance, 'locked', True):
            return False
        if not api.nova.extension_supported('AdminActions', request):
            return False
        if not api.nova.is_feature_available(request, "locked_attribute"):
            return False
        return True

    def action(self, request, obj_id):
        api.nova.server_unlock(request, obj_id)


class AttachVolume(tables.LinkAction):
    name = "attach_volume"
    verbose_name = _("Attach Volume")
    url = "horizon:project:instances:attach_volume"
    classes = ("ajax-modal",)
    policy_rules = (
        ("compute", "os_compute_api:os-volumes-attachments:create"),)

    # This action should be disabled if the instance
    # is not active, or the instance is being deleted
    # or cinder is not enabled
    def allowed(self, request, instance=None):
        return (instance.status in ("ACTIVE") and
                not is_deleting(instance) and
                api.cinder.is_volume_service_enabled(request))


class DetachVolume(AttachVolume):
    name = "detach_volume"
    verbose_name = _("Detach Volume")
    url = "horizon:project:instances:detach_volume"
    policy_rules = (
        ("compute", "os_compute_api:os-volumes-attachments:delete"),)

    # This action should be disabled if the instance
    # is not active, or the instance is being deleted
    # or cinder is not enabled
    def allowed(self, request, instance=None):
        return (instance.status in ("ACTIVE") and
                not is_deleting(instance) and
                api.cinder.is_volume_service_enabled(request))


class AttachInterface(policy.PolicyTargetMixin, tables.LinkAction):
    name = "attach_interface"
    verbose_name = _("Attach Interface")
    classes = ("btn-confirm", "ajax-modal")
    url = "horizon:project:instances:attach_interface"
    policy_rules = (("compute", "os_compute_api:os-attach-interfaces"),)

    def allowed(self, request, instance):
        return ((instance.status in ACTIVE_STATES or
                 instance.status == 'SHUTOFF') and
                not is_deleting(instance) and
                api.base.is_service_enabled(request, 'network'))

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        return urls.reverse(self.url, args=[instance_id])


class DetachInterface(policy.PolicyTargetMixin, tables.LinkAction):
    name = "detach_interface"
    verbose_name = _("Detach Interface")
    classes = ("btn-confirm", "ajax-modal")
    url = "horizon:project:instances:detach_interface"
    policy_rules = (("compute", "os_compute_api:os-attach-interfaces:delete"),)

    def allowed(self, request, instance):
        if not api.base.is_service_enabled(request, 'network'):
            return False
        if is_deleting(instance):
            return False
        if (instance.status not in ACTIVE_STATES and
                instance.status != 'SHUTOFF'):
            return False
        for addresses in instance.addresses.values():
            for address in addresses:
                if address.get('OS-EXT-IPS:type') == "fixed":
                    return True
        return False

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        return urls.reverse(self.url, args=[instance_id])


def get_ips(instance):
    template_name = 'project/instances/_instance_ips.html'
    ip_groups = {}

    for ip_group, addresses in instance.addresses.items():
        ip_groups[ip_group] = {}
        ip_groups[ip_group]["floating"] = []
        ip_groups[ip_group]["non_floating"] = []

        for address in addresses:
            if ('OS-EXT-IPS:type' in address and
               address['OS-EXT-IPS:type'] == "floating"):
                ip_groups[ip_group]["floating"].append(address)
            else:
                ip_groups[ip_group]["non_floating"].append(address)

    context = {
        "ip_groups": ip_groups,
    }
    return template.loader.render_to_string(template_name, context)


def get_flavor(instance):
    if hasattr(instance, "full_flavor"):
        template_name = 'project/instances/_instance_flavor.html'
        size_ram = sizeformat.mb_float_format(instance.full_flavor.ram)
        if instance.full_flavor.disk > 0:
            size_disk = sizeformat.diskgbformat(instance.full_flavor.disk)
        else:
            size_disk = _("%s GB") % "0"
        context = {
            "name": instance.full_flavor.name,
            "id": instance.id,
            "size_disk": size_disk,
            "size_ram": size_ram,
            "vcpus": instance.full_flavor.vcpus,
            "flavor_id": instance.full_flavor.id
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")


def get_keyname(instance):
    if hasattr(instance, "key_name"):
        keyname = instance.key_name
        return keyname
    return _("Not available")


def get_power_state(instance):
    return POWER_STATES.get(getattr(instance, "OS-EXT-STS:power_state", 0), '')


STATUS_DISPLAY_CHOICES = (
    ("deleted", pgettext_lazy("Current status of an Instance", u"Deleted")),
    ("active", pgettext_lazy("Current status of an Instance", u"Active")),
    ("shutoff", pgettext_lazy("Current status of an Instance", u"Shutoff")),
    ("suspended", pgettext_lazy("Current status of an Instance",
                                u"Suspended")),
    ("paused", pgettext_lazy("Current status of an Instance", u"Paused")),
    ("error", pgettext_lazy("Current status of an Instance", u"Error")),
    ("resize", pgettext_lazy("Current status of an Instance",
                             u"Resize/Migrate")),
    ("verify_resize", pgettext_lazy("Current status of an Instance",
                                    u"Confirm or Revert Resize/Migrate")),
    ("revert_resize", pgettext_lazy(
        "Current status of an Instance", u"Revert Resize/Migrate")),
    ("reboot", pgettext_lazy("Current status of an Instance", u"Reboot")),
    ("hard_reboot", pgettext_lazy("Current status of an Instance",
                                  u"Hard Reboot")),
    ("password", pgettext_lazy("Current status of an Instance", u"Password")),
    ("rebuild", pgettext_lazy("Current status of an Instance", u"Rebuild")),
    ("migrating", pgettext_lazy("Current status of an Instance",
                                u"Migrating")),
    ("build", pgettext_lazy("Current status of an Instance", u"Build")),
    ("rescue", pgettext_lazy("Current status of an Instance", u"Rescue")),
    ("soft-delete", pgettext_lazy("Current status of an Instance",
                                  u"Soft Deleted")),
    ("shelved", pgettext_lazy("Current status of an Instance", u"Shelved")),
    ("shelved_offloaded", pgettext_lazy("Current status of an Instance",
                                        u"Shelved Offloaded")),
    # these vm states are used when generating CSV usage summary
    ("building", pgettext_lazy("Current status of an Instance", u"Building")),
    ("stopped", pgettext_lazy("Current status of an Instance", u"Stopped")),
    ("rescued", pgettext_lazy("Current status of an Instance", u"Rescued")),
    ("resized", pgettext_lazy("Current status of an Instance", u"Resized")),
)

TASK_DISPLAY_NONE = pgettext_lazy("Task status of an Instance", u"None")

# Mapping of task states taken from Nova's nova/compute/task_states.py
TASK_DISPLAY_CHOICES = (
    ("scheduling", pgettext_lazy("Task status of an Instance",
                                 u"Scheduling")),
    ("block_device_mapping", pgettext_lazy("Task status of an Instance",
                                           u"Block Device Mapping")),
    ("networking", pgettext_lazy("Task status of an Instance",
                                 u"Networking")),
    ("spawning", pgettext_lazy("Task status of an Instance", u"Spawning")),
    ("image_snapshot", pgettext_lazy("Task status of an Instance",
                                     u"Snapshotting")),
    ("image_snapshot_pending", pgettext_lazy("Task status of an Instance",
                                             u"Image Snapshot Pending")),
    ("image_pending_upload", pgettext_lazy("Task status of an Instance",
                                           u"Image Pending Upload")),
    ("image_uploading", pgettext_lazy("Task status of an Instance",
                                      u"Image Uploading")),
    ("image_backup", pgettext_lazy("Task status of an Instance",
                                   u"Image Backup")),
    ("updating_password", pgettext_lazy("Task status of an Instance",
                                        u"Updating Password")),
    ("resize_prep", pgettext_lazy("Task status of an Instance",
                                  u"Preparing Resize or Migrate")),
    ("resize_migrating", pgettext_lazy("Task status of an Instance",
                                       u"Resizing or Migrating")),
    ("resize_migrated", pgettext_lazy("Task status of an Instance",
                                      u"Resized or Migrated")),
    ("resize_finish", pgettext_lazy("Task status of an Instance",
                                    u"Finishing Resize or Migrate")),
    ("resize_reverting", pgettext_lazy("Task status of an Instance",
                                       u"Reverting Resize or Migrate")),
    ("resize_confirming", pgettext_lazy("Task status of an Instance",
                                        u"Confirming Resize or Migrate")),
    ("rebooting", pgettext_lazy("Task status of an Instance", u"Rebooting")),
    ("reboot_pending", pgettext_lazy("Task status of an Instance",
                                     u"Reboot Pending")),
    ("reboot_started", pgettext_lazy("Task status of an Instance",
                                     u"Reboot Started")),
    ("rebooting_hard", pgettext_lazy("Task status of an Instance",
                                     u"Hard Rebooting")),
    ("reboot_pending_hard", pgettext_lazy("Task status of an Instance",
                                          u"Hard Reboot Pending")),
    ("reboot_started_hard", pgettext_lazy("Task status of an Instance",
                                          u"Hard Reboot Started")),
    ("pausing", pgettext_lazy("Task status of an Instance", u"Pausing")),
    ("unpausing", pgettext_lazy("Task status of an Instance", u"Resuming")),
    ("suspending", pgettext_lazy("Task status of an Instance",
                                 u"Suspending")),
    ("resuming", pgettext_lazy("Task status of an Instance", u"Resuming")),
    ("powering-off", pgettext_lazy("Task status of an Instance",
                                   u"Powering Off")),
    ("powering-on", pgettext_lazy("Task status of an Instance",
                                  u"Powering On")),
    ("rescuing", pgettext_lazy("Task status of an Instance", u"Rescuing")),
    ("unrescuing", pgettext_lazy("Task status of an Instance",
                                 u"Unrescuing")),
    ("rebuilding", pgettext_lazy("Task status of an Instance",
                                 u"Rebuilding")),
    ("rebuild_block_device_mapping", pgettext_lazy(
        "Task status of an Instance", u"Rebuild Block Device Mapping")),
    ("rebuild_spawning", pgettext_lazy("Task status of an Instance",
                                       u"Rebuild Spawning")),
    ("migrating", pgettext_lazy("Task status of an Instance", u"Migrating")),
    ("deleting", pgettext_lazy("Task status of an Instance", u"Deleting")),
    ("soft-deleting", pgettext_lazy("Task status of an Instance",
                                    u"Soft Deleting")),
    ("restoring", pgettext_lazy("Task status of an Instance", u"Restoring")),
    ("shelving", pgettext_lazy("Task status of an Instance", u"Shelving")),
    ("shelving_image_pending_upload", pgettext_lazy(
        "Task status of an Instance", u"Shelving Image Pending Upload")),
    ("shelving_image_uploading", pgettext_lazy("Task status of an Instance",
                                               u"Shelving Image Uploading")),
    ("shelving_offloading", pgettext_lazy("Task status of an Instance",
                                          u"Shelving Offloading")),
    ("unshelving", pgettext_lazy("Task status of an Instance",
                                 u"Unshelving")),
)

POWER_DISPLAY_CHOICES = (
    ("NO STATE", pgettext_lazy("Power state of an Instance", u"No State")),
    ("RUNNING", pgettext_lazy("Power state of an Instance", u"Running")),
    ("BLOCKED", pgettext_lazy("Power state of an Instance", u"Blocked")),
    ("PAUSED", pgettext_lazy("Power state of an Instance", u"Paused")),
    ("SHUTDOWN", pgettext_lazy("Power state of an Instance", u"Shut Down")),
    ("SHUTOFF", pgettext_lazy("Power state of an Instance", u"Shut Off")),
    ("CRASHED", pgettext_lazy("Power state of an Instance", u"Crashed")),
    ("SUSPENDED", pgettext_lazy("Power state of an Instance", u"Suspended")),
    ("FAILED", pgettext_lazy("Power state of an Instance", u"Failed")),
    ("BUILDING", pgettext_lazy("Power state of an Instance", u"Building")),
)

INSTANCE_FILTER_CHOICES = (
    ('uuid', _("Instance ID ="), True),
    ('name', _("Instance Name ="), True),
    ('image', _("Image ID ="), True),
    ('image_name', _("Image Name ="), True),
    ('ip', _("IPv4 Address ="), True),
    ('ip6', _("IPv6 Address ="), True, None,
     api.neutron.is_enabled_by_config('enable_ipv6')),
    ('flavor', _("Flavor ID ="), True),
    ('flavor_name', _("Flavor Name ="), True),
    ('key_name', _("Key Pair Name ="), True),
    ('status', _("Status ="), True),
    ('availability_zone', _("Availability Zone ="), True),
    ('changes-since', _("Changes Since"), True,
        _("Filter by an ISO 8061 formatted time, e.g. 2016-06-14T06:27:59Z")),
    ('vcpus', _("vCPUs ="), True),
)


class InstancesFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = INSTANCE_FILTER_CHOICES


def render_locked(instance):
    if not hasattr(instance, 'locked'):
        return ""
    if instance.locked:
        icon_classes = "fa mdi-lock"
        help_tooltip = _("This instance is currently locked. To enable more "
                         "actions on it, please unlock it by selecting Unlock "
                         "Instance from the actions menu.")
    else:
        icon_classes = "fa mdi-lock-open-outline text-muted"
        help_tooltip = _("This instance is unlocked.")

    locked_status = ('<span data-toggle="tooltip" title="{}" class="{}">'
                     '</span>').format(help_tooltip, icon_classes)
    return mark_safe(locked_status)


def get_server_detail_link(obj, request):
    return get_url_with_pagination(request,
                                   InstancesTable._meta.pagination_param,
                                   InstancesTable._meta.prev_pagination_param,
                                   'horizon:project:instances:detail',
                                   obj.id)


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
        ("rescue", True),
        ("shelved", True),
        ("shelved_offloaded", True),
    )
    name = tables.WrappingColumn("name",
                                 link=get_server_detail_link,
                                 verbose_name=_("Instance Name"))
    image_name = tables.WrappingColumn("image_name",
                                       verbose_name=_("Image Name"))
    ip = tables.Column(get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    flavor = tables.Column(get_flavor,
                           sortable=False,
                           verbose_name=_("Flavor"))
    keypair = tables.Column(get_keyname, verbose_name=_("Key Pair"))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    locked = tables.Column(render_locked,
                           verbose_name="",
                           sortable=False)
    az = tables.Column("availability_zone",
                       verbose_name=_("Availability Zone"))
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         empty_value=TASK_DISPLAY_NONE,
                         status=True,
                         status_choices=TASK_STATUS_CHOICES,
                         display_choices=TASK_DISPLAY_CHOICES)
    state = tables.Column(get_power_state,
                          filters=(title, filters.replace_underscores),
                          verbose_name=_("Power State"),
                          display_choices=POWER_DISPLAY_CHOICES)
    created = tables.Column("created",
                            verbose_name=_("Time since created"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    class Meta(object):
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["status", "task"]
        row_class = UpdateRow
        table_actions_menu = (StartInstance, StopInstance, SoftRebootInstance)
        launch_actions = ()
        if getattr(settings, 'LAUNCH_INSTANCE_LEGACY_ENABLED', False):
            launch_actions = (LaunchLink,) + launch_actions
        if getattr(settings, 'LAUNCH_INSTANCE_NG_ENABLED', True):
            launch_actions = (LaunchLinkNG,) + launch_actions
        table_actions = launch_actions + (DeleteInstance,
                                          InstancesFilterAction)
        row_actions = (StartInstance, ConfirmResize, RevertResize,
                       CreateSnapshot, AssociateIP, DisassociateIP,
                       AttachInterface, DetachInterface, EditInstance,
                       AttachVolume, DetachVolume,
                       UpdateMetadata, DecryptInstancePassword,
                       EditInstanceSecurityGroups,
                       EditPortSecurityGroups,
                       ConsoleLink, LogLink,
                       TogglePause, ToggleSuspend, ToggleShelve,
                       ResizeLink, LockInstance, UnlockInstance,
                       SoftRebootInstance, RebootInstance,
                       StopInstance, RebuildInstance, DeleteInstance)
