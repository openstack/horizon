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
from django import shortcuts
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack.nova import forms as nova_forms
from django_openstack.nova.exceptions import handle_nova_error

from django_openstack import api
from django_openstack import forms
import openstack.compute.servers
import openstackx.api.exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.nova')


class DeleteKeypair(forms.SelfHandlingForm):
    keypair_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            keypair = api.extras_api(request).keypairs.delete(
                                              data['keypair_id'])
            messages.info(request, 'Successfully deleted keypair: %s' \
                                    % data['keypair_id'])
        except api_exceptions.ApiException, e:
            messages.error(request, 'Error deleting keypair: %s' % e.message)
        return shortcuts.redirect(request.build_absolute_uri())

class CreateKeypair(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20", label="Keypair Name")

    def handle(self, request, data):
        try:
            keypair = api.extras_api(request).keypairs.create(data['name'])
            response = http.HttpResponse(mimetype='application/binary')
            response['Content-Disposition'] = \
                'attachment; filename=%s.pem' % \
                keypair.key_name
            response.write(keypair.private_key)
            return response
        except api_exceptions.ApiException, e:
            messages.error(request, 'Error Creating Keypair: %s' % e.message)
            return shortcuts.redirect(request.build_absolute_uri())

@login_required
def index(request, tenant_id):
    delete_form, handled = DeleteKeypair.maybe_handle(request)
    if handled:
        return handled

    try:
        keypairs = api.extras_api(request).keypairs.list()
    except api_exceptions.ApiException, e:
        keypairs = []
        messages.error(request, 'Error featching keypairs: %s' % e.message)

    return render_to_response('dash_keypairs.html', {
        'keypairs': keypairs,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))

@login_required
def create(request, tenant_id):
    form, handled = CreateKeypair.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('dash_keypairs_create.html', {
        'create_form': form,
    }, context_instance=template.RequestContext(request))
