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

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch  # noqa
from django.core.urlresolvers import reverse
from django.http import HttpResponse  # noqa
from django.template import defaultfilters as filters
from django.utils import html
from django.utils.http import urlencode
from django.utils import safestring
from django.utils.translation import pgettext_lazy
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard import policy


DELETABLE_STATES = ("available", "error", "error_extending")


class VolumePolicyTargetMixin(policy.PolicyTargetMixin):
    policy_target_attrs = (("project_id", 'os-vol-tenant-attr:tenant_id'),)


class LaunchVolume(tables.LinkAction):
    name = "launch_volume"
    verbose_name = _("Launch as Instance")
    url = "horizon:project:instances:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    policy_rules = (("compute", "compute:create"),)

    def get_link_url(self, datum):
        base_url = reverse(self.url)

        vol_id = "%s:vol" % self.table.get_object_id(datum)
        params = urlencode({"source_type": "volume_id",
                            "source_id": vol_id})
        return "?".join([base_url, params])

    def allowed(self, request, volume=None):
        if getattr(volume, 'bootable', '') == 'true':
            return volume.status == "available"
        return False


class LaunchVolumeNG(LaunchVolume):
    name = "launch_volume_ng"
    verbose_name = _("Launch as Instance")
    url = "horizon:project:volumes:index"
    classes = ("btn-launch", )
    ajax = False

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(LaunchVolume, self).__init__(attrs, **kwargs)

    def get_link_url(self, datum):
        url = reverse(self.url)
        vol_id = "%s:vol" % self.table.get_object_id(datum)
        ngclick = "modal.openLaunchInstanceWizard(" \
            "{successUrl: '%s', volumeId: '%s'})" \
                  % (url, vol_id.split(":vol")[0])
        self.attrs.update({
            "ng-controller": "LaunchInstanceModalController as modal",
            "ng-click": ngclick
        })
        return "javascript:void(0);"


class DeleteVolume(VolumePolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Volume",
            u"Delete Volumes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Volume",
            u"Scheduled deletion of Volumes",
            count
        )

    policy_rules = (("volume", "volume:delete"),)

    def delete(self, request, obj_id):
        cinder.volume_delete(request, obj_id)

    def allowed(self, request, volume=None):
        if volume:
            return (volume.status in DELETABLE_STATES and
                    not getattr(volume, 'has_snapshot', False))
        return True


class CreateVolume(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume")
    url = "horizon:project:volumes:volumes:create"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"
    policy_rules = (("volume", "volume:create"),)
    ajax = True

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(CreateVolume, self).__init__(attrs, **kwargs)

    def allowed(self, request, volume=None):
        limits = api.cinder.tenant_absolute_limits(request)

        gb_available = (limits.get('maxTotalVolumeGigabytes', float("inf"))
                        - limits.get('totalGigabytesUsed', 0))
        volumes_available = (limits.get('maxTotalVolumes', float("inf"))
                             - limits.get('totalVolumesUsed', 0))

        if gb_available <= 0 or volumes_available <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
        else:
            self.verbose_name = _("Create Volume")
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
        return True

    def single(self, table, request, object_id=None):
        self.allowed(request, None)
        return HttpResponse(self.render(is_table_action=True))


class ExtendVolume(VolumePolicyTargetMixin, tables.LinkAction):
    name = "extend"
    verbose_name = _("Extend Volume")
    url = "horizon:project:volumes:volumes:extend"
    classes = ("ajax-modal", "btn-extend")
    policy_rules = (("volume", "volume:extend"),)

    def allowed(self, request, volume=None):
        return volume.status == "available"


class EditAttachments(tables.LinkAction):
    name = "attachments"
    verbose_name = _("Manage Attachments")
    url = "horizon:project:volumes:volumes:attach"
    classes = ("ajax-modal",)
    icon = "pencil"

    def allowed(self, request, volume=None):
        if volume:
            project_id = getattr(volume, "os-vol-tenant-attr:tenant_id", None)
            attach_allowed = \
                policy.check((("compute", "compute:attach_volume"),),
                             request,
                             {"project_id": project_id})
            detach_allowed = \
                policy.check((("compute", "compute:detach_volume"),),
                             request,
                             {"project_id": project_id})

            if attach_allowed or detach_allowed:
                return volume.status in ("available", "in-use")
        return False


class CreateSnapshot(VolumePolicyTargetMixin, tables.LinkAction):
    name = "snapshots"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:volumes:volumes:create_snapshot"
    classes = ("ajax-modal",)
    icon = "camera"
    policy_rules = (("volume", "volume:create_snapshot"),)

    def allowed(self, request, volume=None):
        try:
            limits = api.cinder.tenant_absolute_limits(request)
        except Exception:
            exceptions.handle(request, _('Unable to retrieve tenant limits.'))
            limits = {}

        snapshots_available = (limits.get('maxTotalSnapshots', float("inf"))
                               - limits.get('totalSnapshotsUsed', 0))

        if snapshots_available <= 0 and "disabled" not in self.classes:
            self.classes = [c for c in self.classes] + ['disabled']
            self.verbose_name = string_concat(self.verbose_name, ' ',
                                              _("(Quota exceeded)"))
        return volume.status in ("available", "in-use")


class CreateTransfer(VolumePolicyTargetMixin, tables.LinkAction):
    name = "create_transfer"
    verbose_name = _("Create Transfer")
    url = "horizon:project:volumes:volumes:create_transfer"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "volume:create_transfer"),)

    def allowed(self, request, volume=None):
        return volume.status == "available"


