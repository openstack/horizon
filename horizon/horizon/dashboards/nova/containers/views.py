# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

"""
Views for managing Swift containers.
"""
import logging
import os

from django import http
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from .forms import CreateContainer, UploadObject, CopyObject
from .tables import ContainersTable, ObjectsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = ContainersTable
    template_name = 'nova/containers/index.html'

    def has_more_data(self):
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


class ObjectIndexView(tables.DataTableView):
    table_class = ObjectsTable
    template_name = 'nova/objects/index.html'

    def has_more_data(self):
        return self._more

    def get_data(self):
        objects = []
        self._more = None
        marker = self.request.GET.get('marker', None)
        container_name = self.kwargs['container_name']
        try:
            objects, self._more = api.swift_get_objects(self.request,
                                                        container_name,
                                                        marker=marker)
        except:
            msg = _('Unable to retrieve object list.')
            exceptions.handle(self.request, msg)
        return objects

    def get_context_data(self, **kwargs):
        context = super(ObjectIndexView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        return context


class UploadView(forms.ModalFormView):
    form_class = UploadObject
    template_name = 'nova/objects/upload.html'

    def get_initial(self):
        return {"container_name": self.kwargs["container_name"]}

    def get_context_data(self, **kwargs):
        context = super(UploadView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        return context


def object_download(request, container_name, object_name):
    obj = api.swift.swift_get_object(request, container_name, object_name)
    # Add the original file extension back on if it wasn't preserved in the
    # name given to the object.
    filename = object_name
    if not os.path.splitext(obj.name)[1]:
        name, ext = os.path.splitext(obj.metadata.get('orig-filename', ''))
        filename = "%s%s" % (object_name, ext)
    try:
        object_data = api.swift_get_object_data(request,
                                                container_name,
                                                object_name)
    except:
        redirect = reverse("horizon:nova:containers:index")
        exceptions.handle(request,
                          _("Unable to retrieve object."),
                          redirect=redirect)
    response = http.HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Type'] = 'application/octet-stream'
    for data in object_data:
        response.write(data)
    return response


class CopyView(forms.ModalFormView):
    form_class = CopyObject
    template_name = 'nova/objects/copy.html'

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
        return {"new_container_name": self.kwargs["container_name"],
                "orig_container_name": self.kwargs["container_name"],
                "orig_object_name": self.kwargs["object_name"],
                "new_object_name": "%s copy" % self.kwargs["object_name"]}

    def get_context_data(self, **kwargs):
        context = super(CopyView, self).get_context_data(**kwargs)
        context['container_name'] = self.kwargs["container_name"]
        context['object_name'] = self.kwargs["object_name"]
        return context
