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
Views for managing Nova images.
"""

import logging

from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from glance.common import exception as glance_exception
from novaclient import exceptions as novaclient_exceptions
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon.dashboards.nova.images_and_snapshots.images.forms import \
                                    (UpdateImageForm, LaunchForm, DeleteImage)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    for f in (DeleteImage, ):
        unused, handled = f.maybe_handle(request)
        if handled:
            return handled
    all_images = []
    try:
        all_images = api.image_list_detailed(request)
        if not all_images:
            messages.info(request, _("There are currently no images."))
    except glance_exception.ClientConnectionError, e:
        LOG.exception("Error connecting to glance")
        messages.error(request, _("Error connecting to glance: %s") % str(e))
    except glance_exception.GlanceException, e:
        LOG.exception("Error retrieving image list")
        messages.error(request, _("Error retrieving image list: %s") % str(e))
    except Exception, e:
        msg = _("Unable to retrieve image info from glance: %s") % str(e)
        LOG.exception(msg)
        messages.error(request, msg)

    images = [im for im in all_images
              if im['container_format'] not in ['aki', 'ari']]

    context = {'delete_form': DeleteImage(), 'images': images}

    return shortcuts.render(request,
                            'nova/images_and_snapshots/images/index.html', {
                                'delete_form': DeleteImage(),
                                'quotas': quotas,
                                'images': images})


@login_required
def launch(request, image_id):

    def flavorlist():
        try:
            fl = api.flavor_list(request)

            # TODO add vcpu count to flavors
            sel = [(f.id, '%s (%svcpu / %sGB Disk / %sMB Ram )' %
                   (f.name, f.vcpus, f.disk, f.ram)) for f in fl]
            return sorted(sel)
        except api_exceptions.ApiException:
            LOG.exception('Unable to retrieve list of instance types')
            return [(1, 'm1.tiny')]

    def keynamelist():
        try:
            fl = api.keypair_list(request)
            sel = [(f.name, f.name) for f in fl]
            return sel
        except api_exceptions.ApiException:
            LOG.exception('Unable to retrieve list of keypairs')
            return []

    def securitygrouplist():
        try:
            fl = api.security_group_list(request)
            sel = [(f.name, f.name) for f in fl]
            return sel
        except novaclient_exceptions.ClientException, e:
            LOG.exception('Unable to retrieve list of security groups')
            return []

    tenant_id = request.user.tenant_id
    # TODO(mgius): Any reason why these can't be after the launchform logic?
    # If The form is valid, we've just wasted these two api calls
    image = api.image_get_meta(request, image_id)
    quotas = api.tenant_quota_get(request, request.user.tenant_id)
    try:
        quotas.ram = int(quotas.ram)
    except Exception, e:
        messages.error(request,
                _('Error parsing quota  for %(image)s: %(msg)s') %
                {"image": image_id, "msg": e.message})
        return shortcuts.redirect(
                        'horizon:nova:instances_and_volumes:instances:index')

    form, handled = LaunchForm.maybe_handle(
            request, initial={'flavorlist': flavorlist(),
                              'keynamelist': keynamelist(),
                              'securitygrouplist': securitygrouplist(),
                              'image_id': image_id,
                              'tenant_id': tenant_id})
    if handled:
        return handled

    return shortcuts.render(request,
                            'nova/images_and_snapshots/images/launch.html', {
                                'image': image,
                                'form': form,
                                'quotas': quotas})


@login_required
def update(request, image_id):
    try:
        image = api.image_get_meta(request, image_id)
    except glance_exception.ClientConnectionError, e:
        LOG.exception("Error connecting to glance")
        messages.error(request, _("Error connecting to glance: %s")
                                 % e.message)
    except glance_exception.Error, e:
        LOG.exception('Error retrieving image with id "%s"' % image_id)
        messages.error(request,
                _("Error retrieving image %(image)s: %(msg)s")
                % {"image": image_id, "msg": e.message})

    form, handled = UpdateImageForm().maybe_handle(request, initial={
                 'image_id': image_id,
                 'name': image.get('name', ''),
                 'kernel': image['properties'].get('kernel_id', ''),
                 'ramdisk': image['properties'].get('ramdisk_id', ''),
                 'architecture': image['properties'].get('architecture', ''),
                 'container_format': image.get('container_format', ''),
                 'disk_format': image.get('disk_format', ''), })
    if handled:
        return handled

    context = {'form': form, "image": image}

    return shortcuts.render(request, 'nova/images_and_snapshots/images/update.html', context)
