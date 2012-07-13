# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

"""
Views for managing Swift containers.
"""
import logging
import os

from django import http
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from .forms import CreateContainer, UploadObject, CopyObject
from .tables import ContainersTable, ObjectsTable,\
                        ContainerSubfoldersTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = ContainersTable
    template_name = 'nova/containers/index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        containers = []
        self._more = None
        marker = self.request.GET.get('marker', None)
        try:
            containers, self._more = api.swift_get_containers(self.request,
                                                              marker=marker)
        except:
            msg = _('Unable to retrieve container list.')
            exceptions.handle(self.request, msg)
        return containers


class CreateView(forms.ModalFormView):
    form_class = CreateContainer
    template_name = 'nova/containers/create.html'
    success_url = "horizon:nova:containers:object_index"

    def get_success_url(self):
        parent = self.request.POST.get('parent', None)
        if parent:
            container, slash, remainder = parent.partition("/")
            if remainder and not remainder.endswith("/"):
                remainder = "".join([remainder, "/"])
            return reverse(self.success_url, args=(container, remainder))
        else:
            return reverse(self.success_url, args=[self.request.POST['name']])

    def get_initial(self):
        initial = super(CreateView, self).get_initial()
        initial['parent'] = self.kwargs['container_name']
        return initial


class ObjectIndexView(tables.MultiTableView):
    table_classes = (ObjectsTable, ContainerSubfoldersTable)
    template_name = 'nova/containers/detail.html'

    def has_more_data(self, table):
        return self._more

    @property
    def objects(self):
        """ Returns a list of objects given the subfolder's path.

        The path is from the kwargs of the request
        """
        if not hasattr(self, "_objects"):
            objects = []
            self._more = None
            marker = self.request.GET.get('marker', None)
            container_name = self.kwargs['container_name']
            subfolders = self.kwargs['subfolder_path']
            if subfolders:
                prefix = subfolders.rstrip("/")
            else:
                prefix = None
            try:
                objects, self._more = api.swift_get_objects(self.request,
                                                            container_name,
                                                            marker=marker,
                                                            path=prefix)
            except:
                objects = []
                msg = _('Unable to retrieve object list.')
                exceptions.handle(self.request, msg)
            self._objects = objects
        return self._objects

    def get_objects_data(self):
        """ Returns the objects within the in the current folder.

        These objects are those whose names don't contain '/' after
        striped the path out
        """
        filtered_objects = [item for item in self.objects if
                            item.content_type != "application/directory"]
        return filtered_objects

    def get_subfolders_data(self):
        """ Returns a list of subfolders given the current folder path.
        """
        filtered_objects = [item for item in self.objects if
                            item.content_type == "application/directory"]
        return filtered_objects

    def get_context_data(self, **kwargs):
        context = super(ObjectIndexView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['subfolder_path'] = self.kwargs["subfolder_path"]
        return context


class UploadView(forms.ModalFormView):
    form_class = UploadObject
    template_name = 'nova/containers/upload.html'
    success_url = "horizon:nova:containers:object_index"

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.request.POST['container_name'],
                             self.request.POST.get('path', '')))

    def get_initial(self):
        return {"container_name": self.kwargs["container_name"],
                "path": self.kwargs['subfolder_path']}

    def get_context_data(self, **kwargs):
        context = super(UploadView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        return context


def object_download(request, container_name, object_path):
    obj = api.swift.swift_get_object(request, container_name, object_path)
    # Add the original file extension back on if it wasn't preserved in the
    # name given to the object.
    filename = object_path.rsplit("/")[-1]
    if not os.path.splitext(obj.name)[1]:
        name, ext = os.path.splitext(obj.metadata.get('orig-filename', ''))
        filename = "%s%s" % (filename, ext)
    try:
        object_data = api.swift_get_object_data(request,
                                                container_name,
                                                object_path)
    except:
        redirect = reverse("horizon:nova:containers:index")
        exceptions.handle(request,
                          _("Unable to retrieve object."),
                          redirect=redirect)
    response = http.HttpResponse()
    safe_name = filename.replace(",", "").encode('utf-8')
    response['Content-Disposition'] = 'attachment; filename=%s' % safe_name
    response['Content-Type'] = 'application/octet-stream'
    for data in object_data:
        response.write(data)
    return response


class CopyView(forms.ModalFormView):
    form_class = CopyObject
    template_name = 'nova/containers/copy.html'
    success_url = "horizon:nova:containers:object_index"

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.request.POST['new_container_name'],
                             self.request.POST.get('path', '')))

    def get_form_kwargs(self):
        kwargs = super(CopyView, self).get_form_kwargs()
        try:
            containers = api.swift_get_containers(self.request)
        except:
            redirect = reverse("horizon:nova:containers:index")
            exceptions.handle(self.request,
                              _('Unable to list containers.'),
                              redirect=redirect)
        kwargs['containers'] = [(c.name, c.name) for c in containers[0]]
        return kwargs

    def get_initial(self):
        path = self.kwargs["subfolder_path"]
        orig = "%s%s" % (path or '', self.kwargs["object_name"])
        return {"new_container_name": self.kwargs["container_name"],
                "orig_container_name": self.kwargs["container_name"],
                "orig_object_name": orig,
                "path": path,
                "new_object_name": "%s copy" % self.kwargs["object_name"]}

    def get_context_data(self, **kwargs):
        context = super(CopyView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['object_name'] = self.kwargs["object_name"]
        return context
