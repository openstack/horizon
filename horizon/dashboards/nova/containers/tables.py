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

from cloudfiles.errors import ContainerNotEmpty
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat
from django.utils import http
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteContainer(tables.DeleteAction):
    data_type_singular = _("Container")
    data_type_plural = _("Containers")

    def delete(self, request, obj_id):
        try:
            api.swift_delete_container(request, obj_id)
        except ContainerNotEmpty:
            messages.error(request,
                           _('Containers must be empty before deletion.'))
            raise


class CreateContainer(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Container")
    url = "horizon:nova:containers:create"
    classes = ("ajax-modal", "btn-create")


class ListObjects(tables.LinkAction):
    name = "list_objects"
    verbose_name = _("View Container")
    url = "horizon:nova:containers:object_index"
    classes = ("btn-list",)


class UploadObject(tables.LinkAction):
    name = "upload"
    verbose_name = _("Upload Object")
    url = "horizon:nova:containers:object_upload"
    classes = ("ajax-modal", "btn-upload")

    def get_link_url(self, datum=None):
        # Usable for both the container and object tables
        if getattr(datum, 'container', datum):
            # This is an Container
            container_name = http.urlquote(datum.name)
        else:
            # This is a table action and we already have the container name
            container_name = self.table.kwargs['container_name']
        subfolders = self.table.kwargs.get('subfolder_path', '')
        args = (http.urlquote(bit) for bit in
                (container_name, subfolders) if bit)
        return reverse(self.url, args=args)

    def update(self, request, obj):
        # This will only be called for the row, so we can remove the button
        # styles meant for the table action version.
        self.attrs = {'class': 'ajax-modal'}


def get_size_used(container):
    return filesizeformat(container.size_used)


class ContainersTable(tables.DataTable):
    name = tables.Column("name", link='horizon:nova:containers:object_index',
                         verbose_name=_("Container Name"))
    objects = tables.Column("object_count",
                            verbose_name=_('Objects'),
                            empty_value="0")
    size = tables.Column(get_size_used, verbose_name=_('Size'))

    def get_object_id(self, container):
        return container.name

    class Meta:
        name = "containers"
        verbose_name = _("Containers")
        table_actions = (CreateContainer, DeleteContainer)
        row_actions = (ListObjects, UploadObject, DeleteContainer)


class DeleteObject(tables.DeleteAction):
    data_type_singular = _("Object")
    data_type_plural = _("Objects")

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        container_name = obj.container.name
        api.swift_delete_object(request, container_name, obj_id)


class CopyObject(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy")
    url = "horizon:nova:containers:object_copy"
    classes = ("ajax-modal", "btn-copy")

    def get_link_url(self, obj):
        return reverse(self.url, args=(http.urlquote(obj.container.name),
                                       http.urlquote(obj.name)))


class DownloadObject(tables.LinkAction):
    name = "download"
    verbose_name = _("Download")
    url = "horizon:nova:containers:object_download"
    classes = ("btn-download",)

    def get_link_url(self, obj):
        return reverse(self.url, args=(http.urlquote(obj.container.name),
                                       http.urlquote(obj.name)))


class ObjectFilterAction(tables.FilterAction):
    def filter(self, table, objects, filter_string):
        request = table._meta.request
        container = self.table.kwargs['container_name']
        subfolder = self.table.kwargs['subfolder_path']
        path = subfolder + '/' if subfolder else ''
        return api.swift_filter_objects(request,
                                        filter_string,
                                        container,
                                        path=path)


def sanitize_name(name):
    return name.split("/")[-1]


def get_size(obj):
    return filesizeformat(obj.size)


class ObjectsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Object Name"),
                         filters=(sanitize_name,))
    size = tables.Column(get_size, verbose_name=_('Size'))

    def get_object_id(self, obj):
        return obj.name

    class Meta:
        name = "objects"
        verbose_name = _("Objects")
        table_actions = (ObjectFilterAction, UploadObject, DeleteObject)
        row_actions = (DownloadObject, CopyObject, DeleteObject)


def get_link_subfolder(subfolder):
    return reverse("horizon:nova:containers:object_index",
                    args=(http.urlquote(subfolder.container.name),
                            http.urlquote(subfolder.name + "/")))


class CreateSubfolder(CreateContainer):
    verbose_name = _("Create Folder")
    url = "horizon:nova:containers:create"

    def get_link_url(self):
        container = self.table.kwargs['container_name']
        subfolders = self.table.kwargs['subfolder_path']
        parent = "/".join((bit for bit in [container, subfolders] if bit))
        parent = parent.rstrip("/")
        return reverse(self.url, args=(http.urlquote(parent + "/"),))


class DeleteSubfolder(DeleteObject):
    data_type_singular = _("Folder")
    data_type_plural = _("Folders")


class ContainerSubfoldersTable(tables.DataTable):
    name = tables.Column("name",
                         link=get_link_subfolder,
                         verbose_name=_("Subfolder Name"),
                         filters=(sanitize_name,))

    def get_object_id(self, obj):
        return obj.name

    class Meta:
        name = "subfolders"
        verbose_name = _("Subfolders")
        table_actions = (CreateSubfolder, DeleteSubfolder)
        row_actions = (DeleteSubfolder,)
