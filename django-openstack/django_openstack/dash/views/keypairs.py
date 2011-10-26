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
Views for managing Nova instances.
"""
import logging

from django import http
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import validators
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms
from novaclient import exceptions as novaclient_exceptions


LOG = logging.getLogger('django_openstack.dash.views.keypairs')


class DeleteKeypair(forms.SelfHandlingForm):
    keypair_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Deleting keypair "%s"' % data['keypair_id'])
            api.keypair_delete(request, data['keypair_id'])
            messages.info(request, _('Successfully deleted keypair: %s')
                                    % data['keypair_id'])
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in DeleteKeypair")
            messages.error(request,
                           _('Error deleting keypair: %s') % e.message)
        return redirect(request.build_absolute_uri())


class CreateKeypair(forms.SelfHandlingForm):

    name = forms.CharField(max_length="20", label=_("Keypair Name"),
                 validators=[validators.RegexValidator('\w+')])

    def handle(self, request, data):
        try:
            LOG.info('Creating keypair "%s"' % data['name'])
            keypair = api.keypair_create(request, data['name'])
            response = http.HttpResponse(mimetype='application/binary')
            response['Content-Disposition'] = \
                     'attachment; filename=%s.pem' % keypair.name
            response.write(keypair.private_key)
            return response
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in CreateKeyPair")
            messages.error(request,
                           _('Error Creating Keypair: %s') % e.message)
            return redirect(request.build_absolute_uri())


class ImportKeypair(forms.SelfHandlingForm):

    name = forms.CharField(max_length="20", label=_("Keypair Name"),
                 validators=[validators.RegexValidator('\w+')])
    public_key = forms.CharField(label=_("Public Key"), widget=forms.Textarea)

    def handle(self, request, data):
        try:
            LOG.info('Importing keypair "%s"' % data['name'])
            api.keypair_import(request, data['name'], data['public_key'])
            messages.success(request, _('Successfully imported public key: %s')
                                       % data['name'])
            return redirect('dash_keypairs', request.user.tenant_id)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in ImportKeypair")
            messages.error(request,
                           _('Error Importing Keypair: %s') % e.message)
            return redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id):
    delete_form, handled = DeleteKeypair.maybe_handle(request)

    if handled:
        return handled

    try:
        keypairs = api.keypair_list(request)
    except novaclient_exceptions.ClientException, e:
        keypairs = []
        LOG.exception("ClientException in keypair index")
        messages.error(request, _('Error fetching keypairs: %s') % e.message)

    return render_to_response('django_openstack/dash/keypairs/index.html', {
        'keypairs': keypairs,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))


@login_required
def create(request, tenant_id):
    form, handled = CreateKeypair.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('django_openstack/dash/keypairs/create.html', {
        'create_form': form,
    }, context_instance=template.RequestContext(request))


@login_required
def import_keypair(request, tenant_id):
    form, handled = ImportKeypair.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('django_openstack/dash/keypairs/import.html', {
        'create_form': form,
    }, context_instance=template.RequestContext(request))
