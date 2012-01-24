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

from django.template import defaultfilters as filters
from django.utils.translation import ugettext as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteImage(tables.DeleteAction):
    data_type_singular = _("Image")
    data_type_plural = _("Images")

    def allowed(self, request, image=None):
        if image:
            return image.owner == request.user.id
        return True

    def delete(self, request, obj_id):
        api.image_delete(request, obj_id)


class LaunchImage(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch")
    url = "horizon:nova:images_and_snapshots:images:launch"
    attrs = {"class": "ajax-modal"}


class EditImage(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:nova:images_and_snapshots:images:update"
    attrs = {"class": "ajax-modal"}


def get_image_type(image):
    return getattr(image.properties, "image_type", "Image")


def get_container_format(image):
    container_format = getattr(image, "container_format", "")
    # The "container_format" attribute can actually be set to None,
    # which will raise an error if you call upper() on it.
    if container_format is not None:
        return container_format.upper()


class ImagesTable(tables.DataTable):
    name = tables.Column("name")
    image_type = tables.Column(get_image_type,
                               verbose_name=_("Type"),
                               filters=(filters.title,))
    status = tables.Column("status", filters=(filters.title,))
    public = tables.Column("is_public",
                           verbose_name=_("Public"),
                           empty_value=False,
                           filters=(filters.yesno, filters.capfirst))
    container_format = tables.Column(get_container_format,
                                     verbose_name=_("Container Format"))

    class Meta:
        name = "images"
        verbose_name = _("Images")
        table_actions = (DeleteImage,)
        row_actions = (LaunchImage, EditImage, DeleteImage)