class CreateBackup(VolumePolicyTargetMixin, tables.LinkAction):
    name = "backups"
    verbose_name = _("Create Backup")
    url = "horizon:project:volumes:volumes:create_backup"
    classes = ("ajax-modal",)
    policy_rules = (("volume", "backup:create"),)

    def allowed(self, request, volume=None):
        return (cinder.volume_backup_supported(request) and
                volume.status == "available")


class UploadToImage(VolumePolicyTargetMixin, tables.LinkAction):
    name = "upload_to_image"
    verbose_name = _("Upload to Image")
    url = "horizon:project:volumes:volumes:upload_to_image"
    classes = ("ajax-modal",)
    icon = "cloud-upload"
    policy_rules = (("volume", "volume:upload_to_image"),)

    def allowed(self, request, volume=None):
        has_image_service_perm = \
            request.user.has_perm('openstack.services.image')

        return (volume.status in ("available", "in-use") and
                has_image_service_perm)


class EditVolume(VolumePolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Volume")
    url = "horizon:project:volumes:volumes:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume:update"),)

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


class RetypeVolume(VolumePolicyTargetMixin, tables.LinkAction):
    name = "retype"
    verbose_name = _("Change Volume Type")
    url = "horizon:project:volumes:volumes:retype"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume:retype"),)

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


class AcceptTransfer(tables.LinkAction):
    name = "accept_transfer"
    verbose_name = _("Accept Transfer")
    url = "horizon:project:volumes:volumes:accept_transfer"
    classes = ("ajax-modal",)
    icon = "exchange"
    policy_rules = (("volume", "volume:accept_transfer"),)
    ajax = True

    def single(self, table, request, object_id=None):
        return HttpResponse(self.render())


class DeleteTransfer(VolumePolicyTargetMixin, tables.Action):
    # This class inherits from tables.Action instead of the more obvious
    # tables.DeleteAction due to the confirmation message.  When the delete
    # is successful, DeleteAction automatically appends the name of the
    # volume to the message, e.g. "Deleted volume transfer 'volume'". But
    # we are deleting the volume *transfer*, whose name is different.
    name = "delete_transfer"
    verbose_name = _("Cancel Transfer")
    policy_rules = (("volume", "volume:delete_transfer"),)
    classes = ('btn-danger',)
    help_text = _("This action cannot be undone.")

    def allowed(self, request, volume):
        return (volume.status == "awaiting-transfer" and
                getattr(volume, 'transfer', None))

    def single(self, table, request, volume_id):
        volume = table.get_object_by_id(volume_id)
        try:
            cinder.transfer_delete(request, volume.transfer.id)
            if volume.transfer.name:
                msg = _('Successfully deleted volume transfer "%s"'
                        ) % volume.transfer.name
            else:
                msg = _("Successfully deleted volume transfer")
            messages.success(request, msg)
        except Exception:
            exceptions.handle(request, _("Unable to delete volume transfer."))


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_id):
        volume = cinder.volume_get(request, volume_id)
        return volume


def get_size(volume):
    return _("%sGiB") % volume.size


def get_attachment_name(request, attachment):
    server_id = attachment.get("server_id", None)
    if "instance" in attachment and attachment['instance']:
        name = attachment["instance"].name
    else:
        try:
            server = api.nova.server_get(request, server_id)
            name = server.name
        except Exception:
            name = None
            exceptions.handle(request, _("Unable to retrieve "
                                         "attachment information."))
    try:
        url = reverse("horizon:project:instances:detail", args=(server_id,))
        instance = '<a href="%s">%s</a>' % (url, html.escape(name))
    except NoReverseMatch:
        instance = html.escape(name)
    return instance


class AttachmentColumn(tables.Column):
    """Customized column class.

    So it that does complex processing on the attachments
    for a volume instance.
    """
    def get_raw_data(self, volume):
        request = self.table.request
        link = _('Attached to %(instance)s on %(dev)s')
        attachments = []
        # Filter out "empty" attachments which the client returns...
        for attachment in [att for att in volume.attachments if att]:
            # When a volume is attached it may return the server_id
            # without the server name...
            instance = get_attachment_name(request, attachment)
            vals = {"instance": instance,
                    "dev": html.escape(attachment.get("device", ""))}
            attachments.append(link % vals)
        return safestring.mark_safe(", ".join(attachments))


def get_volume_type(volume):
    return volume.volume_type if volume.volume_type != "None" else None


def get_encrypted_value(volume):
    if not hasattr(volume, 'encrypted') or volume.encrypted is None:
        return _("-")
    elif volume.encrypted is False:
        return _("No")
    else:
        return _("Yes")


