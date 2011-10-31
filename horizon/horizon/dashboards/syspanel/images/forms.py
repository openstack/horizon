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
from django.contrib import messages
from django.utils.translation import ugettext as _

from glance.common import exception as glance_exception

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class DeleteImage(forms.SelfHandlingForm):
    image_id = forms.CharField(required=True)

    def handle(self, request, data):
        image_id = data['image_id']
        try:
            api.image_delete(request, image_id)
        except glance_exception.ClientConnectionError, e:
            LOG.exception("Error connecting to glance")
            messages.error(request,
                           _("Error connecting to glance: %s") % e.message)
        except glance_exception.Error, e:
            LOG.exception('Error deleting image with id "%s"' % image_id)
            messages.error(request, _("Error deleting image: %s") % e.message)
        return shortcuts.redirect(request.build_absolute_uri())


class ToggleImage(forms.SelfHandlingForm):
    image_id = forms.CharField(required=True)

    def handle(self, request, data):
        image_id = data['image_id']
        try:
            api.image_update(request, image_id,
                    image_meta={'is_public': False})
        except glance_exception.ClientConnectionError, e:
            LOG.exception("Error connecting to glance")
            messages.error(request,
                           _("Error connecting to glance: %s") % e.message)
        except glance_exception.Error, e:
            LOG.exception('Error updating image with id "%s"' % image_id)
            messages.error(request, _("Error updating image: %s") % e.message)
        return shortcuts.redirect(request.build_absolute_uri())


class UpdateImageForm(forms.Form):
    name = forms.CharField(max_length="25", label=_("Name"))
    kernel = forms.CharField(max_length="25", label=_("Kernel ID"),
            required=False)
    ramdisk = forms.CharField(max_length="25", label=_("Ramdisk ID"),
            required=False)
    architecture = forms.CharField(label=_("Architecture"), required=False)
    #project_id = forms.CharField(label=_("Project ID"))
    container_format = forms.CharField(label=_("Container Format"),
            required=False)
    disk_format = forms.CharField(label=_("Disk Format"))
    #is_public = forms.BooleanField(label=_("Publicly Available"),
    #                               required=False)
