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

from django_openstack import api
from django_openstack import forms
import openstack.compute.servers
import openstackx.api.exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.dash')


class TerminateInstance(forms.SelfHandlingForm):
    instance = forms.CharField(required=True)

    def handle(self, request, data):
        instance_id = data['instance']
        instance = api.server_get(request, instance_id)

        try:
            api.server_delete(request, instance)
        except api_exceptions.ApiException, e:
            LOG.error('ApiException while terminating instance "%s"' %
                      instance_id, exc_info=True)
            messages.error(request,
                           'Unable to terminate %s: %s' %
                           (instance_id, e.message,))
        else:
            msg = 'Instance %s has been terminated.' % instance_id
            LOG.info(msg)
            messages.success(request, msg)

        return redirect(request.build_absolute_uri())


class RebootInstance(forms.SelfHandlingForm):
    instance = forms.CharField(required=True)

    def handle(self, request, data):
        instance_id = data['instance']
        try:
            server = api.server_reboot(request, instance_id)
            messages.success(request, "Instance rebooting")
        except api_exceptions.ApiException, e:
            LOG.error('ApiException while rebooting instance "%s"' %
                      instance_id, exc_info=True)
            messages.error(request,
                       'Unable to reboot instance: %s' % e.message)

        else:
            msg = 'Instance %s has been rebooted.' % instance_id
            LOG.info(msg)
            messages.success(request, msg)

        return redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id):
    for f in (TerminateInstance, RebootInstance):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    instances = []
    try:
        instances = api.server_list(request)
    # TODO(markgius): Why isn't this an apiexception?
    except Exception as e:
        LOG.error('Exception in instance index', exc_info=True)
        messages.error(request, 'Unable to get instance list: %s' % e.message)

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()

    return render_to_response('dash_instances.html', {
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
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
        usage = api.usage_get(request, tenant_id, datetime_start, datetime_end)
    except api_exceptions.ApiException, e:
        LOG.error('ApiException in instance usage', exc_info=True)

        messages.error(request, 'Unable to get usage info: %s' % e.message)
    return render_to_response('dash_usage.html', {
        'usage': usage,
    }, context_instance=template.RequestContext(request))


@login_required
def console(request, tenant_id, instance_id):
    try:
        console = api.console_create(request, instance_id)
        response = http.HttpResponse(mimetype='text/plain')
        response.write(console.output)
        response.flush()
        return response
    except api_exceptions.ApiException, e:
        LOG.error('ApiException while fetching instance console',
                  exc_info=True)

        messages.error(request,
                   'Unable to get log for instance %s: %s' %
                   (instance_id, e.message))
        return redirect('dash_instances', tenant_id)


@login_required
def vnc(request, tenant_id, instance_id):
    try:
        console = api.console_create(request, instance_id, 'vnc')
        return redirect(console.output)
    except api_exceptions.ApiException, e:
        LOG.error('ApiException while fetching instance vnc connection',
                  exc_info=True)

        messages.error(request,
                   'Unable to get vnc console for instance %s: %s' %
                   (instance_id, e.message))
        return redirect('dash_instances', tenant_id)
