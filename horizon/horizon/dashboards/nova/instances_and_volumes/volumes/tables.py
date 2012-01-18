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

from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat, title
from django.utils import safestring
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)


class DeleteVolume(tables.DeleteAction):
    data_type_singular = _("Volume")
    data_type_plural = _("Volumes")
    classes = ('danger',)

    def delete(self, request, obj_id):
        api.volume_delete(request, obj_id)


class CreateVolume(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume")
    url = "horizon:nova:instances_and_volumes:volumes:create"
    attrs = {"class": "btn small ajax-modal"}


class EditAttachments(tables.LinkAction):
    name = "attachments"
    verbose_name = _("Edit Attachments")
    url = "horizon:nova:instances_and_volumes:volumes:attach"

    def allowed(self, request, volume=None):
        return volume.status in ("available", "in-use")


def get_size(volume):
    return _("%s GB") % volume.size


def get_attachment(volume):
    attachments = []
    link = '<a href="%(url)s">Instance %(instance)s&nbsp;' \
           '<small>(%(dev)s)</small></a>'
    # Filter out "empty" attachments which the client returns...
    for attachment in [att for att in volume.attachments if att]:
        url = reverse("horizon:nova:instances_and_volumes:instances:detail",
                      args=(attachment["serverId"],))
        # TODO(jake): Make "instance" the instance name
        vals = {"url": url,
                "instance": attachment["serverId"],
                "dev": attachment["device"]}
        attachments.append(link % vals)
    return safestring.mark_safe(", ".join(attachments))


class VolumesTable(tables.DataTable):
    name = tables.Column("displayName",
                         verbose_name=_("Name"),
                         link="horizon:nova:instances_and_volumes:"
                              "volumes:detail")
    description = tables.Column("displayDescription",
                                verbose_name=("Description"))
    size = tables.Column(get_size, verbose_name=_("Size"))
    attachments = tables.Column(get_attachment,
                                verbose_name=_("Attachments"),
                                empty_value=_("-"))
    status = tables.Column("status", filters=(title,))

    def sanitize_id(self, obj_id):
        return int(obj_id)

    def get_object_display(self, obj):
        return obj.displayName

    class Meta:
        name = "volumes"
        verbose_name = _("Volumes")
        table_actions = (CreateVolume, DeleteVolume,)
        row_actions = (EditAttachments, DeleteVolume,)


class DetachVolume(tables.BatchAction):
    name = "detach"
    action_present = _("Detach")
    action_past = _("Detached")
    data_type_singular = _("Volume")
    data_type_plural = _("Volumes")
    classes = ('danger',)

    def action(self, request, obj_id):
        instance_id = self.table.get_object_by_id(obj_id)['serverId']
        api.volume_detach(request, instance_id, obj_id)

    def get_success_url(self, request):
        return reverse('horizon:nova:instances_and_volumes:index')


class AttachmentsTable(tables.DataTable):
    instance = tables.Column("serverId", verbose_name=_("Instance"))
    device = tables.Column("device")

    def sanitize_id(self, obj_id):
        return int(obj_id)

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, obj):
        vals = {"dev": obj['device'],
                "instance": obj['serverId']}
        return "Attachment %(dev)s on %(instance)s" % vals

    def get_object_by_id(self, obj_id):
        for obj in self.data:
            print self.get_object_id(obj)
            if self.get_object_id(obj) == obj_id:
                return obj
        raise ValueError('No match found for the id "%s".' % obj_id)

    class Meta:
        name = "attachments"
        table_actions = (DetachVolume,)
        row_actions = (DetachVolume,)
