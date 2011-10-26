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

from django import http
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import shortcuts
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms


LOG = logging.getLogger('django_openstack.dash')


class FilterObjects(forms.SelfHandlingForm):
    container_name = forms.CharField(widget=forms.HiddenInput())
    object_prefix = forms.CharField(required=False)

    def handle(self, request, data):
        object_prefix = data['object_prefix'] or None

        objects = api.swift_get_objects(request,
                                        data['container_name'],
                                        prefix=object_prefix)

        if not objects:
            messages.info(request,
                         _('There are no objects matching that prefix in %s') %
                         data['container_name'])

        return objects


class DeleteObject(forms.SelfHandlingForm):
    object_name = forms.CharField(widget=forms.HiddenInput())
    container_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        api.swift_delete_object(
                request,
                data['container_name'],
                data['object_name'])
        messages.info(request,
                      _('Successfully deleted object: %s') %
                      data['object_name'])
        return shortcuts.redirect(request.build_absolute_uri())


class UploadObject(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Object Name"))
    object_file = forms.FileField(label=_("File"))
    container_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        api.swift_upload_object(
                request,
                data['container_name'],
                data['name'],
                self.files['object_file'].read())

        messages.success(request, _("Object was successfully uploaded."))
        return shortcuts.redirect(request.build_absolute_uri())


class CopyObject(forms.SelfHandlingForm):
    new_container_name = forms.ChoiceField(
        label=_("Container to store object in"))

    new_object_name = forms.CharField(max_length="255",
                                      label=_("New object name"))
    orig_container_name = forms.CharField(widget=forms.HiddenInput())
    orig_object_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        containers = kwargs.pop('containers')

        super(CopyObject, self).__init__(*args, **kwargs)

        self.fields['new_container_name'].choices = containers

    def handle(self, request, data):
        orig_container_name = data['orig_container_name']
        orig_object_name = data['orig_object_name']
        new_container_name = data['new_container_name']
        new_object_name = data['new_object_name']

        api.swift_copy_object(request, orig_container_name,
                              orig_object_name, new_container_name,
                              new_object_name)

        messages.success(request,
                _('Object was successfully copied to %(container)s\%(obj)s') %
                {"container": new_container_name, "obj": new_object_name})

        return shortcuts.redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id, container_name):
    marker = request.GET.get('marker', None)

    delete_form, handled = DeleteObject.maybe_handle(request)
    if handled:
        return handled

    filter_form, objects = FilterObjects.maybe_handle(request)

    if objects is None:
        filter_form.fields['container_name'].initial = container_name
        objects = api.swift_get_objects(request, container_name, marker=marker)

    delete_form.fields['container_name'].initial = container_name
    return render_to_response(
    'django_openstack/dash/objects/index.html', {
        'container_name': container_name,
        'objects': objects,
        'delete_form': delete_form,
        'filter_form': filter_form,
    }, context_instance=template.RequestContext(request))


@login_required
def upload(request, tenant_id, container_name):
    form, handled = UploadObject.maybe_handle(request)
    if handled:
        return handled

    form.fields['container_name'].initial = container_name
    return render_to_response(
    'django_openstack/dash/objects/upload.html', {
        'container_name': container_name,
        'upload_form': form,
    }, context_instance=template.RequestContext(request))


@login_required
def download(request, tenant_id, container_name, object_name):
    object_data = api.swift_get_object_data(
            request, container_name, object_name)

    response = http.HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=%s' % \
            object_name
    for data in object_data:
        response.write(data)
    return response


@login_required
def copy(request, tenant_id, container_name, object_name):
    containers = \
            [(c.name, c.name) for c in api.swift_get_containers(
                    request)]
    form, handled = CopyObject.maybe_handle(request,
            containers=containers)

    if handled:
        return handled

    form.fields['new_container_name'].initial = container_name
    form.fields['orig_container_name'].initial = container_name
    form.fields['orig_object_name'].initial = object_name

    return render_to_response(
        'django_openstack/dash/objects/copy.html',
        {'container_name': container_name,
         'object_name': object_name,
         'copy_form': form},
        context_instance=template.RequestContext(request))
