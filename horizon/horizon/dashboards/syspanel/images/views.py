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
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from glance.common import exception as glance_exception

from horizon import api
from horizon.dashboards.syspanel.images.forms import (DeleteImage,
        ToggleImage, UpdateImageForm)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    for f in (DeleteImage, ToggleImage):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    delete_form = DeleteImage()
    toggle_form = ToggleImage()

    images = []
    try:
        images = api.image_list_detailed(request)
        if not images:
            messages.info(request, _("There are currently no images."))
    except glance_exception.ClientConnectionError, e:
        LOG.exception("Error connecting to glance")
        messages.error(request,
                       _("Error connecting to glance: %s") % e.message)
    except glance_exception.Error, e:
        LOG.exception("Error retrieving image list")
        messages.error(request,
                       _("Error retrieving image list: %s") % e.message)

    return shortcuts.render(request,
                            'syspanel/images/index.html', {
                                'delete_form': delete_form,
                                'toggle_form': toggle_form,
                                'images': images})


@login_required
def update(request, image_id):
    try:
        image = api.image_get(request, image_id)
    except glance_exception.ClientConnectionError, e:
        LOG.exception("Error connecting to glance")
        messages.error(request,
                       _("Error connecting to glance: %s") % e.message)
    except glance_exception.Error, e:
        LOG.exception('Error retrieving image with id "%s"' % image_id)
        messages.error(request,
                       _("Error retrieving image %(image)s: %(msg)s") %
                       {"image": image_id, "msg": e.message})

    if request.method == "POST":
        form = UpdateImageForm(request.POST)
        if form.is_valid():
            image_form = form.clean()
            metadata = {
                'is_public': True,
                'disk_format': image_form['disk_format'],
                'container_format': image_form['container_format'],
                'name': image_form['name'],
            }
            try:
                # TODO add public flag to properties
                metadata['properties'] = {}
                if image_form['kernel']:
                    metadata['properties']['kernel_id'] = image_form['kernel']
                if image_form['ramdisk']:
                    metadata['properties']['ramdisk_id'] = \
                            image_form['ramdisk']
                if image_form['architecture']:
                    metadata['properties']['architecture'] = \
                            image_form['architecture']
                api.image_update(request, image_id, metadata)
                messages.success(request, _("Image was successfully updated."))
            except glance_exception.ClientConnectionError, e:
                LOG.exception("Error connecting to glance")
                messages.error(request,
                               _("Error connecting to glance: %s") % e.message)
            except glance_exception.Error, e:
                LOG.exception('Error updating image with id "%s"' % image_id)
                messages.error(request,
                               _("Error updating image: %s") % e.message)
            except:
                LOG.exception('Unspecified Exception in image update')
                messages.error(request,
                            _("Image could not be updated, please try again."))
            return shortcuts.redirect('syspanel_images_update', image_id)
        else:
            LOG.exception('Image "%s" failed to update' % image['name'])
            messages.error(request,
                           _("Image could not be uploaded, please try agian."))
            form = UpdateImageForm(request.POST)
            return shortcuts.render(request,
                                    'syspanel/images/update.html', {
                                        'image': image,
                                        'form': form})
    else:
        form = UpdateImageForm(initial={
                'name': image.get('name', ''),
                'kernel': image['properties'].get('kernel_id', ''),
                'ramdisk': image['properties'].get('ramdisk_id', ''),
                'is_public': image.get('is_public', ''),
                'location': image.get('location', ''),
                'state': image['properties'].get('image_state', ''),
                'architecture': image['properties'].get('architecture', ''),
                'project_id': image['properties'].get('project_id', ''),
                'container_format': image.get('container_format', ''),
                'disk_format': image.get('disk_format', ''),
            })

        return shortcuts.render(request,
                                'syspanel/images/update.html', {
                                    'image': image,
                                    'form': form})


@login_required
def upload(request):
    if request.method == "POST":
        form = UploadImageForm(request.POST)
        if form.is_valid():
            image = form.clean()
            metadata = {'is_public': image['is_public'],
                        'disk_format': 'ami',
                        'container_format': 'ami',
                        'name': image['name']}
            try:
                messages.success(request,
                                 _("Image was successfully uploaded."))
            except:
                # TODO add better error management
                messages.error(request,
                        _("Image could not be uploaded, please try again."))

            try:
                api.image_create(request, metadata, image['image_file'])
            except glance_exception.ClientConnectionError, e:
                LOG.exception('Error connecting to glance while trying to'
                              'upload image')
                messages.error(request,
                               _("Error connecting to glance: %s") % e.message)
            except glance_exception.Error, e:
                LOG.exception('Glance exception while uploading image')
                messages.error(request,
                               _("Error adding image: %s") % e.message)
        else:
            LOG.exception('Image "%s" failed to upload' % image['name'])
            messages.error(request,
                           _("Image could not be uploaded, please try agian."))
            form = UploadImageForm(request.POST)
            return shortcuts.render(request,
                                    'django_nova_syspanel/images/upload.html',
                                    {'form': form})

        return shortcuts.redirect('syspanel_images')
    else:
        form = UploadImageForm()
        return shortcuts.render(request,
                                'django_nova_syspanel/images/upload.html',
                                {'form': form})
