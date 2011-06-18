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

import re

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack import log as logging
from django_openstack.nova import exceptions
from django_openstack.nova import forms
from django_openstack.nova import shortcuts
from django_openstack.nova.exceptions import handle_nova_error


LOG = logging.getLogger('django_openstack.nova')


def _image_lists(images, project_id):
    def image_is_project(i):
        return i.ownerId == project_id

    def image_is_admin(i):
        return i.ownerId in ['admin']

    def image_is_community(i):
        return (not image_is_admin(i)) and (not image_is_project(i))

    return {'Project Images': filter(image_is_project, images),
            '%s Images' % settings.SITE_BRANDING: filter(image_is_admin,
                                                         images),
            'Community Images': filter(image_is_community, images)}


@login_required
@handle_nova_error
def index(request, project_id):
    project = shortcuts.get_project_or_404(request, project_id)
    images = project.get_images()

    return render_to_response('django_openstack/nova/images/index.html', {
        'form': forms.LaunchInstanceForm(project),
        'region': project.region,
        'project': project,
        'image_lists': _image_lists(images, project_id),
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def launch(request, project_id, image_id):
    project = shortcuts.get_project_or_404(request, project_id)

    if request.method == 'POST':
        form = forms.LaunchInstanceForm(project, request.POST)
        if form.is_valid():
            try:
                reservation = project.run_instances(image_id,
                    form.cleaned_data['size'],
                    form.cleaned_data['count'],
                    key_name=form.cleaned_data['key_name'],
                    display_name=form.cleaned_data['display_name'],
                    user_data=re.sub('\r\n', '\n',
                       form.cleaned_data['user_data']))
            except exceptions.NovaApiError, e:
                messages.error(request,
                               _('Unable to launch: %s') % e.message)
                LOG.error('User "%s" unable to launch image "%s" '
                          ' on project "%s". Exception message: "%s"' %
                          (str(request.user), image_id, project_id, e.message))
            except exceptions.NovaUnauthorizedError, e:
                messages.error(request, 'Permission Denied')
                LOG.error('User "%s" permission denied creating image "%s"'
                          ' on project "%s"' %
                          (str(request.user), image_id, project_id))
            else:
                for instance in reservation.instances:
                    messages.success(request,
                                     _('Instance %s launched.') % instance.id)
                LOG.info('%d instances of "%s" launched by "%s" on "%s"' %
                         (len(reservation.instances), image_id,
                          str(request.user), project_id))
                LOG.debug('"%s" instance ids: "%s"' %
                          (image_id,
                           ",".join(str(instance.id)
                                    for instance in reservation.instances)))
            return redirect('nova_instances', project_id)
    else:
        form = forms.LaunchInstanceForm(project)

    ami = project.get_image(image_id)

    return render_to_response('django_openstack/nova/images/launch.html', {
        'form': form,
        'region': project.region,
        'project': project,
        'ami': ami,
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def detail(request, project_id, image_id):
    project = shortcuts.get_project_or_404(request, project_id)
    images = project.get_images()

    ami = project.get_image(image_id)

    if not ami:
        raise http.Http404()
    return render_to_response('django_openstack/nova/images/index.html', {
        'form': forms.LaunchInstanceForm(project),
        'region': project.region,
        'project': project,
        'image_lists': _image_lists(images, project_id),
        'ami': ami,
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

    return redirect('nova_images', project_id)


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

    return redirect('nova_images_detail', project_id, image_id)


@login_required
@handle_nova_error
def update(request, project_id, image_id):
    project = shortcuts.get_project_or_404(request, project_id)
    ami = project.get_image(image_id)

    if request.method == 'POST':
        form = forms.UpdateImageForm(ami, request.POST)
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

            return redirect('nova_images_detail', project_id, image_id)

        # TODO(devcamcar): This needs to be cleaned up. Can make
        # one of the render_to_response blocks go away.
        else:
            form = forms.UpdateImageForm(ami)
            return render_to_response('django_openstack/images/edit.html', {
                'form': form,
                'region': project.region,
                'project': project,
                'ami': ami,
            }, context_instance=template.RequestContext(request))
    else:
        form = forms.UpdateImageForm(ami)
        return render_to_response('django_openstack/nova/images/edit.html', {
            'form': form,
            'region': project.region,
            'project': project,
            'ami': ami,
        }, context_instance=template.RequestContext(request))
