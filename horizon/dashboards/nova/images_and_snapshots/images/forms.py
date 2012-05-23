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
Views for managing Nova images.
"""

import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class UpdateImageForm(forms.SelfHandlingForm):
    completion_view = 'horizon:nova:images_and_snapshots:index'

    image_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length="255", label=_("Name"))
    kernel = forms.CharField(max_length="36", label=_("Kernel ID"),
                             required=False,
                             widget=forms.TextInput(
                                attrs={'readonly': 'readonly'}
                             ))
    ramdisk = forms.CharField(max_length="36", label=_("Ramdisk ID"),
                              required=False,
                              widget=forms.TextInput(
                                attrs={'readonly': 'readonly'}
                              ))
    architecture = forms.CharField(label=_("Architecture"), required=False,
                                   widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}
                                   ))
    container_format = forms.CharField(label=_("Container Format"),
                                       widget=forms.TextInput(
                                        attrs={'readonly': 'readonly'}
                                       ))
    disk_format = forms.CharField(label=_("Disk Format"),
                                  widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}
                                  ))
    public = forms.BooleanField(label=_("Public"),
                                required=False)

    def handle(self, request, data):
        # TODO add public flag to image meta properties
        image_id = data['image_id']
        error_updating = _('Unable to update image "%s".')

        meta = {'is_public': data['public'],
                'disk_format': data['disk_format'],
                'container_format': data['container_format'],
                'name': data['name'],
                'properties': {}}
        if data['kernel']:
            meta['properties']['kernel_id'] = data['kernel']
        if data['ramdisk']:
            meta['properties']['ramdisk_id'] = data['ramdisk']
        if data['architecture']:
            meta['properties']['architecture'] = data['architecture']

        try:
            api.image_update(request, image_id, **meta)
            messages.success(request, _('Image was successfully updated.'))
        except:
            exceptions.handle(request, error_updating % image_id)
        return shortcuts.redirect(self.get_success_url())
