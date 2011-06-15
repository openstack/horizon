# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
import re

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack.nova import exceptions
from django_openstack.nova import forms as nova_forms
#from django_openstack.nova import shortcuts
from django_openstack.nova.exceptions import handle_nova_error
from django import shortcuts

from django_openstack import api
from openstackx.api import exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.nova')


def _image_lists(images, tenant_id):
    def image_is_project(i):
        return i['properties']['project_id'] == tenant_id

    def image_is_admin(i):
        return i['properties']['project_id'] in ['admin']

    def image_is_community(i):
        return (not image_is_admin(i)) and (not image_is_project(i))

    return {'Project Images': filter(image_is_project, images),
            '%s Images' % settings.SITE_BRANDING: filter(image_is_admin,
                                                         images),
            'Community Images': filter(image_is_community, images)}


@login_required
@handle_nova_error
def index(request, tenant_id):
    tenant = api.get_tenant(request, request.user.tenant)
    logging.info('TENANT: %s', tenant)
    #project = shortcuts.get_project_or_404(request, project_id)
    images = api.glance_api(request).get_images_detailed()
    logging.info('IMAGES: %s', images)

    return render_to_response('django_openstack/nova/images/index.html', {
        'form': nova_forms.LaunchForm(),
        #'region': project.region,
        'tenant': tenant,
        'image_lists': _image_lists(images, request.user.tenant),
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def launch(request, tenant_id, image_id):
    def flavorlist():
        try:
            fl = api.extras_api(request).flavors.list()

            # TODO add vcpu count to flavors
            sel = [(f.id, '%s (%svcpu / %sGB Disk / %sMB Ram )' %
                   (f.name, f.vcpus, f.disk, f.ram)) for f in fl]
            return sorted(sel)
        except:
            return [(1, 'm1.tiny')]

    image = api.compute_api(request).images.get(image_id)
    tenant = api.get_tenant(request, request.user.tenant)

    if request.method == 'POST':
        form = nova_forms.LaunchForm(request.POST,
                                     initial={'flavorlist': flavorlist()})
        if form.is_valid():
            userdata = form.clean()
            try:
                image = api.compute_api(request).images.get(image_id)
                fl = api.compute_api(request).flavors.get(userdata['flavor'])
                api.compute_api(request).servers.create(userdata['name'],
                                                        image,
                                                        fl)
                messages.success(request, "Instance was successfully\
                                           launched.")
                return shortcuts.redirect('nova_instances', tenant_id=tenant.id)
            except api_exceptions.ApiException, e:
                messages.error(request,
                           'Unable to launch instance: %s' % e.message)

    form = nova_forms.LaunchForm(initial={'image_id': image_id,
                                          'flavorlist': flavorlist()})

    return render_to_response('django_openstack/nova/images/launch.html', {
        'tenant': tenant,
        'image': image,
        'form': form,
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def detail(request, tenant_id, image_id):
    image = api.compute_api(request).images.get(image_id)
    tenant = api.get_tenant(request, request.user.tenant)
    images = api.glance_api(request).get_images_detailed()

    if not image:
        raise http.Http404()
    return render_to_response('django_openstack/nova/images/index.html', {
        'form': nova_forms.LaunchForm(),
        #'region': project.region,
        'tenant': tenant,
        'image_lists': _image_lists(images, tenant_id),
        'image': image,
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def remove(request, project_id, image_id):
    project = shortcuts.get_project_or_404(request, project_id)

    if request.method == 'POST':
        try:
            project.deregister_image(image_id)
        except exceptions.NovaApiError, e:
            messages.error(request,
                           _('Unable to deregister image: %s') % e.message)
            LOG.error('Unable to deregister image "%s" from project "%s".'
                      ' Exception message: "%s"' %
                      (image_id, project_id, e.message))
        else:
            messages.success(request,
                            _('Image %s has been successfully deregistered.') %
                             image_id)
            LOG.info('Image "%s" deregistered from project "%s"' %
                     (image_id, project_id))

    return shortcuts.redirect('nova_images', project_id)


@login_required
@handle_nova_error
def privacy(request, project_id, image_id):
    project = shortcuts.get_project_or_404(request, project_id)

    if request.method == 'POST':
        ami = project.get_image(image_id)

        if ami.is_public:
            try:
                project.modify_image_attribute(image_id,
                                               attribute='launchPermission',
                                               operation='remove')
                LOG.info('Image "%s" on project "%s" set to private' %
                         (image_id, project_id))
            except exceptions.NovaApiError, e:
                messages.error(request,
                               _('Unable to make image private: %s') %
                                e.message)
                LOG.error('Unable to make image "%s" private on project "%s".'
                          ' Exception text: "%s"' %
                          (image_id, project_id, e.message))
        else:
            try:
                project.modify_image_attribute(image_id,
                                               attribute='launchPermission',
                                               operation='add')
                LOG.info('Image "%s" on project "%s" set to public' %
                         (image_id, project_id))
            except exceptions.NovaApiError, e:
                messages.error(request,
                               _('Unable to make image public: %s') %
                               e.message)
                LOG.error('Unable to make image "%s" public on project "%s".'
                          ' Exception text: "%s"' %
                          (image_id, project_id, e.message))

    return shortcuts.redirect('nova_images_detail', project_id, image_id)


@login_required
@handle_nova_error
def update(request, project_id, image_id):
    project = shortcuts.get_project_or_404(request, project_id)
    ami = project.get_image(image_id)

    if request.method == 'POST':
        form = nova_forms.UpdateImageForm(ami, request.POST)
        if form.is_valid():
            try:
                project.update_image(image_id,
                                     form.cleaned_data['nickname'],
                                     form.cleaned_data['description'])
                LOG.info('Image "%s" on project "%s" updated' %
                         (image_id, project_id))
            except exceptions.NovaApiError, e:
                messages.error(request,
                               _('Unable to update image: %s') % e.message)
            else:
                messages.success(request,
                                 _('Image %s has been updated.') % image_id)

            return shortcuts.redirect('nova_images_detail', project_id, image_id)

        # TODO(devcamcar): This needs to be cleaned up. Can make
        # one of the render_to_response blocks go away.
        else:
            form = nova_forms.UpdateImageForm(ami)
            return render_to_response('django_openstack/images/edit.html', {
                'form': form,
                'region': project.region,
                'project': project,
                'ami': ami,
            }, context_instance=template.RequestContext(request))
    else:
        form = nova_forms.UpdateImageForm(ami)
        return render_to_response('django_openstack/nova/images/edit.html', {
            'form': form,
            'region': project.region,
            'project': project,
            'ami': ami,
        }, context_instance=template.RequestContext(request))
