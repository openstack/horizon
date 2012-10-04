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

from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class LaunchImage(tables.LinkAction):
    name = "launch_image"
    verbose_name = _("Launch")
    url = "horizon:project:instances:launch"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"source_type": "image_id",
                            "source_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])


class DeleteImage(tables.DeleteAction):
    data_type_singular = _("Image")
    data_type_plural = _("Images")

    def allowed(self, request, image=None):
        if image:
            return image.owner == request.user.tenant_id
        # Return True to allow table-level bulk delete action to appear.
        return True

    def delete(self, request, obj_id):
        api.image_delete(request, obj_id)


class CreateImage(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Image")
    url = "horizon:project:images_and_snapshots:images:create"
    classes = ("ajax-modal", "btn-create")


class EditImage(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:project:images_and_snapshots:images:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, image=None):
        if image:
            return image.status in ("active",) and \
                image.owner == request.user.tenant_id
        # We don't have bulk editing, so if there isn't an image that's
        # authorized, don't allow the action.
        return False


def get_image_type(image):
    return getattr(image, "properties", {}).get("image_type", _("Image"))


def get_format(image):
    format = getattr(image, "disk_format", "")
    # The "container_format" attribute can actually be set to None,
    # which will raise an error if you call upper() on it.
    if format is not None:
        return format.upper()


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, image_id):
        image = api.image_get(request, image_id)
        return image


class ImagesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("saving", None),
        ("queued", None),
        ("pending_delete", None),
        ("killed", False),
        ("deleted", False),
    )
    name = tables.Column("name",
                         link=("horizon:project:images_and_snapshots:"
                               "images:detail"),
                         verbose_name=_("Image Name"))
    image_type = tables.Column(get_image_type,
                               verbose_name=_("Type"),
                               filters=(filters.title,))
    status = tables.Column("status",
                           filters=(filters.title,),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)
    public = tables.Column("is_public",
                           verbose_name=_("Public"),
                           empty_value=False,
                           filters=(filters.yesno, filters.capfirst))
    disk_format = tables.Column(get_format, verbose_name=_("Format"))

    class Meta:
        name = "images"
        row_class = UpdateRow
        status_columns = ["status"]
        verbose_name = _("Images")
        table_actions = (CreateImage, DeleteImage,)
        row_actions = (LaunchImage, EditImage, DeleteImage,)
        pagination_param = "image_marker"
