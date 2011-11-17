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

import logging

from cloudfiles.errors import ContainerNotEmpty
from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class DeleteContainer(forms.SelfHandlingForm):
    container_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            api.swift_delete_container(request, data['container_name'])
        except ContainerNotEmpty, e:
            messages.error(request,
                           _('Unable to delete non-empty container: %s') %
                           data['container_name'])
            LOG.exception('Unable to delete container "%s".  Exception: "%s"' %
                      (data['container_name'], str(e)))
        else:
            messages.info(request,
                      _('Successfully deleted container: %s') % \
                      data['container_name'])
        return shortcuts.redirect(request.build_absolute_uri())


class CreateContainer(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Container Name"))

    def handle(self, request, data):
        api.swift_create_container(request, data['name'])
        messages.success(request, _("Container was successfully created."))
        return shortcuts.redirect("horizon:nova:containers:index")


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
        return shortcuts.redirect("horizon:nova:containers:object_index",
                                  data['container_name'])


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

        return shortcuts.redirect("horizon:nova:containers:object_index",
                                  data['new_container_name'])
