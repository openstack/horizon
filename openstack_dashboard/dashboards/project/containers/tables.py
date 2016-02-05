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
from django import shortcuts
from django import template
from django.template import defaultfilters as filters
from django.utils import http
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.api import swift
from openstack_dashboard.dashboards.project.containers import utils

LOG = logging.getLogger(__name__)


class ViewContainer(tables.LinkAction):
    name = "view"
    verbose_name = _("View Details")
    url = "horizon:project:containers:container_detail"
    classes = ("ajax-modal", "btn-view")

    def get_link_url(self, datum=None):
        obj_id = self.table.get_object_id(datum)
        return reverse(self.url, args=(obj_id,))


class MakePublicContainer(tables.Action):
    name = "make_public"
    verbose_name = _("Make Public")
    icon = "pencil"

    def allowed(self, request, container):
        # Container metadata have not been loaded
        if not hasattr(container, 'is_public'):
            return False
        return not container.is_public

    def single(self, table, request, obj_id):
        try:
            api.swift.swift_update_container(request,
                                             obj_id,
                                             metadata=({'is_public': True}))
            LOG.info('Updating container "%s" access to public.' % obj_id)
            messages.success(request,
                             _('Successfully updated container access to '
                               'public.'))
        except Exception:
            exceptions.handle(request,
                              _('Unable to update container access.'))
        return shortcuts.redirect('horizon:project:containers:index')


class MakePrivateContainer(tables.Action):
    name = "make_private"
    verbose_name = _("Make Private")
    icon = "pencil"

    def allowed(self, request, container):
        # Container metadata have not been loaded
        if not hasattr(container, 'is_public'):
            return False
        return container.is_public

    def single(self, table, request, obj_id):
        try:
            api.swift.swift_update_container(request,
                                             obj_id,
                                             metadata=({'is_public': False}))
            LOG.info('Updating container "%s" access to private.' % obj_id)
            messages.success(request,
                             _('Successfully updated container access to '
                               'private.'))
        except Exception:
            exceptions.handle(request,
                              _('Unable to update container access.'))
        return shortcuts.redirect('horizon:project:containers:index')


