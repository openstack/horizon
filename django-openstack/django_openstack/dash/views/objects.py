# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development, Inc.
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

from django_openstack import api
from django_openstack import forms


LOG = logging.getLogger('django_openstack.dash')


class DeleteObject(forms.SelfHandlingForm):
    object_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        api.swift_delete_object(
                request.POST['container_name'],
                data['object_name'])
        messages.info(request,
                      'Successfully deleted object: %s' % \
                      data['object_name'])
        return shortcuts.redirect(request.build_absolute_uri())


class UploadObject(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label="Object Name")
    object_file = forms.FileField(label="File")

    def handle(self, request, data):
        api.swift_upload_object(
                request.POST['container_name'],
                data['name'],
                request.FILES['object_file'].read())

        messages.success(request, "Object was successfully uploaded.")
        return shortcuts.redirect(request.build_absolute_uri())


class CopyObject(forms.SelfHandlingForm):
    container_choices = []

    for idx, container in enumerate(api.swift_get_containers()):
        container_choices.append((container.name, container.name))

    new_container_name = forms.ChoiceField(
        choices=container_choices,
        label="Container to store object in")

    new_object_name = forms.CharField(max_length="255",
                                      label="New object name")

    def handle(self, request, data):
        orig_container_name = request.POST['orig_container_name']
        orig_object_name = request.POST['orig_object_name']
        new_container_name = request.POST['new_container_name']
        new_object_name = data['new_object_name']

        api.swift_copy_object(orig_container_name, orig_object_name,
                              new_container_name, new_object_name)

        messages.success(request,
                         'Object was successfully copied to %s\%s' %
                         (new_container_name, new_object_name))

        return shortcuts.redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id, container_name):
    delete_form, handled = DeleteObject.maybe_handle(request)
    if handled:
        return handled

    objects = api.swift_get_objects(container_name)

    return render_to_response('dash_objects.html', {
        'container_name': container_name,
        'objects': objects,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))


@login_required
def upload(request, tenant_id, container_name):
    form, handled = UploadObject.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('dash_objects_upload.html', {
        'container_name': container_name,
        'upload_form': form,
    }, context_instance=template.RequestContext(request))


@login_required
def download(request, tenant_id, container_name, object_name):
    object_data = api.swift_get_object_data(
            container_name, object_name)

    response = http.HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=%s' % \
            object_name
    for data in object_data:
        response.write(data)
    return response


@login_required
def copy(request, tenant_id, container_name, object_name):
    form, handled = CopyObject.maybe_handle(request)

    form.fields['new_container_name'].initial = container_name

    if handled:
        return handled

    return render_to_response(
        'dash_object_copy.html',
        {'container_name': container_name,
         'object_name': object_name,
         'copy_form': form },
        context_instance=template.RequestContext(request))
