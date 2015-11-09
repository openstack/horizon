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

import os

from django import http
from django.utils.functional import cached_property  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views import generic
import six

from horizon import browsers
from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon.utils.urlresolvers import reverse  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import swift
from openstack_dashboard.dashboards.project.containers \
    import browsers as project_browsers
from openstack_dashboard.dashboards.project.containers \
    import forms as project_forms
from openstack_dashboard.dashboards.project.containers import utils


class ContainerView(browsers.ResourceBrowserView):
    browser_class = project_browsers.ContainerBrowser
    template_name = "project/containers/index.html"

    def get_containers_data(self):
        containers = []
        self._more = None
        marker = self.request.GET.get('marker', None)
        try:
            containers, self._more = api.swift.swift_get_containers(
                self.request, marker=marker)
        except Exception:
            msg = _('Unable to retrieve container list.')
            exceptions.handle(self.request, msg)
        return containers

    @cached_property
    def objects(self):
        """Returns a list of objects given the subfolder's path.

        The path is from the kwargs of the request.
        """
        objects = []
        self._more = None
        marker = self.request.GET.get('marker', None)
        container_name = self.kwargs['container_name']
        subfolder = self.kwargs['subfolder_path']
        prefix = None
        if container_name:
            self.navigation_selection = True
            if subfolder:
                prefix = subfolder
            try:
                objects, self._more = api.swift.swift_get_objects(
                    self.request,
                    container_name,
                    marker=marker,
                    prefix=prefix)
            except Exception:
                self._more = None
                objects = []
                msg = _('Unable to retrieve object list.')
                exceptions.handle(self.request, msg)
        return objects

    def is_subdir(self, item):
        content_type = "application/pseudo-folder"
        return getattr(item, "content_type", None) == content_type

    def is_placeholder(self, item):
        object_name = getattr(item, "name", "")
        return object_name.endswith(api.swift.FOLDER_DELIMITER)

    def get_objects_data(self):
        """Returns a list of objects within the current folder."""
        filtered_objects = [item for item in self.objects
                            if (not self.is_subdir(item) and
                                not self.is_placeholder(item))]
        return filtered_objects

    def get_subfolders_data(self):
        """Returns a list of subfolders within the current folder."""
        filtered_objects = [item for item in self.objects
                            if self.is_subdir(item)]
        return filtered_objects

    def get_context_data(self, **kwargs):
        context = super(ContainerView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['subfolders'] = []
        if self.kwargs["subfolder_path"]:
            (parent, slash, folder) = self.kwargs["subfolder_path"] \
                                          .strip('/').rpartition('/')
            while folder:
                path = "%s%s%s/" % (parent, slash, folder)
                context['subfolders'].insert(0, (folder, path))
                (parent, slash, folder) = parent.rpartition('/')
        return context


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateContainer
    template_name = 'project/containers/create.html'
    success_url = "horizon:project:containers:index"
    page_title = _("Create Container")

    def get_success_url(self):
        parent = self.request.POST.get('parent', None)
        if parent:
            container, slash, remainder = parent.partition(
                swift.FOLDER_DELIMITER)
            args = (utils.wrap_delimiter(container),
                    utils.wrap_delimiter(remainder))
            return reverse(self.success_url, args=args)
        else:
            container = utils.wrap_delimiter(self.request.POST['name'])
            return reverse(self.success_url, args=[container])

    def get_initial(self):
        initial = super(CreateView, self).get_initial()
        initial['parent'] = self.kwargs['container_name']
        return initial


class CreatePseudoFolderView(forms.ModalFormView):
    form_class = project_forms.CreatePseudoFolder
    template_name = 'project/containers/create_pseudo_folder.html'
    success_url = "horizon:project:containers:index"
    page_title = _("Create Pseudo-folder")

    def get_success_url(self):
        container_name = self.request.POST['container_name']
        return reverse(self.success_url,
                       args=(utils.wrap_delimiter(container_name),
                             self.request.POST.get('path', '')))

    def get_initial(self):
        return {"container_name": self.kwargs["container_name"],
                "path": self.kwargs['subfolder_path']}

    def get_context_data(self, **kwargs):
        context = super(CreatePseudoFolderView, self). \
            get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        return context


class UploadView(forms.ModalFormView):
    form_class = project_forms.UploadObject
    template_name = 'project/containers/upload.html'
    success_url = "horizon:project:containers:index"
    page_title = _("Upload Objects")

    def get_success_url(self):
        container = utils.wrap_delimiter(self.request.POST['container_name'])
        path = utils.wrap_delimiter(self.request.POST.get('path', ''))
        args = (container, path)
        return reverse(self.success_url, args=args)

    def get_initial(self):
        return {"container_name": self.kwargs["container_name"],
                "path": self.kwargs['subfolder_path']}

    def get_context_data(self, **kwargs):
        context = super(UploadView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        return context


def object_download(request, container_name, object_path):
    try:
        obj = api.swift.swift_get_object(request, container_name, object_path,
                                         resp_chunk_size=swift.CHUNK_SIZE)
    except Exception:
        redirect = reverse("horizon:project:containers:index")
        exceptions.handle(request,
                          _("Unable to retrieve object."),
                          redirect=redirect)
    # Add the original file extension back on if it wasn't preserved in the
    # name given to the object.
    filename = object_path.rsplit(swift.FOLDER_DELIMITER)[-1]
    if not os.path.splitext(obj.name)[1] and obj.orig_name:
        name, ext = os.path.splitext(obj.orig_name)
        filename = "%s%s" % (filename, ext)
    response = http.StreamingHttpResponse(obj.data)
    safe_name = filename.replace(",", "")
    if six.PY2:
        safe_name = safe_name.encode('utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % safe_name
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Length'] = obj.bytes
    return response


class CopyView(forms.ModalFormView):
    form_class = project_forms.CopyObject
    template_name = 'project/containers/copy.html'
    success_url = "horizon:project:containers:index"
    page_title = _("Copy Object")

    def get_success_url(self):
        container = utils.wrap_delimiter(
            self.request.POST['new_container_name'])
        path = utils.wrap_delimiter(self.request.POST.get('path', ''))
        args = (container, path)
        return reverse(self.success_url, args=args)

    def get_form_kwargs(self):
        kwargs = super(CopyView, self).get_form_kwargs()
        try:
            containers = api.swift.swift_get_containers(self.request)
        except Exception:
            redirect = reverse("horizon:project:containers:index")
            exceptions.handle(self.request,
                              _('Unable to list containers.'),
                              redirect=redirect)
        kwargs['containers'] = [(c.name, c.name) for c in containers[0]]
        return kwargs

    @staticmethod
    def get_copy_name(object_name):
        filename, ext = os.path.splitext(object_name)
        return "%s.copy%s" % (filename, ext)

    def get_initial(self):
        path = self.kwargs["subfolder_path"]
        object_name = self.kwargs["object_name"]
        orig = "%s%s" % (path or '', object_name)

        return {"new_container_name": self.kwargs["container_name"],
                "orig_container_name": self.kwargs["container_name"],
                "orig_object_name": orig,
                "path": path,
                "new_object_name": self.get_copy_name(object_name)}

    def get_context_data(self, **kwargs):
        context = super(CopyView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['object_name'] = self.kwargs["object_name"]
        return context


class ContainerDetailView(forms.ModalFormMixin, generic.TemplateView):
    template_name = 'project/containers/container_detail.html'
    page_title = _("Container Details")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.swift.swift_get_container(
                self.request,
                self.kwargs["container_name"],
                with_data=False)
        except Exception:
            redirect = reverse("horizon:project:containers:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve details.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ContainerDetailView, self).get_context_data(**kwargs)
        context['container'] = self.get_object()
        return context


class ObjectDetailView(forms.ModalFormMixin, generic.TemplateView):
    template_name = 'project/containers/object_detail.html'
    page_title = _("Object Details")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.swift.swift_get_object(
                self.request,
                self.kwargs["container_name"],
                self.kwargs["object_path"],
                with_data=False)
        except Exception:
            redirect = reverse("horizon:project:containers:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve details.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ObjectDetailView, self).get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context


class UpdateObjectView(forms.ModalFormView):
    form_class = project_forms.UpdateObject
    template_name = 'project/containers/update.html'
    success_url = "horizon:project:containers:index"
    page_title = _("Update Object")

    def get_success_url(self):
        container = utils.wrap_delimiter(self.request.POST['container_name'])
        path = utils.wrap_delimiter(self.request.POST.get('path', ''))
        args = (container, path)
        return reverse(self.success_url, args=args)

    def get_initial(self):
        return {"container_name": self.kwargs["container_name"],
                "path": self.kwargs["subfolder_path"],
                "name": self.kwargs["object_name"]}

    def get_context_data(self, **kwargs):
        context = super(UpdateObjectView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['subfolder_path'] = self.kwargs["subfolder_path"]
        context['object_name'] = self.kwargs["object_name"]
        return context
