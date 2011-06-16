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
Views for managing Nova instances.
"""

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack import log as logging
from django_openstack.nova import exceptions
from django_openstack.nova import forms as nova_forms
from django_openstack.nova import shortcuts
from django_openstack.nova.exceptions import handle_nova_error

import boto.ec2.ec2object


LOG = logging.getLogger('django_openstack.nova')


@login_required
@handle_nova_error
def index(request, project_id):
    project = shortcuts.get_project_or_404(request, project_id)
    instances = sorted(project.get_instances(),
                       key=lambda k: k.public_dns_name)

    return render_to_response('django_openstack/nova/instances/index.html', {
        'region': project.region,
        'project': project,
        'instances': instances,
        'detail': False,
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def detail(request, project_id, instance_id):
    project = shortcuts.get_project_or_404(request, project_id)
    instance = project.get_instance(instance_id)
    instances = sorted(project.get_instances(),
                       key=lambda k: k.public_dns_name)

    if not instance:
        raise http.Http404()

    return render_to_response('django_openstack/nova/instances/index.html', {
        'region': project.region,
        'project': project,
        'selected_instance': instance,
        'instances': instances,
        'update_form': nova_forms.UpdateInstanceForm(instance),
        'enable_vnc': settings.ENABLE_VNC,
        'detail': True,
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def performance(request, project_id, instance_id):
    project = shortcuts.get_project_or_404(request, project_id)
    instance = project.get_instance(instance_id)

    if not instance:
        raise http.Http404()

    return render_to_response(
        'django_openstack/nova/instances/performance.html',
        {'region': project.region,
         'project': project,
         'instance': instance,
         'update_form': nova_forms.UpdateInstanceForm(instance)},
        context_instance=template.RequestContext(request))


# TODO(devcamcar): Wrap this in an @ajax decorator.
def refresh(request, project_id):
    # TODO(devcamcar): This logic belongs in decorator.
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    project = shortcuts.get_project_or_404(request, project_id)
    instances = sorted(project.get_instances(),
                       key=lambda k: k.public_dns_name)

    return render_to_response(
        'django_openstack/nova/instances/_instances_list.html',
        {'project': project,
         'instances': instances},
        context_instance=template.RequestContext(request))


@handle_nova_error
def refresh_detail(request, project_id, instance_id):
    # TODO(devcamcar): This logic belongs in decorator.
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    project = shortcuts.get_project_or_404(request, project_id)
    instance = project.get_instance(instance_id)
    instances = sorted(project.get_instances(),
                       key=lambda k: k.public_dns_name)

    return render_to_response(
        'django_openstack/nova/instances/_instances_list.html',
        {'project': project,
         'selected_instance': instance,
         'instances': instances},
        context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def terminate(request, project_id):
    project = shortcuts.get_project_or_404(request, project_id)

    if request.method == 'POST':
        instance_id = request.POST['instance_id']

        try:
            project.terminate_instance(instance_id)
        except exceptions.NovaApiError, e:
            messages.error(request,
                           _('Unable to terminate %(inst)s: %(msg)s') %
                            {'inst': instance_id, 'msg': e.message})
            LOG.error('Unable to terminate instance "%s" on project "%s".'
                      ' Exception:"%s"' % (instance_id, project_id, e.message))
        except exceptions.NovaUnauthorizedError, e:
            messages.error(request, 'Permission Denied')
            LOG.error('User "%s" denied permission to terminate instance'
                      ' "%s" on project "%s"' %
                      (str(request.user), instance_id, project_id))
        else:
            messages.success(request,
                             _('Instance %(inst)s has been terminated.') %
                              {'inst': instance_id})
            LOG.info('Instance "%s" terminated on project "%s"' %
                     (instance_id, project_id))

    return redirect('nova_instances', project_id)


@login_required
@handle_nova_error
def console(request, project_id, instance_id):
    project = shortcuts.get_project_or_404(request, project_id)
    conn = project.get_openstack_connection()
    console = conn.get_console_output(instance_id)
    response = http.HttpResponse(mimetype='text/plain')
    response.write(console.output)
    response.flush()

    return response


@login_required
@handle_nova_error
def vnc(request, project_id, instance_id):
    project = shortcuts.get_project_or_404(request, project_id)
    conn = project.get_openstack_connection()
    params = {'InstanceId': instance_id}
    vnc = conn.get_object('GetVncConsole',
                          params,
                          boto.ec2.ec2object.EC2Object)
    return http.HttpResponseRedirect(vnc.url)


@login_required
@handle_nova_error
def graph(request, project_id, instance_id, graph_name):
    project = shortcuts.get_project_or_404(request, project_id)
    graph = project.get_instance_graph(instance_id, graph_name)

    if graph is None:
        raise http.Http404()

    response = http.HttpResponse(mimetype='image/png')
    response.write(graph)

    return response


@login_required
@handle_nova_error
def update(request, project_id, instance_id):
    project = shortcuts.get_project_or_404(request, project_id)
    instance = project.get_instance(instance_id)

    if not instance:
        raise http.Http404()

    if request.method == 'POST':
        form = nova_forms.UpdateInstanceForm(instance, request.POST)
        if form.is_valid():
            try:
                project.update_instance(instance_id, form.cleaned_data)
            except exceptions.NovaApiError, e:
                messages.error(request,
                          _('Unable to update instance %(inst)s: %(msg)s') %
                           {'inst': instance_id, 'msg': e.message})
                LOG.error('Unable to update instance "%s" on project "%s".'
                          ' Exception message: "%s"' %
                          (instance_id, project_id, e.message))
            except exceptions.NovaUnauthorizedError, e:
                messages.error(request, 'Permission Denied')
                LOG.error('User "%s" denied permission to update instance'
                          ' "%s" on project "%s"' %
                          (str(request.user), instance_id, project_id))
            else:
                messages.success(request,
                                 _('Instance %(inst)s has been updated.') %
                                  {'inst': instance_id})
                LOG.info('Instance "%s" updated on project "%s"' %
                         (instance_id, project_id))
            return redirect('nova_instances', project_id)
        else:
            return render_to_response(
                'django_openstack/nova/instances/edit.html',
                {'region': project.region,
                 'project': project,
                 'instance': instance,
                 'update_form': form},
                context_instance=template.RequestContext(request))

    else:
        return render_to_response(
            'django_openstack/nova/instances/edit.html',
            {'region': project.region,
             'project': project,
             'instance': instance,
             'update_form': nova_forms.UpdateInstanceForm(instance)},
            context_instance=template.RequestContext(request))
