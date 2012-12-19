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
from django.template.defaultfilters import filesizeformat
from django.utils import http
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables
from horizon.api import FOLDER_DELIMITER


LOG = logging.getLogger(__name__)


def wrap_delimiter(name):
    if not name.endswith(FOLDER_DELIMITER):
        return name + FOLDER_DELIMITER
    return name


class DeleteContainer(tables.DeleteAction):
    data_type_singular = _("Container")
    data_type_plural = _("Containers")
    success_url = "horizon:nova:containers:index"

    def delete(self, request, obj_id):
        api.swift_delete_container(request, obj_id)

    def get_success_url(self, request=None):
        """
        Returns the URL to redirect to after a successful action.
        """
        current_container = self.table.kwargs.get("container_name", None)

        # If the current_container is deleted, then redirect to the default
        # completion url
        if current_container in self.success_ids:
            return self.success_url
        return request.get_full_path()


class CreateContainer(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Container")
    url = "horizon:nova:containers:create"
    classes = ("ajax-modal", "btn-create")


class ListObjects(tables.LinkAction):
    name = "list_objects"
    verbose_name = _("View Container")
    url = "horizon:nova:containers:index"
    classes = ("btn-list",)

    def get_link_url(self, datum=None):
        container_name = http.urlquote(datum.name)
        args = (wrap_delimiter(container_name),)
        return reverse(self.url, args=args)


class UploadObject(tables.LinkAction):
    name = "upload"
    verbose_name = _("Upload Object")
    url = "horizon:nova:containers:object_upload"
    classes = ("ajax-modal", "btn-upload")

    def get_link_url(self, datum=None):
        # Usable for both the container and object tables
        if getattr(datum, 'container', datum):
            # This is a container
            container_name = http.urlquote(datum.name)
        else:
            # This is a table action, and we already have the container name
            container_name = self.table.kwargs['container_name']
        subfolders = self.table.kwargs.get('subfolder_path', '')
        args = (http.urlquote(bit) for bit in
                (container_name, subfolders) if bit)
        return reverse(self.url, args=args)

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False

    def update(self, request, obj):
        # This will only be called for the row, so we can remove the button
        # styles meant for the table action version.
        self.attrs = {'class': 'ajax-modal'}


def get_size_used(container):
    return filesizeformat(container.bytes)


def get_container_link(container):
    return reverse("horizon:nova:containers:index",
                   args=(http.urlquote(wrap_delimiter(container.name)),))


class ContainersTable(tables.DataTable):
    name = tables.Column("name",
                         link=get_container_link,
                         verbose_name=_("Container Name"))

    def get_object_id(self, container):
        return container.name

    class Meta:
        name = "containers"
        verbose_name = _("Containers")
        table_actions = (CreateContainer,)
        row_actions = (DeleteContainer,)
        browser_table = "navigation"
        footer = False


class DeleteObject(tables.DeleteAction):
    name = "delete_object"
    data_type_singular = _("Object")
    data_type_plural = _("Objects")
    allowed_data_types = ("objects",)

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        container_name = obj.container_name
        api.swift_delete_object(request, container_name, obj_id)


class DeleteSubfolder(DeleteObject):
    name = "delete_subfolder"
    data_type_singular = _("Folder")
    data_type_plural = _("Folders")
    allowed_data_types = ("subfolders",)


class DeleteMultipleObjects(DeleteObject):
    name = "delete_multiple_objects"
    data_type_singular = _("Object")
    data_type_plural = _("Objects")
    allowed_data_types = ("subfolders", "objects",)


class CopyObject(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy")
    url = "horizon:nova:containers:object_copy"
    classes = ("ajax-modal", "btn-copy")
    allowed_data_types = ("objects",)

    def get_link_url(self, obj):
        container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(http.urlquote(container_name),
                                       http.urlquote(obj.name)))


class DownloadObject(tables.LinkAction):
    name = "download"
    verbose_name = _("Download")
    url = "horizon:nova:containers:object_download"
    classes = ("btn-download",)
    allowed_data_types = ("objects",)

    def get_link_url(self, obj):
        container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(http.urlquote(container_name),
                                       http.urlquote(obj.name)))


class ObjectFilterAction(tables.FilterAction):
    def _filtered_data(self, table, filter_string):
        request = table.request
        container = self.table.kwargs['container_name']
        subfolder = self.table.kwargs['subfolder_path']
        prefix = wrap_delimiter(subfolder) if subfolder else ''
        self.filtered_data = api.swift_filter_objects(request,
                                                        filter_string,
                                                        container,
                                                        prefix=prefix)
        return self.filtered_data

    def filter_subfolders_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type == "application/directory"]

    def filter_objects_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type != "application/directory"]

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False


def sanitize_name(name):
    return name.split(FOLDER_DELIMITER)[-1]


def get_size(obj):
    if obj.bytes:
        return filesizeformat(obj.bytes)


def get_link_subfolder(subfolder):
    container_name = subfolder.container_name
    return reverse("horizon:nova:containers:index",
                    args=(http.urlquote(wrap_delimiter(container_name)),
                          http.urlquote(wrap_delimiter(subfolder.name))))


class CreateSubfolder(CreateContainer):
    verbose_name = _("Create Folder")
    url = "horizon:nova:containers:create"

    def get_link_url(self):
        container = self.table.kwargs['container_name']
        subfolders = self.table.kwargs['subfolder_path']
        parent = FOLDER_DELIMITER.join((bit for bit in [container,
                                                        subfolders] if bit))
        parent = parent.rstrip(FOLDER_DELIMITER)
        return reverse(self.url, args=[http.urlquote(wrap_delimiter(parent))])

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False


class ObjectsTable(tables.DataTable):
    name = tables.Column("name",
                         link=get_link_subfolder,
                         allowed_data_types=("subfolders",),
                         verbose_name=_("Object Name"),
                         filters=(sanitize_name,))

    size = tables.Column(get_size, verbose_name=_('Size'))

    def get_object_id(self, obj):
        return obj.name

    class Meta:
        name = "objects"
        verbose_name = _("Objects")
        table_actions = (ObjectFilterAction, CreateSubfolder,
                            UploadObject, DeleteMultipleObjects)
        row_actions = (DownloadObject, CopyObject, DeleteObject,
                        DeleteSubfolder)
        data_types = ("subfolders", "objects")
        browser_table = "content"
        footer = False
