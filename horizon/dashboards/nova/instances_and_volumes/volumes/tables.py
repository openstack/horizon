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

from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.defaultfilters import title
from django.utils import safestring
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import tables


LOG = logging.getLogger(__name__)

URL_PREFIX = "horizon:nova:instances_and_volumes"
DELETABLE_STATES = ("available", "error")


class DeleteVolume(tables.DeleteAction):
    data_type_singular = _("Volume")
    data_type_plural = _("Volumes")

    def delete(self, request, obj_id):
        api.volume_delete(request, obj_id)

    def allowed(self, request, volume=None):
        if volume:
            return volume.status in DELETABLE_STATES
        return True


class CreateVolume(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume")
    url = "%s:volumes:create" % URL_PREFIX
    classes = ("ajax-modal", "btn-create")


class EditAttachments(tables.LinkAction):
    name = "attachments"
    verbose_name = _("Edit Attachments")
    url = "%s:volumes:attach" % URL_PREFIX
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


class CreateSnapshot(tables.LinkAction):
    name = "snapshots"
    verbose_name = _("Create Snapshot")
    url = "%s:volumes:create_snapshot" % URL_PREFIX
    classes = ("ajax-modal", "btn-camera")

    def allowed(self, request, volume=None):
        return volume.status == "available"


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_id):
        volume = api.volume_get(request, volume_id)
        return volume


def get_size(volume):
    return _("%sGB") % volume.size


def get_attachment_name(request, attachment):
    server_id = attachment.get("server_id", None)
    if "instance" in attachment:
        name = attachment["instance"].name
    else:
        try:
            server = api.nova.server_get(request, server_id)
            name = server.name
        except:
            name = None
            exceptions.handle(request, _("Unable to retrieve "
                                         "attachment information."))
    try:
        url = reverse("%s:instances:detail" % URL_PREFIX, args=(server_id,))
        instance = '<a href="%s">%s</a>' % (url, name)
    except NoReverseMatch:
        instance = name
    return instance


class AttachmentColumn(tables.Column):
    """
    Customized column class that does complex processing on the attachments
    for a volume instance.
    """
    def get_raw_data(self, volume):
        request = self.table._meta.request
        link = _('Attached to %(instance)s on %(dev)s')
        attachments = []
        # Filter out "empty" attachments which the client returns...
        for attachment in [att for att in volume.attachments if att]:
            # When a volume is first attached it may return the server_id
            # without the server name...
            instance = get_attachment_name(request, attachment)
            vals = {"instance": instance,
                    "dev": attachment["device"]}
            attachments.append(link % vals)
        return safestring.mark_safe(", ".join(attachments))


class VolumesTableBase(tables.DataTable):
    STATUS_CHOICES = (
        ("in-use", True),
        ("available", True),
        ("creating", None),
        ("error", False),
    )
    name = tables.Column("display_name", verbose_name=_("Name"),
                         link="%s:volumes:detail" % URL_PREFIX)
    description = tables.Column("display_description",
                                verbose_name=_("Description"))
    size = tables.Column(get_size, verbose_name=_("Size"))
    status = tables.Column("status",
                           filters=(title,),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

    def get_object_display(self, obj):
        return obj.display_name


class VolumesTable(VolumesTableBase):
    name = tables.Column("display_name",
                         verbose_name=_("Name"),
                         link="%s:volumes:detail" % URL_PREFIX)
    attachments = AttachmentColumn("attachments",
                                verbose_name=_("Attached To"))

    class Meta:
        name = "volumes"
        verbose_name = _("Volumes")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateVolume, DeleteVolume,)
        row_actions = (EditAttachments, CreateSnapshot, DeleteVolume)


class DetachVolume(tables.BatchAction):
    name = "detach"
    action_present = _("Detach")
    action_past = _("Detaching")  # This action is asynchronous.
    data_type_singular = _("Volume")
    data_type_plural = _("Volumes")
    classes = ('btn-danger', 'btn-detach')

    def action(self, request, obj_id):
        attachment = self.table.get_object_by_id(obj_id)
        api.volume_detach(request, attachment.get('server_id', None), obj_id)

    def get_success_url(self, request):
        return reverse('%s:index' % URL_PREFIX)


class AttachedInstanceColumn(tables.Column):
    """
    Customized column class that does complex processing on the attachments
    for a volume instance.
    """
    def get_raw_data(self, attachment):
        request = self.table._meta.request
        return safestring.mark_safe(get_attachment_name(request, attachment))


class AttachmentsTable(tables.DataTable):
    instance = AttachedInstanceColumn(get_attachment_name,
                                      verbose_name=_("Instance"))
    device = tables.Column("device")

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, attachment):
        instance_name = get_attachment_name(self._meta.request, attachment)
        vals = {"dev": attachment['device'],
                "instance_name": strip_tags(instance_name)}
        return _("%(dev)s on instance %(instance_name)s") % vals

    def get_object_by_id(self, obj_id):
        for obj in self.data:
            if self.get_object_id(obj) == obj_id:
                return obj
        raise ValueError('No match found for the id "%s".' % obj_id)

    class Meta:
        name = "attachments"
        table_actions = (DetachVolume,)
        row_actions = (DetachVolume,)
