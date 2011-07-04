# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development, Inc.
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

from django import template
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

import datetime
import json
import logging

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from openstackx.api import exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.syspanel.views.tenants')


class CreateTenant(forms.SelfHandlingForm):
    id = forms.CharField(label="ID (name)")
    description = forms.CharField(widget=forms.widgets.Textarea(), label="Description")
    enabled = forms.BooleanField(label="Enabled", required=False)

    def handle(self, request, data):
        try:
            LOG.info('Creating tenant with id "%s"' % data['id'])
            api.tenant_create(request,
                              data['id'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             '%s was successfully created.'
                             % data['id'])
        except api_exceptions.ApiException, e:
            LOG.error('ApiException while creating tenant\n'
                      'Id: "%s", Description: "%s", Enabled "%s"' %
                      (data['id'], data['description'], data['enabled']),
                      exc_info=True)
            messages.error(request, 'Unable to create tenant: %s' %
                           (e.message))
        return redirect('syspanel_tenants')


class UpdateTenant(forms.SelfHandlingForm):
    id = forms.CharField(label="ID (name)", widget=forms.TextInput(attrs={'readonly':'readonly'}))
    description = forms.CharField(widget=forms.widgets.Textarea(), label="Description")
    enabled = forms.BooleanField(label="Enabled", required=False)

    def handle(self, request, data):
        try:
            LOG.info('Updating tenant with id "%s"' % data['id'])
            api.tenant_update(request,
                              data['id'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             '%s was successfully updated.'
                             % data['id'])
        except api_exceptions.ApiException, e:
            LOG.error('ApiException while updating tenant\n'
                      'Id: "%s", Description: "%s", Enabled "%s"' %
                      (data['id'], data['description'], data['enabled']),
                      exc_info=True)
            messages.error(request, 'Unable to update tenant: %s' % e.message)
        return redirect('syspanel_tenants')


@login_required
def index(request):
    tenants = []
    try:
        tenants = api.tenant_list(request)
    except api_exceptions.ApiException, e:
        LOG.error('ApiException while getting tenant list', exc_info=True)
        messages.error(request, 'Unable to get tenant info: %s' % e.message)
    tenants.sort(key=lambda x: x.id, reverse=True)
    return render_to_response('syspanel_tenants.html',{
        'tenants': tenants,
    }, context_instance = template.RequestContext(request))


@login_required
def create(request):
    form, handled = CreateTenant.maybe_handle(request)
    if handled:
        return handled

    return render_to_response(
    'syspanel_tenant_create.html',{
        'form': form,
    }, context_instance = template.RequestContext(request))


@login_required
def update(request, tenant_id):
    form, handled = UpdateTenant.maybe_handle(request)
    if handled:
        return handled

    if request.method == 'GET':
        try:
            tenant = api.tenant_get(request, tenant_id)
            form = UpdateTenant(initial={'id': tenant.id,
                                         'description': tenant.description,
                                         'enabled': tenant.enabled})
        except api_exceptions.ApiException, e:
            LOG.error('Error fetching tenant with id "%s"' % tenant_id,
                      exc_info=True)
            messages.error(request, 'Unable to update tenant: %s' % e.message)
            return redirect('syspanel_tenants')

    return render_to_response(
    'syspanel_tenant_update.html',{
        'form': form,
    }, context_instance = template.RequestContext(request))
