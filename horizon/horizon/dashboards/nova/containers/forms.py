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

from django import shortcuts
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class CreateContainer(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Container Name"))

    def handle(self, request, data):
        try:
            api.swift_create_container(request, data['name'])
            messages.success(request, _("Container created successfully."))
        except:
            exceptions.handle(request, _('Unable to create container.'))
        return shortcuts.redirect("horizon:nova:containers:index")


class UploadObject(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Object Name"))
    object_file = forms.FileField(label=_("File"))
    container_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        object_file = self.files['object_file']
        try:
            obj = api.swift_upload_object(request,
                                          data['container_name'],
                                          data['name'],
                                          object_file.read())
            obj.metadata['orig-filename'] = object_file.name
            obj.sync_metadata()
            messages.success(request, _("Object was successfully uploaded."))
        except:
            exceptions.handle(request, _("Unable to upload object."))
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
        object_index = "horizon:nova:containers:object_index"
        orig_container = data['orig_container_name']
        orig_object = data['orig_object_name']
        new_container = data['new_container_name']
        new_object = data['new_object_name']
        try:
            api.swift_copy_object(request,
                                  orig_container,
                                  orig_object,
                                  new_container,
                                  new_object)
            vals = {"container": new_container, "obj": new_object}
            messages.success(request, _('Object "%(obj)s" copied to container '
                                        '"%(container)s".') % vals)
        except:
            redirect = reverse(object_index, args=(orig_container,))
            exceptions.handle(request,
                              _("Unable to copy object."),
                              redirect=redirect)
        return shortcuts.redirect(object_index, new_container)
