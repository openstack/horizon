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

from django.conf import settings
from django.core import validators
from django.forms import ValidationError  # noqa
from django.forms.widgets import HiddenInput  # noqa
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import policy


IMAGE_BACKEND_SETTINGS = getattr(settings, 'OPENSTACK_IMAGE_BACKEND', {})
IMAGE_FORMAT_CHOICES = IMAGE_BACKEND_SETTINGS.get('image_formats', [])


class ImageURLField(forms.URLField):
    default_validators = [validators.URLValidator(schemes=["http", "https"])]


def create_image_metadata(data):
    """Use the given dict of image form data to generate the metadata used for
    creating the image in glance.
    """
    # Glance does not really do anything with container_format at the
    # moment. It requires it is set to the same disk_format for the three
    # Amazon image types, otherwise it just treats them as 'bare.' As such
    # we will just set that to be that here instead of bothering the user
    # with asking them for information we can already determine.
    disk_format = data['disk_format']
    if disk_format in ('ami', 'aki', 'ari',):
        container_format = disk_format
    elif disk_format == 'docker':
        # To support docker containers we allow the user to specify
        # 'docker' as the format. In that case we really want to use
        # 'raw' as the disk format and 'docker' as the container format.
        disk_format = 'raw'
        container_format = 'docker'
    else:
        container_format = 'bare'

    # The Create form uses 'is_public' but the Update form uses 'public'. Just
    # being tolerant here so we don't break anything else.
    meta = {'is_public': data.get('is_public', data.get('public', False)),
            'protected': data['protected'],
            'disk_format': disk_format,
            'container_format': container_format,
            'min_disk': (data['minimum_disk'] or 0),
            'min_ram': (data['minimum_ram'] or 0),
            'name': data['name'],
            'properties': {}}

    if 'description' in data:
        meta['properties']['description'] = data['description']
    if data.get('kernel'):
        meta['properties']['kernel_id'] = data['kernel']
    if data.get('ramdisk'):
        meta['properties']['ramdisk_id'] = data['ramdisk']
    if data.get('architecture'):
        meta['properties']['architecture'] = data['architecture']
    return meta


class CreateImageForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))
    description = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_("Description"),
        required=False)
    source_type = forms.ChoiceField(
        label=_('Image Source'),
        required=False,
        choices=[('url', _('Image Location')),
                 ('file', _('Image File'))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'source'}))
    image_url_attrs = {
        'class': 'switched',
        'data-switch-on': 'source',
        'data-source-url': _('Image Location'),
        'ng-model': 'ctrl.copyFrom',
        'ng-change': 'ctrl.selectImageFormat(ctrl.copyFrom)'
    }
    image_url = ImageURLField(label=_("Image Location"),
                              help_text=_("An external (HTTP/HTTPS) URL to "
                                          "load the image from."),
                              widget=forms.TextInput(attrs=image_url_attrs),
                              required=False)
    image_attrs = {
        'class': 'switched',
        'data-switch-on': 'source',
        'data-source-file': _('Image File'),
        'ng-model': 'ctrl.imageFile',
        'ng-change': 'ctrl.selectImageFormat(ctrl.imageFile.name)',
        'image-file-on-change': None
    }
    image_file = forms.FileField(label=_("Image File"),
                                 help_text=_("A local image to upload."),
                                 widget=forms.FileInput(attrs=image_attrs),
                                 required=False)
    kernel = forms.ChoiceField(
        label=_('Kernel'),
        required=False,
        widget=forms.SelectWidget(
            transform=lambda x: "%s (%s)" % (
                x.name, defaultfilters.filesizeformat(x.size))))
    ramdisk = forms.ChoiceField(
        label=_('Ramdisk'),
        required=False,
        widget=forms.SelectWidget(
            transform=lambda x: "%s (%s)" % (
                x.name, defaultfilters.filesizeformat(x.size))))
    disk_format = forms.ChoiceField(label=_('Format'),
                                    choices=[],
                                    widget=forms.Select(attrs={
                                        'class': 'switchable',
                                        'ng-model': 'ctrl.diskFormat'}))
    architecture = forms.CharField(max_length=255, label=_("Architecture"),
                                   required=False)
    minimum_disk = forms.IntegerField(
        label=_("Minimum Disk (GB)"),
        min_value=0,
        help_text=_('The minimum disk size required to boot the image. '
                    'If unspecified, this value defaults to 0 (no minimum).'),
        required=False)
    minimum_ram = forms.IntegerField(
        label=_("Minimum RAM (MB)"),
        min_value=0,
        help_text=_('The minimum memory size required to boot the image. '
                    'If unspecified, this value defaults to 0 (no minimum).'),
        required=False)
    is_copying = forms.BooleanField(
        label=_("Copy Data"), initial=True, required=False,
        help_text=_('Specify this option to copy image data to the image '
                    'service. If unspecified, image data will be used in its '
                    'current location.'),
        widget=forms.CheckboxInput(attrs={
            'class': 'switched',
            'data-source-url': _('Image Location'),
            'data-switch-on': 'source'}))
    is_public = forms.BooleanField(label=_("Public"), required=False)
    protected = forms.BooleanField(label=_("Protected"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateImageForm, self).__init__(request, *args, **kwargs)

        if (not settings.HORIZON_IMAGES_ALLOW_UPLOAD or
                not policy.check((("image", "upload_image"),), request)):
            self._hide_file_source_type()
        if not policy.check((("image", "set_image_location"),), request):
            self._hide_url_source_type()
        if not policy.check((("image", "publicize_image"),), request):
            self._hide_is_public()

        self.fields['disk_format'].choices = IMAGE_FORMAT_CHOICES

        try:
            kernel_images = api.glance.image_list_detailed(
                request, filters={'disk_format': 'aki'})[0]
        except Exception:
            kernel_images = []
            msg = _('Unable to retrieve image list.')
            messages.error(request, msg)

        if kernel_images:
            choices = [('', _("Choose an image"))]
            for image in kernel_images:
                choices.append((image.id, image))
            self.fields['kernel'].choices = choices
        else:
            del self.fields['kernel']

        try:
            ramdisk_images = api.glance.image_list_detailed(
                request, filters={'disk_format': 'ari'})[0]
        except Exception:
            ramdisk_images = []
            msg = _('Unable to retrieve image list.')
            messages.error(request, msg)

        if ramdisk_images:
            choices = [('', _("Choose an image"))]
            for image in ramdisk_images:
                choices.append((image.id, image))
            self.fields['ramdisk'].choices = choices
        else:
            del self.fields['ramdisk']

    def _hide_file_source_type(self):
        self.fields['image_file'].widget = HiddenInput()
        source_type = self.fields['source_type']
        source_type.choices = [choice for choice in source_type.choices
                               if choice[0] != 'file']
        if len(source_type.choices) == 1:
            source_type.widget = HiddenInput()

    def _hide_url_source_type(self):
        self.fields['image_url'].widget = HiddenInput()
        source_type = self.fields['source_type']
        source_type.choices = [choice for choice in source_type.choices
                               if choice[0] != 'url']
        if len(source_type.choices) == 1:
            source_type.widget = HiddenInput()

    def _hide_is_public(self):
        self.fields['is_public'].widget = HiddenInput()
        self.fields['is_public'].initial = False

    def clean(self):
        data = super(CreateImageForm, self).clean()

        # The image_file key can be missing based on particular upload
        # conditions. Code defensively for it here...
        image_file = data.get('image_file', None)
        image_url = data.get('image_url', None)

        if not image_url and not image_file:
            raise ValidationError(
                _("A image or external image location must be specified."))
        elif image_url and image_file:
            raise ValidationError(
                _("Can not specify both image and external image location."))
        else:
            return data

    def handle(self, request, data):
        meta = create_image_metadata(data)

        # Add image source file or URL to metadata
        if (settings.HORIZON_IMAGES_ALLOW_UPLOAD and
                policy.check((("image", "upload_image"),), request) and
                data.get('image_file', None)):
            meta['data'] = self.files['image_file']
        elif data['is_copying']:
            meta['copy_from'] = data['image_url']
        else:
            meta['location'] = data['image_url']

        try:
            image = api.glance.image_create(request, **meta)
            messages.info(request,
                          _('Your image %s has been queued for creation.') %
                          meta['name'])
            return image
        except Exception as e:
            msg = _('Unable to create new image')
            # TODO(nikunj2512): Fix this once it is fixed in glance client
            if hasattr(e, 'code') and e.code == 400:
                if "Invalid disk format" in e.details:
                    msg = _('Unable to create new image: Invalid disk format '
                            '%s for image.') % meta['disk_format']
                elif "Image name too long" in e.details:
                    msg = _('Unable to create new image: Image name too long.')
                elif "not supported" in e.details:
                    msg = _('Unable to create new image: URL scheme not '
                            'supported.')

            exceptions.handle(request, msg)

            return False


class UpdateImageForm(forms.SelfHandlingForm):
    image_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=255, label=_("Name"))
    description = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_("Description"),
        required=False)
    kernel = forms.CharField(
        max_length=36,
        label=_("Kernel ID"),
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    )
    ramdisk = forms.CharField(
        max_length=36,
        label=_("Ramdisk ID"),
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    )
    architecture = forms.CharField(
        label=_("Architecture"),
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    )
    disk_format = forms.ChoiceField(
        label=_("Format"),
    )
    minimum_disk = forms.IntegerField(label=_("Minimum Disk (GB)"),
                                      min_value=0,
                                      help_text=_('The minimum disk size'
                                                  ' required to boot the'
                                                  ' image. If unspecified,'
                                                  ' this value defaults to'
                                                  ' 0 (no minimum).'),
                                      required=False)
    minimum_ram = forms.IntegerField(label=_("Minimum RAM (MB)"),
                                     min_value=0,
                                     help_text=_('The minimum memory size'
                                                 ' required to boot the'
                                                 ' image. If unspecified,'
                                                 ' this value defaults to'
                                                 ' 0 (no minimum).'),
                                     required=False)
    public = forms.BooleanField(label=_("Public"), required=False)
    protected = forms.BooleanField(label=_("Protected"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateImageForm, self).__init__(request, *args, **kwargs)
        self.fields['disk_format'].choices = [(value, name) for value,
                                              name in IMAGE_FORMAT_CHOICES
                                              if value]
        if not policy.check((("image", "publicize_image"),), request):
            self.fields['public'].widget = forms.CheckboxInput(
                attrs={'readonly': 'readonly', 'disabled': 'disabled'})
            self.fields['public'].help_text = _(
                'Non admin users are not allowed to make images public.')

    def handle(self, request, data):
        image_id = data['image_id']
        error_updating = _('Unable to update image "%s".')
        meta = create_image_metadata(data)
        # Ensure we do not delete properties that have already been
        # set on an image.
        meta['purge_props'] = False

        try:
            image = api.glance.image_update(request, image_id, **meta)
            messages.success(request, _('Image was successfully updated.'))
            return image
        except Exception:
            exceptions.handle(request, error_updating % image_id)
