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
Views for managing images.
"""

import logging

from django.conf import settings
from django.forms import ValidationError
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class CreateImageForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Name"), required=True)
    copy_from = forms.CharField(max_length="255",
                                label=_("Image Location"),
                                help_text=_("An external (HTTP) URL to load "
                                            "the image from."),
                                required=False)
    image_file = forms.FileField(label=_("Image File"),
                                 help_text=("A local image to upload."),
                                 required=False)
    disk_format = forms.ChoiceField(label=_('Format'),
                                    required=True,
                                    choices=[('', ''),
                                             ('aki',
                                                _('AKI - Amazon Kernel '
                                                        'Image')),
                                             ('ami',
                                                _('AMI - Amazon Machine '
                                                        'Image')),
                                             ('ari',
                                                _('ARI - Amazon Ramdisk '
                                                        'Image')),
                                             ('iso',
                                                _('ISO - Optical Disk Image')),
                                             ('qcow2',
                                                _('QCOW2 - QEMU Emulator')),
                                             ('raw', 'Raw'),
                                             ('vdi', 'VDI'),
                                             ('vhd', 'VHD'),
                                             ('vmdk', 'VMDK')],
                                    widget=forms.Select(attrs={'class':
                                                               'switchable'}))
    minimum_disk = forms.IntegerField(label=_("Minimum Disk (GB)"),
                                    help_text=_('The minimum disk size'
                                            ' required to boot the'
                                            ' image. If unspecified, this'
                                            ' value defaults to 0'
                                            ' (no minimum).'),
                                    required=False)
    minimum_ram = forms.IntegerField(label=_("Minimum Ram (MB)"),
                                    help_text=_('The minimum disk size'
                                            ' required to boot the'
                                            ' image. If unspecified, this'
                                            ' value defaults to 0 (no'
                                            ' minimum).'),
                                    required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False)

    def __init__(self, *args, **kwargs):
        super(CreateImageForm, self).__init__(*args, **kwargs)
        if not settings.HORIZON_IMAGES_ALLOW_UPLOAD:
            self.fields['image_file'].widget = HiddenInput()

    def clean(self):
        data = super(CreateImageForm, self).clean()
        if not data['copy_from'] and not data['image_file']:
            raise ValidationError(
                _("A image or external image location must be specified."))
        elif data['copy_from'] and data['image_file']:
            raise ValidationError(
                _("Can not specify both image and external image location."))
        else:
            return data

    def handle(self, request, data):
        # Glance does not really do anything with container_format at the
        # moment. It requires it is set to the same disk_format for the three
        # Amazon image types, otherwise it just treats them as 'bare.' As such
        # we will just set that to be that here instead of bothering the user
        # with asking them for information we can already determine.
        if data['disk_format'] in ('ami', 'aki', 'ari',):
            container_format = data['disk_format']
        else:
            container_format = 'bare'

        meta = {'is_public': data['is_public'],
                'disk_format': data['disk_format'],
                'container_format': container_format,
                'min_disk': (data['minimum_disk'] or 0),
                'min_ram': (data['minimum_ram'] or 0),
                'name': data['name']}

        if settings.HORIZON_IMAGES_ALLOW_UPLOAD and data['image_file']:
            meta['data'] = self.files['image_file']
        else:
            meta['copy_from'] = data['copy_from']

        try:
            image = api.glance.image_create(request, **meta)
            messages.success(request,
                _('Your image %s has been queued for creation.' %
                    data['name']))
            return image
        except:
            exceptions.handle(request, _('Unable to create new image.'))


class UpdateImageForm(forms.SelfHandlingForm):
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
    disk_format = forms.CharField(label=_("Format"),
                                  widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}
                                  ))
    public = forms.BooleanField(label=_("Public"), required=False)

    def handle(self, request, data):
        image_id = data['image_id']
        error_updating = _('Unable to update image "%s".')

        if data['disk_format'] in ['aki', 'ari', 'ami']:
            container_format = data['disk_format']
        else:
            container_format = 'bare'

        meta = {'is_public': data['public'],
                'disk_format': data['disk_format'],
                'container_format': container_format,
                'name': data['name'],
                'properties': {}}
        if data['kernel']:
            meta['properties']['kernel_id'] = data['kernel']
        if data['ramdisk']:
            meta['properties']['ramdisk_id'] = data['ramdisk']
        if data['architecture']:
            meta['properties']['architecture'] = data['architecture']
        # Ensure we do not delete properties that have already been
        # set on an image.
        meta['purge_props'] = False

        try:
            image = api.glance.image_update(request, image_id, **meta)
            messages.success(request, _('Image was successfully updated.'))
            return image
        except:
            exceptions.handle(request, error_updating % image_id)
