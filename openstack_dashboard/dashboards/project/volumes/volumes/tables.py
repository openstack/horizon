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

from django.core.urlresolvers import NoReverseMatch  # noqa
from django.core.urlresolvers import reverse
from django.template.defaultfilters import title  # noqa
from django.utils import html
from django.utils import safestring
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _


from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


DELETABLE_STATES = ("available", "error", "error_extending")


class DeleteVolume(tables.DeleteAction):
    data_type_singular = _("Volume")
    data_type_plural = _("Volumes")
    action_past = _("Scheduled deletion of %(data_type)s")
    policy_rules = (("volume", "volume:delete"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, "os-vol-tenant-attr:tenant_id", None)
        return {"project_id": project_id}

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            cinder.volume_delete(request, obj_id)
        except Exception:
            msg = _('Unable to delete volume "%s". One or more snapshots '
                    'depend on it.')
            exceptions.check_message(["snapshots", "dependent"], msg % name)
            raise

    def allowed(self, request, volume=None):
        if volume:
            return volume.status in DELETABLE_STATES
        return True


class CreateVolume(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume")
    url = "horizon:project:volumes:volumes:create"
    classes = ("ajax-modal", "btn-create")
    policy_rules = (("volume", "volume:create"),)

    def allowed(self, request, volume=None):
        usages = quotas.tenant_quota_usages(request)
        if usages['gigabytes']['available'] <= 0 or\
           usages['volumes']['available'] <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
        else:
            self.verbose_name = _("Create Volume")
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
        return True


class ExtendVolume(tables.LinkAction):
    name = "extend"
    verbose_name = _("Extend Volume")
    url = "horizon:project:volumes:volumes:extend"
    classes = ("ajax-modal", "btn-extend")
    policy_rules = (("volume", "volume:extend"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, "os-vol-tenant-attr:tenant_id", None)
        return {"project_id": project_id}

    def allowed(self, request, volume=None):
        return volume.status == "available"


class EditAttachments(tables.LinkAction):
    name = "attachments"
    verbose_name = _("Edit Attachments")
    url = "horizon:project:volumes:volumes:attach"
    classes = ("ajax-modal", "btn-edit")

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


class CreateSnapshot(tables.LinkAction):
    name = "snapshots"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:volumes:volumes:create_snapshot"
    classes = ("ajax-modal", "btn-camera")
    policy_rules = (("volume", "volume:create_snapshot"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, "os-vol-tenant-attr:tenant_id", None)
        return {"project_id": project_id}

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


class EditVolume(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Volume")
    url = "horizon:project:volumes:volumes:update"
    classes = ("ajax-modal", "btn-edit")
    policy_rules = (("volume", "volume:update"),)

    def get_policy_target(self, request, datum=None):
        project_id = None
        if datum:
            project_id = getattr(datum, "os-vol-tenant-attr:tenant_id", None)
        return {"project_id": project_id}

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_id):
        volume = cinder.volume_get(request, volume_id)
        return volume


def get_size(volume):
    return _("%sGB") % volume.size


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
        instance = name
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
                    "dev": html.escape(attachment["device"])}
            attachments.append(link % vals)
        return safestring.mark_safe(", ".join(attachments))


def get_volume_type(volume):
    return volume.volume_type if volume.volume_type != "None" else None


class VolumesTableBase(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
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
                           filters=(title,),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

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
                                verbose_name=_("Type"),
                                empty_value="-")
    attachments = AttachmentColumn("attachments",
                                verbose_name=_("Attached To"))
    availability_zone = tables.Column("availability_zone",
                         verbose_name=_("Availability Zone"))

    class Meta:
        name = "volumes"
        verbose_name = _("Volumes")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateVolume, DeleteVolume, VolumesFilterAction)
        row_actions = (EditVolume, ExtendVolume, EditAttachments,
                       CreateSnapshot, DeleteVolume)


class DetachVolume(tables.BatchAction):
    name = "detach"
    action_present = _("Detach")
    action_past = _("Detaching")  # This action is asynchronous.
    data_type_singular = _("Volume")
    data_type_plural = _("Volumes")
    classes = ('btn-danger', 'btn-detach')
    policy_rules = (("compute", "compute:detach_volume"),)

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
        vals = {"dev": attachment['device'],
                "instance_name": html.strip_tags(instance_name)}
        return _("%(dev)s on instance %(instance_name)s") % vals

    def get_object_by_id(self, obj_id):
        for obj in self.data:
            if self.get_object_id(obj) == obj_id:
                return obj
        raise ValueError('No match found for the id "%s".' % obj_id)

    class Meta:
        name = "attachments"
        verbose_name = _("Attachments")
        table_actions = (DetachVolume,)
        row_actions = (DetachVolume,)