class VolumesTableBase(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
        ("error_extending", False),
        ("maintenance", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available", pgettext_lazy("Current status of a Volume",
                                    u"Available")),
        ("in-use", pgettext_lazy("Current status of a Volume", u"In-use")),
        ("error", pgettext_lazy("Current status of a Volume", u"Error")),
        ("creating", pgettext_lazy("Current status of a Volume",
                                   u"Creating")),
        ("error_extending", pgettext_lazy("Current status of a Volume",
                                          u"Error Extending")),
        ("extending", pgettext_lazy("Current status of a Volume",
                                    u"Extending")),
        ("attaching", pgettext_lazy("Current status of a Volume",
                                    u"Attaching")),
        ("detaching", pgettext_lazy("Current status of a Volume",
                                    u"Detaching")),
        ("deleting", pgettext_lazy("Current status of a Volume",
                                   u"Deleting")),
        ("error_deleting", pgettext_lazy("Current status of a Volume",
                                         u"Error deleting")),
        ("backing-up", pgettext_lazy("Current status of a Volume",
                                     u"Backing Up")),
        ("restoring-backup", pgettext_lazy("Current status of a Volume",
                                           u"Restoring Backup")),
        ("error_restoring", pgettext_lazy("Current status of a Volume",
                                          u"Error Restoring")),
        ("maintenance", pgettext_lazy("Current status of a Volume",
                                      u"Maintenance")),
    )
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:volumes:volumes:detail")
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                truncate=40)
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    def get_object_display(self, obj):
        return obj.name


class VolumesFilterAction(tables.FilterAction):

    def filter(self, table, volumes, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [volume for volume in volumes
                if q in volume.name.lower()]


class VolumesTable(VolumesTableBase):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:volumes:volumes:detail")
    volume_type = tables.Column(get_volume_type,
                                verbose_name=_("Type"))
    attachments = AttachmentColumn("attachments",
                                   verbose_name=_("Attached To"))
    availability_zone = tables.Column("availability_zone",
                                      verbose_name=_("Availability Zone"))
    bootable = tables.Column('is_bootable',
                             verbose_name=_("Bootable"),
                             filters=(filters.yesno, filters.capfirst))
    encryption = tables.Column(get_encrypted_value,
                               verbose_name=_("Encrypted"),
                               link="horizon:project:volumes:"
                                    "volumes:encryption_detail")

    class Meta(object):
        name = "volumes"
        verbose_name = _("Volumes")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateVolume, AcceptTransfer, DeleteVolume,
                         VolumesFilterAction)

        launch_actions = ()
        if getattr(settings, 'LAUNCH_INSTANCE_LEGACY_ENABLED', False):
            launch_actions = (LaunchVolume,) + launch_actions
        if getattr(settings, 'LAUNCH_INSTANCE_NG_ENABLED', True):
            launch_actions = (LaunchVolumeNG,) + launch_actions

        row_actions = ((EditVolume, ExtendVolume,) +
                       launch_actions +
                       (EditAttachments, CreateSnapshot, CreateBackup,
                        RetypeVolume, UploadToImage, CreateTransfer,
                        DeleteTransfer, DeleteVolume))


class DetachVolume(tables.BatchAction):
    name = "detach"
    classes = ('btn-danger', 'btn-detach')
    policy_rules = (("compute", "compute:detach_volume"),)
    help_text = _("The data will remain in the volume and another instance"
                  " will be able to access the data if you attach"
                  " this volume to it.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Detach Volume",
            u"Detach Volumes",
            count
        )

    # This action is asynchronous.
    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Detaching Volume",
            u"Detaching Volumes",
            count
        )

    def action(self, request, obj_id):
        attachment = self.table.get_object_by_id(obj_id)
        api.nova.instance_volume_detach(request,
                                        attachment.get('server_id', None),
                                        obj_id)

    def get_success_url(self, request):
        return reverse('horizon:project:volumes:index')


class AttachedInstanceColumn(tables.Column):
    """Customized column class that does complex processing on the attachments
    for a volume instance.
    """
    def get_raw_data(self, attachment):
        request = self.table.request
        return safestring.mark_safe(get_attachment_name(request, attachment))


class AttachmentsTable(tables.DataTable):
    instance = AttachedInstanceColumn(get_attachment_name,
                                      verbose_name=_("Instance"))
    device = tables.Column("device",
                           verbose_name=_("Device"))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, attachment):
        instance_name = get_attachment_name(self.request, attachment)
        vals = {"volume_name": attachment['volume_name'],
                "instance_name": html.strip_tags(instance_name)}
        return _("Volume %(volume_name)s on instance %(instance_name)s") % vals

    def get_object_by_id(self, obj_id):
        for obj in self.data:
            if self.get_object_id(obj) == obj_id:
                return obj
        raise ValueError('No match found for the id "%s".' % obj_id)

    class Meta(object):
        name = "attachments"
        verbose_name = _("Attachments")
        table_actions = (DetachVolume,)
        row_actions = (DetachVolume,)
