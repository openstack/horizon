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

from cloudfiles.errors import ContainerNotEmpty
from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat
from django.utils import http
from django.utils.translation import ugettext as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteContainer(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    verbose_name_plural = _("Delete Containers")
    classes = ('danger',)

    def handle(self, table, request, object_ids):
        deleted = []
        for obj_id in object_ids:
            obj = table.get_object_by_id(obj_id)
            try:
                api.swift_delete_container(request, obj_id)
                deleted.append(obj)
            except ContainerNotEmpty, e:
                LOG.exception('Unable to delete container "%s".' % obj.name)
                messages.error(request,
                               _('Unable to delete non-empty container: %s') %
                               obj.name)
        if deleted:
            messages.success(request,
                             _('Successfully deleted containers: %s')
                               % ", ".join([obj.name for obj in deleted]))
        return shortcuts.redirect('horizon:nova:containers:index')


class CreateContainer(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Container")
    url = "horizon:nova:containers:create"
    attrs = {"class": "btn small ajax-modal"}


class ListObjects(tables.LinkAction):
    name = "list_objects"
    verbose_name = _("List Objects")
    url = "horizon:nova:containers:object_index"


class UploadObject(tables.LinkAction):
    name = "upload"
    verbose_name = _("Upload Object")
    url = "horizon:nova:containers:object_upload"
    attrs = {"class": "btn small ajax-modal"}

    def get_link_url(self, datum=None):
        # Usable for both the container and object tables
        if getattr(datum, 'container', datum):
            # This is an Container
            container_name = http.urlquote(datum.name)
        else:
            # This is a table action and we already have the container name
            container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(container_name,))

    def update(self, request, obj):
        # This will only be called for the row, so we can remove the button
        # styles meant for the table action version.
        self.attrs = {'class': 'ajax-modal'}


def get_size_used(container):
    return filesizeformat(container.size_used)


class ContainersTable(tables.DataTable):
    name = tables.Column("name", link='horizon:nova:containers:object_index')
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


class DeleteObject(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    verbose_name_plural = _("Delete Objects")
    classes = ('danger',)

    def handle(self, table, request, object_ids):
        deleted = []
        for obj_id in object_ids:
            obj = table.get_object_by_id(obj_id)
            container_name = obj.container.name
            try:
                api.swift_delete_object(request, container_name, obj_id)
                deleted.append(obj)
            except Exception, e:
                msg = 'Unable to delete object.'
                LOG.exception(msg)
                messages.error(request, _(msg))
        if deleted:
            messages.success(request,
                             _('Successfully deleted objects: %s')
                               % ", ".join([obj.name for obj in deleted]))
        return shortcuts.redirect('horizon:nova:containers:object_index',
                                  table.kwargs['container_name'])


class CopyObject(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy")
    url = "horizon:nova:containers:object_copy"
    attrs = {"class": "ajax-modal"}

    def get_link_url(self, obj):
        return reverse(self.url, args=(http.urlquote(obj.container.name),
                                       http.urlquote(obj.name)))


class DownloadObject(tables.LinkAction):
    name = "download"
    verbose_name = _("Download")
    url = "horizon:nova:containers:object_download"

    def get_link_url(self, obj):
        #assert False, obj.__dict__['_apiresource'].__dict__
        return reverse(self.url, args=(http.urlquote(obj.container.name),
                                       http.urlquote(obj.name)))


class ObjectFilterAction(tables.FilterAction):
    def filter(self, table, users, filter_string):
        """ Really naive case-insensitive search. """
        # FIXME(gabriel): This should be smarter. Written for demo purposes.
        q = filter_string.lower()

        def comp(user):
            if q in user.name.lower() or q in user.email.lower():
                return True
            return False

        return filter(comp, users)


def get_size(obj):
    return filesizeformat(obj.size)


class ObjectsTable(tables.DataTable):
    name = tables.Column("name")
    size = tables.Column(get_size, verbose_name=_('Size'))

    def get_object_id(self, obj):
        return obj.name

    class Meta:
        name = "objects"
        verbose_name = _("Objects")
        table_actions = (ObjectFilterAction, UploadObject, DeleteObject)
        row_actions = (DownloadObject, CopyObject, DeleteObject)
