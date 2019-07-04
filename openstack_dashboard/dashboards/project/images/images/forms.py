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
from django.forms import ValidationError
from django.forms.widgets import HiddenInput
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _
import six

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import policy


IMAGE_BACKEND_SETTINGS = settings.OPENSTACK_IMAGE_BACKEND
IMAGE_FORMAT_CHOICES = IMAGE_BACKEND_SETTINGS['image_formats']


class ImageURLField(forms.URLField):
    default_validators = [validators.URLValidator(schemes=["http", "https"])]


if api.glance.get_image_upload_mode() == 'direct':
    FileField = forms.ExternalFileField
    CreateParent = six.with_metaclass(forms.ExternalUploadMeta,
                                      forms.SelfHandlingForm)
else:
    FileField = forms.FileField
    CreateParent = forms.SelfHandlingForm


class CreateImageForm(CreateParent):
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
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switchable',
            'data-slug': 'source'}))
    image_url_attrs = {
        'class': 'switched',
        'data-switch-on': 'source',
        'data-source-url': _('Image Location'),
        'ng-model': 'ctrl.copyFrom',
        'ng-change': 'ctrl.selectImageFormat(ctrl.copyFrom)',
        'placeholder': 'http://example.com/image.img'
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
    image_file = FileField(label=_("Image File"),
                           help_text=_("A local image to upload."),
                           widget=forms.FileInput(attrs=image_attrs),
                           required=False)
    kernel = forms.ChoiceField(
        label=_('Kernel'),
        required=False,
        widget=forms.ThemableSelectWidget(
            transform=lambda x: "%s (%s)" % (
                x.name, defaultfilters.filesizeformat(x.size))))
    ramdisk = forms.ChoiceField(
        label=_('Ramdisk'),
        required=False,
        widget=forms.ThemableSelectWidget(
            transform=lambda x: "%s (%s)" % (
                x.name, defaultfilters.filesizeformat(x.size))))
    disk_format = forms.ChoiceField(label=_('Format'),
                                    choices=[],
                                    widget=forms.ThemableSelectWidget(attrs={
                                        'class': 'switchable',
                                        'ng-model': 'ctrl.diskFormat'}))
    architecture = forms.CharField(
        max_length=255,
        label=_("Architecture"),
        help_text=_('CPU architecture of the image.'),
        required=False)
    min_disk = forms.IntegerField(
        label=_("Minimum Disk (GB)"),
        min_value=0,
        help_text=_('The minimum disk size required to boot the image. '
                    'If unspecified, this value defaults to 0 (no minimum).'),
        required=False)
    min_ram = forms.IntegerField(
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
    is_public = forms.BooleanField(
        label=_("Public"),
        help_text=_('Make the image visible across projects.'),
        required=False)
    protected = forms.BooleanField(
        label=_("Protected"),
        help_text=_('Prevent the deletion of the image.'),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateImageForm, self).__init__(request, *args, **kwargs)

        if (api.glance.get_image_upload_mode() == 'off' or
                not policy.check((("image", "upload_image"),), request)):
            self._hide_file_source_type()
        if not policy.check((("image", "set_image_location"),), request):
            self._hide_url_source_type()

        # GlanceV2 feature removals
        if api.glance.VERSIONS.active >= 2:
            # NOTE: GlanceV2 doesn't support copy-from feature, sorry!
            self._hide_is_copying()
            if not settings.IMAGES_ALLOW_LOCATION:
                self._hide_url_source_type()
                if (api.glance.get_image_upload_mode() == 'off' or not
                        policy.check((("image", "upload_image"),), request)):
                    # Neither setting a location nor uploading image data is
                    # allowed, so throw an error.
                    msg = _('The current Horizon settings indicate no valid '
                            'image creation methods are available. Providing '
                            'an image location and/or uploading from the '
                            'local file system must be allowed to support '
                            'image creation.')
                    messages.error(request, msg)
                    raise ValidationError(msg)
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

    def _hide_is_copying(self):
        self.fields['is_copying'].widget = HiddenInput()
        self.fields['is_copying'].initial = False

    def clean(self):
        data = super(CreateImageForm, self).clean()

        # The image_file key can be missing based on particular upload
        # conditions. Code defensively for it here...
        source_type = data.get('source_type', None)
        image_file = data.get('image_file', None)
        image_url = data.get('image_url', None)

        if not image_url and not image_file:
            msg = _("An image file or an external location must be specified.")
            if source_type == 'file':
                raise ValidationError({'image_file': [msg, ]})
            else:
                raise ValidationError({'image_url': [msg, ]})
        else:
            return data

    def handle(self, request, data):
        meta = api.glance.create_image_metadata(data)

        # Add image source file or URL to metadata
        if (api.glance.get_image_upload_mode() != 'off' and
                policy.check((("image", "upload_image"),), request) and
                data.get('image_file', None)):
            meta['data'] = data['image_file']
        elif data.get('is_copying'):
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
    disk_format = forms.ThemableChoiceField(
        label=_("Format"),
    )
    min_disk = forms.IntegerField(
        label=_("Minimum Disk (GB)"),
        min_value=0,
        help_text=_('The minimum disk size required to boot the image. '
                    'If unspecified, this value defaults to 0 (no minimum).'),
        required=False)
    min_ram = forms.IntegerField(
        label=_("Minimum RAM (MB)"),
        min_value=0,
        help_text=_('The minimum memory size required to boot the image. '
                    'If unspecified, this value defaults to 0 (no minimum).'),
        required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False)
    protected = forms.BooleanField(label=_("Protected"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateImageForm, self).__init__(request, *args, **kwargs)
        self.fields['disk_format'].choices = [(value, name) for value,
                                              name in IMAGE_FORMAT_CHOICES
                                              if value]
        if not policy.check((("image", "publicize_image"),), request):
            self.fields['is_public'].widget = forms.CheckboxInput(
                attrs={'readonly': 'readonly', 'disabled': 'disabled'})
            self.fields['is_public'].help_text = _(
                'Non admin users are not allowed to make images public.')

    def handle(self, request, data):
        image_id = data['image_id']
        error_updating = _('Unable to update image "%s".')
        meta = api.glance.create_image_metadata(data)

        try:
            image = api.glance.image_update(request, image_id, **meta)
            messages.success(request, _('Image was successfully updated.'))
            return image
        except Exception:
            exceptions.handle(request, error_updating % image_id)