class DeleteContainer(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Container",
            u"Delete Containers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Container",
            u"Deleted Containers",
            count
        )

    success_url = "horizon:project:containers:index"

    def delete(self, request, obj_id):
        try:
            api.swift.swift_delete_container(request, obj_id)
        except exceptions.Conflict as exc:
            exceptions.handle(request, exc, redirect=self.success_url)
        except Exception:
            exceptions.handle(request,
                              _('Unable to delete container.'),
                              redirect=self.success_url)

    def get_success_url(self, request=None):
        """Returns the URL to redirect to after a successful action.
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
    url = "horizon:project:containers:create"
    classes = ("ajax-modal",)
    icon = "plus"


class ListObjects(tables.LinkAction):
    name = "list_objects"
    verbose_name = _("View Container")
    url = "horizon:project:containers:index"
    icon = "list"

    def get_link_url(self, datum=None):
        container_name = http.urlquote(datum.name)
        args = (utils.wrap_delimiter(container_name),)
        return reverse(self.url, args=args)


class CreatePseudoFolder(tables.LinkAction):
    name = "create_pseudo_folder"
    verbose_name = _("Create Pseudo-folder")
    url = "horizon:project:containers:create_pseudo_folder"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        # Usable for both the container and object tables
        if getattr(datum, 'container', datum):
            container_name = http.urlquote(datum.name)
        else:
            container_name = self.table.kwargs['container_name']
        subfolders = self.table.kwargs.get('subfolder_path', '')
        args = (bit for bit in (container_name, subfolders) if bit)
        return reverse(self.url, args=args)

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False

    def update(self, request, obj):
        # This will only be called for the row, so we can remove the button
        # styles meant for the table action version.
        self.attrs = {'class': 'ajax-modal'}


class UploadObject(tables.LinkAction):
    name = "upload"
    verbose_name = _("Upload Object")
    url = "horizon:project:containers:object_upload"
    classes = ("ajax-modal",)
    icon = "upload"

    def get_link_url(self, datum=None):
        # Usable for both the container and object tables
        if getattr(datum, 'container', datum):
            # This is a container
            container_name = datum.name
        else:
            # This is a table action, and we already have the container name
            container_name = self.table.kwargs['container_name']
        subfolders = self.table.kwargs.get('subfolder_path', '')
        args = (bit for bit in (container_name, subfolders) if bit)
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
    return filters.filesizeformat(container.bytes)


def get_container_link(container):
    return reverse("horizon:project:containers:index",
                   args=(utils.wrap_delimiter(container.name),))


class ContainerAjaxUpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, container_name):
        container = api.swift.swift_get_container(request,
                                                  container_name,
                                                  with_data=False)
        return container


def get_metadata(container):
    # If the metadata has not been loading, display a loading image
    if not hasattr(container, 'is_public'):
        return template.loader.render_to_string(
            'project/containers/_container_loader.html'
        )
    template_name = 'project/containers/_container_metadata.html'
    context = {"container": container}
    return template.loader.render_to_string(template_name, context)


def get_metadata_loaded(container):
    # Determine if metadata has been loaded if the attribute is already set.
    return hasattr(container, 'is_public') and container.is_public is not None


class ContainersTable(tables.DataTable):
    METADATA_LOADED_CHOICES = (
        (False, None),
        (True, True),
    )
    name = tables.Column("name",
                         link=get_container_link,
                         verbose_name=_("Container Name"))
    metadata = tables.Column(get_metadata,
                             verbose_name=_("Container Details"),
                             classes=('nowrap-col', ),)
    metadata_loaded = tables.Column(get_metadata_loaded,
                                    status=True,
                                    status_choices=METADATA_LOADED_CHOICES,
                                    hidden=True)

    class Meta(object):
        name = "containers"
        verbose_name = _("Containers")
        row_class = ContainerAjaxUpdateRow
        status_columns = ['metadata_loaded', ]
        table_actions = (CreateContainer,)
        row_actions = (ViewContainer, MakePublicContainer,
                       MakePrivateContainer, DeleteContainer,)
        browser_table = "navigation"
        footer = False

    def get_object_id(self, container):
        return container.name


class ViewObject(tables.LinkAction):
    name = "view"
    verbose_name = _("View Details")
    url = "horizon:project:containers:object_detail"
    classes = ("ajax-modal", "btn-view")
    allowed_data_types = ("objects",)

    def get_link_url(self, obj):
        container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(container_name, obj.name))


class UpdateObject(tables.LinkAction):
    name = "update_object"
    verbose_name = _("Edit")
    url = "horizon:project:containers:object_update"
    classes = ("ajax-modal",)
    icon = "pencil"
    allowed_data_types = ("objects",)

    def get_link_url(self, obj):
        container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(container_name, obj.name))


class DeleteObject(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Object",
            u"Delete Objects",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Object",
            u"Deleted Objects",
            count
        )

    name = "delete_object"
    allowed_data_types = ("objects", "subfolders",)

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        container_name = obj.container_name
        datum_type = getattr(obj, self.table._meta.data_type_name, None)
        if datum_type == 'subfolders':
            obj_id = obj_id[(len(container_name) + 1):] + "/"
        api.swift.swift_delete_object(request, container_name, obj_id)


class DeleteMultipleObjects(DeleteObject):
    name = "delete_multiple_objects"


class CopyObject(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy")
    url = "horizon:project:containers:object_copy"
    classes = ("ajax-modal",)
    icon = "circle-arrow-right"
    allowed_data_types = ("objects",)

    def get_link_url(self, obj):
        container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(container_name, obj.name))


class DownloadObject(tables.LinkAction):
    name = "download"
    verbose_name = _("Download")
    url = "horizon:project:containers:object_download"
    icon = "download"
    allowed_data_types = ("objects",)

    def get_link_url(self, obj):
        container_name = self.table.kwargs['container_name']
        return reverse(self.url, args=(container_name, obj.name))

    def allowed(self, request, object):
        return object.bytes and object.bytes > 0


class ObjectFilterAction(tables.FilterAction):
    def _filtered_data(self, table, filter_string):
        request = table.request
        container = self.table.kwargs['container_name']
        subfolder = self.table.kwargs['subfolder_path']
        prefix = utils.wrap_delimiter(subfolder) if subfolder else ''
        self.filtered_data = api.swift.swift_filter_objects(request,
                                                            filter_string,
                                                            container,
                                                            prefix=prefix)
        return self.filtered_data

    def filter_subfolders_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type == "application/pseudo-folder"]

    def filter_objects_data(self, table, objects, filter_string):
        data = self._filtered_data(table, filter_string)
        return [datum for datum in data if
                datum.content_type != "application/pseudo-folder"]

    def allowed(self, request, datum=None):
        if self.table.kwargs.get('container_name', None):
            return True
        return False


def sanitize_name(name):
    return name.split(swift.FOLDER_DELIMITER)[-1]


def get_size(obj):
    if obj.bytes is None:
        return _("pseudo-folder")
    return filters.filesizeformat(obj.bytes)


def get_link_subfolder(subfolder):
    container_name = subfolder.container_name
    return reverse("horizon:project:containers:index",
                   args=(utils.wrap_delimiter(container_name),
                         utils.wrap_delimiter(subfolder.name)))


class ObjectsTable(tables.DataTable):
    name = tables.Column("name",
                         link=get_link_subfolder,
                         allowed_data_types=("subfolders",),
                         verbose_name=_("Object Name"),
                         filters=(sanitize_name,))

    size = tables.Column(get_size, verbose_name=_('Size'))

    class Meta(object):
        name = "objects"
        verbose_name = _("Objects")
        table_actions = (ObjectFilterAction, CreatePseudoFolder, UploadObject,
                         DeleteMultipleObjects)
        row_actions = (DownloadObject, UpdateObject, CopyObject,
                       ViewObject, DeleteObject)
        data_types = ("subfolders", "objects")
        browser_table = "content"
        footer = False
