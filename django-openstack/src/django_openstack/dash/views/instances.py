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
import datetime
import logging

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack.nova import forms as nova_forms
from django_openstack.nova.exceptions import handle_nova_error

from django_openstack import api
from django_openstack import forms
import openstack.compute.servers
import openstackx.api.exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.nova')


class TerminateInstance(forms.SelfHandlingForm):
    instance = forms.CharField(required=True)

    def handle(self, request, data):
        instance_id = data['instance']
        instance = api.compute_api(request).servers.get(instance_id)

        try:
            api.compute_api(request).servers.delete(instance)
        except api_exceptions.ApiException, e:
            messages.error(request,
                           'Unable to terminate %s: %s' %
                           (instance_id, e.message,))
        else:
            messages.success(request,
                             'Instance %s has been terminated.' % instance_id)

        return redirect(request.build_absolute_uri())


class RebootInstance(forms.SelfHandlingForm):
    instance = forms.CharField(required=True)

    def handle(self, request, data):
        instance_id = data['instance']
        try:
            server = api.compute_api(request).servers.get(instance_id)
            server.reboot(openstack.compute.servers.REBOOT_HARD)
            messages.success(request, "Instance rebooting")
        except api_exceptions.ApiException, e:
            messages.error(request,
                       'Unable to reboot instance: %s' % e.message)

        return redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id):
    tenant = api.get_tenant(request, request.user.tenant)
    instances = api.compute_api(request).servers.list()

    for f in (TerminateInstance, RebootInstance):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()


    return render_to_response('dash_instances.html', {
        'tenant': tenant,
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
        'detail': False,
    }, context_instance=template.RequestContext(request))


@login_required
def usage(request, tenant_id=None):
    today = datetime.date.today()
    date_start = datetime.date(today.year, today.month, 1)
    datetime_start = datetime.datetime.combine(date_start, datetime.time())
    datetime_end = datetime.datetime.utcnow()

    usage = {}
    if not tenant_id:
        tenant_id = request.user.tenant


    try:
        usage = api.extras_api(request).usage.get(tenant_id,
                                                  datetime_start, datetime_end)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to get usage info: %s' % e.message)

    return render_to_response('dash_usage.html', {
        'usage': usage,
    }, context_instance=template.RequestContext(request))


@login_required
def console(request, tenant_id, instance_id):
    try:
        console = api.extras_api(request).consoles.create(instance_id)
        response = http.HttpResponse(mimetype='text/plain')
        response.write(console.output)
        response.flush()
        return response
    except api_exceptions.ApiException, e:
        messages.error(request,
                   'Unable to get log for instance %s: %s' %
                   (instance_id, e.message))
        return redirect('dash_instances', tenant_id)


@login_required
def vnc(request, tenant_id, instance_id):
    try:
        console = api.extras_api(request).consoles.create(instance_id, 'vnc')
        return redirect(console.output)
    except api_exceptions.ApiException, e:
        messages.error(request,
                   'Unable to get vnc console for instance %s: %s' %
                   (instance_id, e.message))
        return redirect('dash_instances', tenant_id)










# TODO(termie): below = NotImplemented

@login_required
@handle_nova_error
def detail(request, tenant_id, instance_id):
    tenant = api.get_tenant(request, request.user.tenant)
    instances = api.compute_api(request).servers.list()
    instance = api.compute_api(request).servers.get(instance_id)
    #instances = sorted(project.get_instances(),
    #                   key=lambda k: k.public_dns_name)

    if not instance:
        raise http.Http404()

    return render_to_response('django_openstack/nova/instances/index.html', {
        #'region': project.region,
        'tenant': tenant,
        'selected_instance': instance,
        'instances': instances,
        #'update_form': nova_forms.UpdateInstanceForm(instance),
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
def refresh(request, tenant_id):
    # TODO(devcamcar): This logic belongs in decorator.
    if not request.user:
        return http.HttpResponseForbidden()

    tenant = api.get_tenant(request, request.user.tenant)
    instances = api.compute_api(request).servers.list()

    return render_to_response(
        'django_openstack/nova/instances/_instances_list.html',
        {'tenant': tenant,
         'instances': instances},
        context_instance=template.RequestContext(request))


@handle_nova_error
def refresh_detail(request, tenant_id, instance_id):
    # TODO(devcamcar): This logic belongs in decorator.
    if not request.user:
        return http.HttpResponseForbidden()

    tenant = api.get_tenant(request, request.user.tenant)
    instances = api.compute_api(request).servers.list()
    instance = api.compute_api(request).servers.get(instance_id)
    #instances = sorted(project.get_instances(),
    #                   key=lambda k: k.public_dns_name)

    return render_to_response(
        'django_openstack/nova/instances/_instances_list.html',
        {'tenant': tenant,
         'selected_instance': instance,
         'instances': instances},
        context_instance=template.RequestContext(request))



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
